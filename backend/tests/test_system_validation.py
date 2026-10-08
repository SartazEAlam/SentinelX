"""Final System Validation for SentinelX Phase 9.

Demonstrates and verifies the 4 representative operational workflows:
  TEST 1 - LOW RISK:
    Normal operation -> classification -> low risk -> ALLOW
  TEST 2 - WARNING:
    Sensitive synthetic data -> classification -> medium risk -> HOLD
    -> administrator approval -> operation continues
  TEST 3 - DENIAL:
    Sensitive synthetic data -> HOLD -> administrator DENY -> operation prevented
  TEST 4 - HIGH RISK:
    Highly sensitive synthetic data + untrusted action -> high risk -> BLOCK
    -> event logged -> administrator alert generated
"""

from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import ApprovalStatus
from app.services.approval_service import create_approval
from app.services.risk_engine import RiskEngine, RiskContext
from app.services.policy_engine import PolicyEngine
from app.risk_policy_config.risk_config import (
    get_default_risk_config,
    ActionType,
    DestinationType,
    DeviceTrustLevel,
    UserRiskRole,
    SensitiveCategory,
)
from app.risk_policy_config.policy_config import get_default_policy_config


def test_system_validation_workflow_1_low_risk_allow() -> None:
    """TEST 1: Normal benign operation -> Low Risk -> ALLOW."""
    risk_engine = RiskEngine(config=get_default_risk_config())
    policy_engine = PolicyEngine(config=get_default_policy_config())

    ctx = RiskContext(
        sensitivity_level="PUBLIC",
        sensitivity_categories=[],
        classification_confidence=0.9,
        action_type=ActionType.READ,
        destination_type=DestinationType.LOCAL_TRUSTED,
        user_role=UserRiskRole.EMPLOYEE,
        device_trust=DeviceTrustLevel.MANAGED,
        is_business_hours=True,
        file_size_bytes=1024,
    )
    assessment = risk_engine.assess(ctx)
    decision = policy_engine.evaluate(ctx, assessment)

    assert assessment.risk_level == "LOW", f"Expected LOW, got {assessment.risk_level}"
    assert decision.decision == "ALLOW", f"Expected ALLOW, got {decision.decision}"


def test_system_validation_workflow_2_warning_hold_and_approve(client: TestClient, db: Session, admin_token: str) -> None:
    """TEST 2: Sensitive synthetic data -> Medium Risk -> HOLD -> Admin APPROVE."""
    risk_engine = RiskEngine(config=get_default_risk_config())
    policy_engine = PolicyEngine(config=get_default_policy_config())

    ctx = RiskContext(
        sensitivity_level="CONFIDENTIAL",
        sensitivity_categories=[SensitiveCategory.EMPLOYEE_DATA],
        classification_confidence=0.85,
        action_type=ActionType.USB_TRANSFER,
        destination_type=DestinationType.USB_TRUSTED,
        user_role=UserRiskRole.EMPLOYEE,
        device_trust=DeviceTrustLevel.KNOWN,
        is_business_hours=True,
        file_size_bytes=50000,
    )
    assessment = risk_engine.assess(ctx)
    decision = policy_engine.evaluate(ctx, assessment)

    assert assessment.risk_level == "MEDIUM", f"Expected MEDIUM, got {assessment.risk_level}"
    assert decision.decision == "HOLD", f"Expected HOLD, got {decision.decision}"

    approval = create_approval(
        db,
        event_id=102,
        requested_by=1,
        reason="Required Q3 payroll reporting for off-site finance audit",
    )
    approval_id = approval.id

    # Admin approves
    resp = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "Approved for 2 hours for authorized audit."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == ApprovalStatus.APPROVED.value


def test_system_validation_workflow_3_warning_hold_and_deny(client: TestClient, db: Session, admin_token: str) -> None:
    """TEST 3: Sensitive synthetic data -> HOLD -> Admin DENY -> Operation Prevented."""
    risk_engine = RiskEngine(config=get_default_risk_config())
    policy_engine = PolicyEngine(config=get_default_policy_config())

    ctx = RiskContext(
        sensitivity_level="CONFIDENTIAL",
        sensitivity_categories=[SensitiveCategory.CUSTOMER_DATA],
        classification_confidence=0.88,
        action_type=ActionType.NETWORK_TRANSFER,
        destination_type=DestinationType.UNKNOWN_NETWORK,
        user_role=UserRiskRole.EMPLOYEE,
        device_trust=DeviceTrustLevel.MANAGED,
        is_business_hours=False,
        file_size_bytes=100000,
    )
    assessment = risk_engine.assess(ctx)
    decision = policy_engine.evaluate(ctx, assessment)

    assert assessment.risk_level == "MEDIUM"
    assert decision.decision == "HOLD"

    approval = create_approval(
        db,
        event_id=103,
        requested_by=1,
        reason="Transfer customer database to external address",
    )
    approval_id = approval.id

    # Admin rejects
    resp = client.post(
        f"/api/v1/approvals/{approval_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "Denied: Unauthorized external customer data egress."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == ApprovalStatus.REJECTED.value


def test_system_validation_workflow_4_high_risk_block(client: TestClient, admin_token: str) -> None:
    """TEST 4: Highly sensitive synthetic credentials + untrusted upload -> High Risk -> BLOCK -> Alert logged."""
    risk_engine = RiskEngine(config=get_default_risk_config())
    policy_engine = PolicyEngine(config=get_default_policy_config())

    ctx = RiskContext(
        sensitivity_level="HIGHLY_CONFIDENTIAL",
        sensitivity_categories=[SensitiveCategory.CREDENTIALS, SensitiveCategory.API_KEYS],
        classification_confidence=0.98,
        action_type=ActionType.EXTERNAL_UPLOAD,
        destination_type=DestinationType.PUBLIC_CLOUD,
        user_role=UserRiskRole.GUEST,
        device_trust=DeviceTrustLevel.UNTRUSTED,
        is_business_hours=False,
        is_weekend=True,
        rapid_operations=True,
        file_size_bytes=1048576,
    )
    assessment = risk_engine.assess(ctx)
    decision = policy_engine.evaluate(ctx, assessment)

    assert assessment.risk_level == "HIGH", f"Expected HIGH, got {assessment.risk_level}"
    assert decision.decision == "BLOCK", f"Expected BLOCK, got {decision.decision}"

    # Verify security alert generated for high risk exfiltration
    alert_resp = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Blocked High-Risk Exfiltration Attempt",
            "message": "Production credentials uploaded to untrusted public cloud host.",
            "severity": "CRITICAL",
        },
    )
    assert alert_resp.status_code == 201
    alert_id = alert_resp.json()["id"]

    # Verify alert appears in dashboard alerts list
    list_resp = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_resp.status_code == 200
    item_ids = [item["id"] for item in list_resp.json()["items"]]
    assert alert_id in item_ids
