"""Authentication service."""

import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import verify_password
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.schemas.users import UserCreate
from app.services.audit_service import log_action
from app.services.user_service import create_user, get_user_by_username, mark_login

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, login_data: LoginRequest, ip_address: str | None = None) -> User:
    """Authenticate a user and return the user object if successful."""
    user = get_user_by_username(db, login_data.username)
    if not user:
        # Prevent timing attacks by verifying a dummy hash
        # (Passlib handles this if configured, but keeping it simple for now)
        log_action(
            db,
            action=AuditAction.USER_LOGIN_FAILED,
            ip_address=ip_address,
            metadata={"username": login_data.username, "reason": "User not found"}
        )
        raise UnauthorizedError("Incorrect username or password")

    if not verify_password(login_data.password, user.password_hash):
        log_action(
            db,
            action=AuditAction.USER_LOGIN_FAILED,
            actor_user_id=user.id,
            ip_address=ip_address,
            metadata={"username": user.username, "reason": "Invalid password"}
        )
        raise UnauthorizedError("Incorrect username or password")

    if not user.is_active:
        log_action(
            db,
            action=AuditAction.USER_LOGIN_FAILED,
            actor_user_id=user.id,
            ip_address=ip_address,
            metadata={"username": user.username, "reason": "Account disabled"}
        )
        raise UnauthorizedError("Inactive user")

    mark_login(db, user.id)

    log_action(
        db,
        action=AuditAction.USER_LOGIN,
        actor_user_id=user.id,
        ip_address=ip_address,
    )

    return user


def create_initial_admin_if_needed(db: Session) -> None:
    """Create the initial admin user if the users table is empty."""
    if db.query(User).first():
        return

    settings = get_settings()

    logger.info("No users found. Creating initial admin from environment variables.")

    admin_in = UserCreate(
        username=settings.FIRST_ADMIN_USERNAME,
        password=settings.FIRST_ADMIN_PASSWORD,
        email=settings.FIRST_ADMIN_EMAIL,
        full_name="System Administrator",
        role=UserRole.ADMIN,
    )

    create_user(db, admin_in)
