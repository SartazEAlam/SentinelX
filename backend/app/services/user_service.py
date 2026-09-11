"""User service for CRUD operations."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.enums import AuditAction, UserRole
from app.models.user import User
from app.schemas.users import UserCreate, UserUpdate
from app.services.audit_service import log_action


def get_user(db: Session, user_id: int) -> User:
    """Get a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    return user


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get a user by username."""
    return db.query(User).filter(User.username == username).first()


def list_users(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
    """List users with pagination."""
    query = db.query(User)
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    return users, total


def create_user(
    db: Session, user_in: UserCreate, actor_id: int | None = None, ip_address: str | None = None
) -> User:
    """Create a new user."""
    # Check duplicates
    if db.query(User).filter(User.username == user_in.username).first():
        raise ConflictError("Username already registered")
    if db.query(User).filter(User.email == user_in.email).first():
        raise ConflictError("Email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(
        db,
        action=AuditAction.USER_CREATED,
        actor_user_id=actor_id,
        resource_type="User",
        resource_id=str(user.id),
        ip_address=ip_address,
        metadata={"username": user.username, "role": user.role},
    )
    
    return user


def update_user(
    db: Session, user_id: int, user_in: UserUpdate, actor_id: int | None = None
) -> User:
    """Update an existing user."""
    user = get_user(db, user_id)

    if user_in.email is not None and user_in.email != user.email:
        if db.query(User).filter(User.email == user_in.email).first():
            raise ConflictError("Email already registered")
        user.email = user_in.email

    if user_in.full_name is not None:
        user.full_name = user_in.full_name
        
    if user_in.role is not None:
        user.role = user_in.role
        
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
        if not user_in.is_active:
            # If deactivated, log specifically
            log_action(
                db,
                action=AuditAction.USER_DEACTIVATED,
                actor_user_id=actor_id,
                resource_type="User",
                resource_id=str(user.id),
                metadata={"username": user.username},
            )

    db.commit()
    db.refresh(user)

    log_action(
        db,
        action=AuditAction.USER_UPDATED,
        actor_user_id=actor_id,
        resource_type="User",
        resource_id=str(user.id),
    )
    
    return user


def mark_login(db: Session, user_id: int) -> None:
    """Update user's last login timestamp."""
    user = get_user(db, user_id)
    user.last_login_at = datetime.now(UTC)
    db.commit()
