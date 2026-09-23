"""Authentication schemas."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    """Credentials for authentication."""

    username: str
    password: str


class PasswordChangeRequest(BaseModel):
    """Schema for changing current user password."""

    current_password: str
    new_password: str = Field(..., min_length=8)


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
