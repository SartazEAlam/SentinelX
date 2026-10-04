import pytest
import uuid
from app.main import app
from app.db.base import Base
from app.db.database import engine, SessionLocal
from app.models.device import Device
from app.models.security_event import SecurityEvent
from app.models.enforcement import EnforcementResultRecord
from app.models.approval import ApprovalRequest
from app.models.user import User
from app.models.enums import UserRole
from app.models.policy import Policy
from app.core.security import hash_password, hash_device_token
from fastapi.testclient import TestClient
from datetime import datetime, UTC
@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Ensure test device exists
    device = db.query(Device).filter_by(device_id="test-laptop-001").first()
    if not device:
        device = Device(
            device_id="test-laptop-001",
            device_name="Test Laptop",
            operating_system="Windows",
            agent_version="0.1.0",
            is_active=True,
            token_hash=hash_device_token("test-laptop-001.dev-token-123")
        )
        db.add(device)
    
    admin = db.query(User).filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@test.com",
            password_hash=hash_password("Admin@123!"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.flush()
        
    p1 = db.query(Policy).filter_by(name="Test Hold").first()
    if not p1:
        p1 = Policy(name="Test Hold", enabled=True, priority=10, decision="HOLD", sensitivity_levels='["CONFIDENTIAL"]', created_by=admin.id, updated_by=admin.id)
        db.add(p1)
    p2 = db.query(Policy).filter_by(name="Test Block").first()
    if not p2:
        p2 = Policy(name="Test Block", enabled=True, priority=20, decision="BLOCK", sensitivity_levels='["HIGHLY_CONFIDENTIAL", "CRITICAL"]', created_by=admin.id, updated_by=admin.id)
        db.add(p2)
        
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(setup_database):
    with TestClient(app) as c:
        yield c

@pytest.fixture
def auth_headers(client):
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "Admin@123!"})
    if response.status_code != 200:
        raise ValueError(f"Auth failed: {response.status_code} - {response.text}")
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def device_headers():
    return {"Authorization": "Bearer test-laptop-001.dev-token-123", "X-Device-ID": "test-laptop-001"}

def create_event(client, headers, content_type="SAFE"):
    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "event_type": "FILE_ACCESS",
        "action": "file_copied",
        "timestamp": "2026-10-04T12:00:00Z",
        "file_name": "test.txt",
        "classification_json": {
            "max_severity": "PUBLIC" if content_type == "SAFE" else ("CONFIDENTIAL" if content_type == "WARNING" else "CRITICAL")
        },
        "sensitivity_level": "PUBLIC" if content_type == "SAFE" else ("CONFIDENTIAL" if content_type == "WARNING" else "HIGHLY_CONFIDENTIAL")
    }
    resp = client.post("/api/v1/events", json=payload, headers=headers)
    if resp.status_code != 201:
        raise ValueError(f"Event creation failed: {resp.status_code} - {resp.text}")
    return event_id

def test_legitimate_operation(client, auth_headers, device_headers, setup_database):
    event_id = create_event(client, device_headers, "SAFE")
    
    # Evaluate risk
    resp = client.post("/api/v1/risk/evaluate", json={"event_id": event_id}, headers=device_headers)
    assert resp.status_code == 201
    assert resp.json()["decision"] == "ALLOW"
    
    # Submit enforcement
    enf_payload = {
        "operation_id": event_id,
        "decision": "ALLOW",
        "status": "COMPLETED",
        "completed_at": datetime.now(UTC).isoformat(),
        "message": "Allowed locally"
    }
    client.post("/api/v1/enforcement/results", json=enf_payload, headers=device_headers)
    
    db_event = setup_database.query(SecurityEvent).filter_by(event_id=event_id).first()
    assert db_event is not None

def test_warning_level_hold_and_approve(client, auth_headers, device_headers, setup_database):
    event_id = create_event(client, device_headers, "WARNING")
    
    # Evaluate risk
    resp = client.post("/api/v1/risk/evaluate", json={"event_id": event_id}, headers=device_headers)
    assert resp.status_code == 201
    assert resp.json()["decision"] == "HOLD"
    
    # Check approval created (Backend view, uses auth)
    resp = client.get(f"/api/v1/approvals?event_id={event_id}", headers=auth_headers)
    items = resp.json()["items"]
    assert len(items) > 0
    approval_id = items[0]["id"]
    
    # Admin approves (uses auth)
    resp = client.post(f"/api/v1/approvals/{approval_id}/approve", json={"status": "APPROVED", "comments": "OK"}, headers=auth_headers)
    assert resp.status_code == 200
    
    # Agent polls (uses device)
    resp = client.get(f"/api/v1/approvals?event_id={event_id}", headers=device_headers)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["status"] == "APPROVED"
    
    # Submit enforcement (uses device)
    enf_payload = {
        "operation_id": event_id,
        "decision": "ALLOW",
        "status": "COMPLETED",
        "completed_at": datetime.now(UTC).isoformat(),
        "message": "Admin approved"
    }
    client.post("/api/v1/enforcement/results", json=enf_payload, headers=device_headers)
    
    db_enf = setup_database.query(EnforcementResultRecord).filter_by(operation_id=event_id).first()
    assert db_enf is not None
    assert db_enf.decision == "ALLOW"

def test_high_risk_block(client, auth_headers, device_headers, setup_database):
    event_id = create_event(client, device_headers, "CRITICAL")
    
    # Evaluate risk
    resp = client.post("/api/v1/risk/evaluate", json={"event_id": event_id}, headers=device_headers)
    assert resp.status_code == 201
    assert resp.json()["decision"] == "BLOCK"
    
    # Submit enforcement
    enf_payload = {
        "operation_id": event_id,
        "decision": "BLOCK",
        "status": "COMPLETED",
        "completed_at": datetime.now(UTC).isoformat(),
        "message": "Blocked by policy"
    }
    client.post("/api/v1/enforcement/results", json=enf_payload, headers=device_headers)
    
    db_enf = setup_database.query(EnforcementResultRecord).filter_by(operation_id=event_id).first()
    assert db_enf is not None
    assert db_enf.decision == "BLOCK"
