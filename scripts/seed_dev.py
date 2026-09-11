"""Seed development database with mock data for testing and development."""

import argparse
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import app modules
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))

from app.config import get_settings
from app.db.database import SessionLocal
from app.models.enums import UserRole, EventDecision
from app.schemas.users import UserCreate
from app.schemas.policies import PolicyCreate
from app.services.user_service import create_user
from app.services.policy_service import create_policy
from app.services.auth_service import create_initial_admin_if_needed

def seed_db() -> None:
    settings = get_settings()
    
    # We must operate in a development context
    if settings.ENVIRONMENT not in ("development", "testing"):
        print(f"Skipping seed in environment: {settings.ENVIRONMENT}")
        return

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
                email="jane@sentinelx.local",
                password="AnalystPassword123!",
                full_name="Jane Doe (Analyst)",
                role=UserRole.SECURITY_ANALYST,
            )
            user = create_user(db, analyst_in)
            print(f"Created analyst: {user.username}")
        except Exception as e:
            print(f"Analyst might already exist: {e}")

        # 3. Add some default policies
        try:
            # Only create if the table is empty
            policies, _ = db.query(Policy).count()
            if policies == 0:
                pass
        except Exception:
            pass # We'll just try to create and catch errors
            
        policy1 = PolicyCreate(
            name="Block USB Mass Storage",
            description="Prevent all untrusted USB drives from mounting",
            decision=EventDecision.BLOCK,
            enabled=True,
            conditions={"device_class": "mass_storage"}
        )
        try:
            create_policy(db, policy1, actor_user_id=1)
            print(f"Created policy: {policy1.name}")
        except Exception as e:
            print(f"Policy might already exist: {e}")

        print("Dev database seed complete.")
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the SentinelX database")
    args = parser.parse_args()
    seed_db()
