"""Seed development database with mock data for testing and development."""

# ruff: noqa: E402
import argparse
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import app modules
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))

import app.models  # noqa: F401
from app.config import get_settings
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.models.enums import EventDecision, UserRole
from app.models.policy import Policy
from app.schemas.policies import PolicyCreate
from app.schemas.users import UserCreate
from app.services.auth_service import create_initial_admin_if_needed
from app.services.policy_service import create_policy
from app.services.user_service import create_user


def seed_db() -> None:
    settings = get_settings()

    # We must operate in a development context
    if settings.ENVIRONMENT not in ("development", "testing"):
        print(f"Skipping seed in environment: {settings.ENVIRONMENT}")
        return

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Starting dev database seed...")

        # 1. Admin
        create_initial_admin_if_needed(db)
        print(f"Admin user verified: {settings.FIRST_ADMIN_USERNAME}")

        # 2. Add an Analyst User
        try:
            analyst_in = UserCreate(
                username="analyst_jane",
                email="jane@sentinelx.com",
                password="AnalystPassword123!",
                full_name="Jane Doe (Analyst)",
                role=UserRole.SECURITY_ANALYST,
            )
            user = create_user(db, analyst_in)
            print(f"Created analyst: {user.username}")
        except Exception as e:
            print(f"Analyst might already exist: {e}")

        # 3. Add default policy
        policy1 = PolicyCreate(
            name="Block USB Mass Storage",
            description="Prevent all untrusted USB drives from mounting",
            decision=EventDecision.BLOCK,
            enabled=True,
            conditions={"device_class": "mass_storage"},
        )
        existing_policy = db.query(Policy).filter(Policy.name == policy1.name).first()
        if not existing_policy:
            try:
                create_policy(db, policy1, creator_id=1)
                print(f"Created policy: {policy1.name}")
            except Exception as e:
                print(f"Failed to create policy: {e}")
        else:
            print(f"Policy already exists: {policy1.name}")

        print("Dev database seed complete.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the SentinelX database")
    args = parser.parse_args()
    seed_db()
