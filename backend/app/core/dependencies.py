"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token, verify_device_token
from app.db.database import get_db
from app.models.device import Device
from app.models.enums import DeviceStatus, UserRole
from app.models.user import User

# Define separate security schemes for user JWT and device bearer tokens
oauth2_scheme = HTTPBearer(auto_error=False)
device_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Validate JWT and return the current user."""
    if not token:
        raise UnauthorizedError("Not authenticated")

    payload = decode_access_token(token.credentials)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")

    username: str | None = payload.get("sub")
    if not username:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is inactive")

    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency that requires ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin privileges required")
    return current_user


def require_analyst_or_above(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency that requires SECURITY_ANALYST or ADMIN role."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SECURITY_ANALYST]:
        raise ForbiddenError("Analyst or admin privileges required")
    return current_user


def require_viewer_or_above(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Dependency that requires VIEWER role or above (any authenticated user)."""
    return current_user


def get_current_device(
    token: Annotated[HTTPAuthorizationCredentials | None, Depends(device_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Device:
    """Validate device one-time token and return the registered device."""
    if not token:
        raise UnauthorizedError("Device token required")

    # Tokens are of the form 'deviceId.randomString'
    # Wait, the spec didn't mandate a specific format, but typically it's just a token.
    # We will look up the device by scanning? No, that's slow.
    # Let's extract device_id from the header (e.g., X-Device-ID).
    # Wait, standard practice: either token is 'device_id:secret' (b64 encoded) or we need X-Device-ID header.
    # To keep it simple, we'll use an X-Device-ID header in addition to the Bearer token, or assume the token is `<device_id>.<secret>`.
    # Let's use the `<device_id>.<secret>` format for the Bearer token.
    
    parts = token.credentials.split(".", 1)
    if len(parts) != 2:
        raise UnauthorizedError("Invalid device token format")
        
    device_id, secret = parts
    
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise UnauthorizedError("Device not found")
        
    if not device.is_active or device.status == DeviceStatus.DISABLED:
        raise UnauthorizedError("Device is disabled")
        
    if not verify_device_token(token.credentials, device.token_hash):
        raise UnauthorizedError("Invalid device token")
        
    return device
