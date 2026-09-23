"""Seed development database with realistic mock data for testing and development."""

# ruff: noqa: E402
import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add the backend directory to sys.path so we can import app modules
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_dir))

import app.models  # noqa: F401
from app.config import get_settings
from app.core.security import hash_device_token
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.models.alert import Alert
from app.models.approval import ApprovalRequest
from app.models.device import Device
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    ApprovalStatus,
    DeviceStatus,
    EventDecision,
    EventType,
    SensitivityLevel,
    UserRole,
)
from app.models.policy import Policy
from app.models.security_event import SecurityEvent
from app.schemas.policies import PolicyCreate
from app.schemas.users import UserCreate
from app.services.auth_service import create_initial_admin_if_needed
from app.services.policy_service import create_policy
from app.services.user_service import create_user


def seed_db() -> None:
    settings = get_settings()

    # We must operate in a development or testing context
    if settings.ENVIRONMENT not in ("development", "testing"):
        print(f"Skipping seed in environment: {settings.ENVIRONMENT}")
        return

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Starting dev database seed...")

        # 1. Admin User
        create_initial_admin_if_needed(db)
        print(f"  [+] Admin user verified: {settings.FIRST_ADMIN_USERNAME}")

        # 2. Analyst & Viewer Users
        try:
            analyst = create_user(
                db,
                UserCreate(
                    username="analyst_jane",
                    email="jane@sentinelx.com",
                    password="AnalystPassword123!",
                    full_name="Jane Doe (Analyst)",
                    role=UserRole.SECURITY_ANALYST,
                ),
            )
            print(f"  [+] Created analyst: {analyst.username}")
        except Exception:
            print("  [i] Analyst already exists")

        try:
            viewer = create_user(
                db,
                UserCreate(
                    username="viewer_bob",
                    email="bob@sentinelx.com",
                    password="ViewerPassword123!",
                    full_name="Bob Smith (Auditor)",
                    role=UserRole.VIEWER,
                ),
            )
            print(f"  [+] Created viewer: {viewer.username}")
        except Exception:
            print("  [i] Viewer already exists")

        # 3. Sample Devices
        now = datetime.now(UTC)
        devices_data = [
            {
                "device_id": "DEV-WIN11-01",
                "device_name": "Dev Workstation Alpha",
                "hostname": "DEV-W11-ALPHA",
                "operating_system": "Windows 11 Pro 23H2",
                "agent_version": "0.1.0",
                "ip_address": "192.168.1.101",
                "status": DeviceStatus.ONLINE,
                "token": "dev-token-secret-01",
            },
            {
                "device_id": "FIN-LAPTOP-04",
                "device_name": "Finance ThinkPad",
                "hostname": "FIN-TP-04",
                "operating_system": "Windows 11 Enterprise",
                "agent_version": "0.1.0",
                "ip_address": "192.168.1.150",
                "status": DeviceStatus.ONLINE,
                "token": "fin-token-secret-04",
            },
            {
                "device_id": "HR-DESKTOP-02",
                "device_name": "HR Office Desktop",
                "hostname": "HR-DT-02",
                "operating_system": "Windows 10 Pro 22H2",
                "agent_version": "0.1.0",
                "ip_address": "192.168.1.205",
                "status": DeviceStatus.OFFLINE,
                "token": "hr-token-secret-02",
            },
        ]

        for d in devices_data:
            existing = db.query(Device).filter(Device.device_id == d["device_id"]).first()
            if not existing:
                full_token = f"{d['device_id']}.{d['token']}"
                token_hash = hash_device_token(full_token)
                dev = Device(
                    device_id=d["device_id"],
                    device_name=d["device_name"],
                    hostname=d["hostname"],
                    operating_system=d["operating_system"],
                    agent_version=d["agent_version"],
                    ip_address=d["ip_address"],
                    status=d["status"],
                    token_hash=token_hash,
                    last_seen_at=now
                    - timedelta(minutes=5 if d["status"] == DeviceStatus.ONLINE else 120),
                    is_active=True,
                )
                db.add(dev)
                print(f"  [+] Created device: {d['device_id']}")
        db.commit()

        # 4. DLP Policies
        policies = [
            PolicyCreate(
                name="Block USB Mass Storage",
                description="Prevent untrusted USB flash drives from exfiltrating data",
                decision=EventDecision.BLOCK,
                enabled=True,
                conditions={"device_class": "mass_storage"},
            ),
            PolicyCreate(
                name="Alert on Confidential Cloud Sync",
                description="Trigger security alert when confidential files are uploaded to cloud",
                decision=EventDecision.MONITOR,
                enabled=True,
                conditions={"sensitivity": ["CONFIDENTIAL", "HIGHLY_CONFIDENTIAL"]},
            ),
            PolicyCreate(
                name="Quarantine Suspicious Executable Copies",
                description="Hold executable binary copies to external destinations for review",
                decision=EventDecision.HOLD,
                enabled=True,
                conditions={"file_extensions": [".exe", ".bat", ".ps1"]},
            ),
        ]

        for p in policies:
            if not db.query(Policy).filter(Policy.name == p.name).first():
                create_policy(db, p, creator_id=1)
                print(f"  [+] Created policy: {p.name}")

        # 5. Security Events
        sample_events = [
            {
                "event_id": f"evt-{uuid4().hex[:8]}",
                "device_id": "FIN-LAPTOP-04",
                "timestamp": now - timedelta(hours=2),
                "event_type": EventType.USB_ACTIVITY,
                "action": "USB_WRITE",
                "file_name": "Q3_Financial_Projections.xlsx",
                "file_path": "D:\\Exports\\Q3_Financial_Projections.xlsx",
                "file_size": 2457600,
                "sensitivity_level": SensitivityLevel.HIGHLY_CONFIDENTIAL,
                "risk_score": 94.0,
                "decision": EventDecision.BLOCK,
                "user_context": "finance_user",
                "process_name": "explorer.exe",
            },
            {
                "event_id": f"evt-{uuid4().hex[:8]}",
                "device_id": "DEV-WIN11-01",
                "timestamp": now - timedelta(hours=1),
                "event_type": EventType.CLOUD_SYNC,
                "action": "FILE_UPLOAD",
                "file_name": "api_keys_backup.json",
                "file_path": "C:\\Users\\dev\\Desktop\\api_keys_backup.json",
                "file_size": 14200,
                "sensitivity_level": SensitivityLevel.CONFIDENTIAL,
                "risk_score": 88.5,
                "decision": EventDecision.HOLD,
                "user_context": "lead_dev",
                "process_name": "Dropbox.exe",
            },
            {
                "event_id": f"evt-{uuid4().hex[:8]}",
                "device_id": "HR-DESKTOP-02",
                "timestamp": now - timedelta(minutes=45),
                "event_type": EventType.CLIPBOARD_ACTIVITY,
                "action": "CLIPBOARD_COPY",
                "file_name": "employee_ssn_list.csv",
                "file_path": "C:\\HR\\employee_ssn_list.csv",
                "file_size": 51200,
                "sensitivity_level": SensitivityLevel.HIGHLY_CONFIDENTIAL,
                "risk_score": 78.0,
                "decision": EventDecision.ALLOW,
                "user_context": "hr_staff",
                "process_name": "excel.exe",
            },
            {
                "event_id": f"evt-{uuid4().hex[:8]}",
                "device_id": "DEV-WIN11-01",
                "timestamp": now - timedelta(minutes=15),
                "event_type": EventType.FILE_ACCESS,
                "action": "FILE_READ",
                "file_name": "README.md",
                "file_path": "D:\\SentinelX\\README.md",
                "file_size": 10240,
                "sensitivity_level": SensitivityLevel.PUBLIC,
                "risk_score": 5.0,
                "decision": EventDecision.ALLOW,
                "user_context": "developer",
                "process_name": "code.exe",
            },
        ]

        created_events = []
        for ev in sample_events:
            if not db.query(SecurityEvent).filter(SecurityEvent.event_id == ev["event_id"]).first():
                event_obj = SecurityEvent(**ev)
                db.add(event_obj)
                db.commit()
                db.refresh(event_obj)
                created_events.append(event_obj)
                print(f"  [+] Created event: {event_obj.event_id} ({ev['file_name']})")

        # 6. Sample Alerts
        if created_events:
            blocked_event = created_events[0]
            alert_existing = db.query(Alert).filter(Alert.event_id == blocked_event.id).first()
            if not alert_existing:
                sample_alert = Alert(
                    alert_id=f"alt-{uuid4().hex[:8]}",
                    event_id=blocked_event.id,
                    device_id=blocked_event.device_id,
                    severity=AlertSeverity.CRITICAL,
                    title="Exfiltration Blocked: Highly Confidential Financial Data",
                    message=(
                        "An unauthorized USB write of Q3 financial projections "
                        "was blocked by policy."
                    ),
                    status=AlertStatus.OPEN,
                )
                db.add(sample_alert)
                db.commit()
                print(f"  [+] Created alert: {sample_alert.title}")

        # 7. Sample Approval Request
        if len(created_events) > 1:
            held_event = created_events[1]
            appr_existing = (
                db.query(ApprovalRequest).filter(ApprovalRequest.event_id == held_event.id).first()
            )
            if not appr_existing:
                sample_approval = ApprovalRequest(
                    request_id=f"req-{uuid4().hex[:8]}",
                    event_id=held_event.id,
                    requested_by=1,
                    status=ApprovalStatus.PENDING,
                    reason="Requesting temporary exception for offsite backup sync",
                )
                db.add(sample_approval)
                db.commit()
                print(f"  [+] Created approval request for event: {held_event.event_id}")

        print("Dev database seed complete successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the SentinelX database")
    parser.parse_args()
    seed_db()
