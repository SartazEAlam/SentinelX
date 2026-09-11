"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserMeResponse
from app.services.auth_service import authenticate_user

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user and return JWT."""
    ip_address = request.client.host if request.client else None
    user = authenticate_user(db, login_data, ip_address=ip_address)

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=1800,  # 30 mins
    )


@router.get("/me", response_model=UserMeResponse)
def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserMeResponse:
    """Return info about the currently authenticated user."""
    return current_user
