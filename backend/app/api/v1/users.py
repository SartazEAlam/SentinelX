"""User management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.users import UserCreate, UserResponse, UserUpdate
from app.services import user_service

# Only ADMIN can manage users
router = APIRouter(tags=["Users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=PaginatedResponse[UserResponse])
def get_users(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """List all users (Admin only)."""
    skip = (params.page - 1) * params.size
    users, total = user_service.list_users(db, skip=skip, limit=params.size)
    
    return {
        "items": users,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Get user by ID (Admin only)."""
    return user_service.get_user(db, user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> User:
    """Create a new user (Admin only)."""
    ip_address = request.client.host if request.client else None
    return user_service.create_user(
        db, user_in, actor_id=current_user.id, ip_address=ip_address
    )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> User:
    """Update user attributes or role (Admin only)."""
    return user_service.update_user(
        db, user_id, user_in, actor_id=current_user.id
    )
