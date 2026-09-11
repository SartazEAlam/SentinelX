"""Authentication schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    """Credentials for authentication."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserMeResponse(BaseModel):
    """Current authenticated user information."""
    id: int
    username: str
    email: EmailStr
    full_name: str | None = None
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
