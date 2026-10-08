"""Risk Score and Policy Enforcement Evaluation for SentinelX Phase 9.

Evaluates the backend RiskEngine and PolicyEngine across representative
operational synthetic scenarios to verify mathematical consistency and decision accuracy.
"""

from typing import Any

from app.services.risk_engine import RiskEngine, RiskContext
from app.services.policy_engine import PolicyEngine, PolicyRule
from app.risk_policy_config.risk_config import (
    get_default_risk_config,
    ActionType,
    DestinationType,
    DeviceTrustLevel,
    UserRiskRole,
    SensitiveCategory,
)
from app.risk_policy_config.policy_config import get_default_policy_config

SCENARIOS = [
    # 1. LOW RISK - Legitimate local non-sensitive operation
    {
        "id": "SCEN_01",
        "description": "Public documentation file read on trusted corporate laptop",
        "context": RiskContext(
            sensitivity_level="PUBLIC",
            sensitivity_categories=[],
            classification_confidence=0.95,
            action_type=ActionType.READ,
            destination_type=DestinationType.LOCAL_TRUSTED,
            destination_identifier="C:/Users/Employee/Documents/readme.md",
            user_role=UserRiskRole.EMPLOYEE,
            device_trust=DeviceTrustLevel.MANAGED,
            is_business_hours=True,
            is_weekend=False,
            file_size_bytes=4096,
        ),
        "expected_risk_level": "LOW",
        "expected_decision": "ALLOW",
    },
    # 2. LOW RISK - Internal team document copied to trusted local project folder
    {
        "id": "SCEN_02",
        "description": "Internal team notes copied to trusted local project folder",
        "context": RiskContext(
            sensitivity_level="INTERNAL",
            sensitivity_categories=[SensitiveCategory.CONFIDENTIAL_DOCUMENT],
            classification_confidence=0.85,
            action_type=ActionType.COPY,
            destination_type=DestinationType.LOCAL_TRUSTED,
            destination_identifier="C:/Projects/SprintNotes/meeting.txt",
            user_role=UserRiskRole.EMPLOYEE,
            device_trust=DeviceTrustLevel.MANAGED,
            is_business_hours=True,
            is_weekend=False,
            file_size_bytes=16384,
        ),
        "expected_risk_level": "LOW",
        "expected_decision": "ALLOW",
    },
    # 3. MEDIUM / WARNING RISK - Confidential employee salary data moved to external removable drive
    {
        "id": "SCEN_03",
        "description": "Confidential payroll spreadsheet copied to external USB drive",
        "context": RiskContext(
            sensitivity_level="CONFIDENTIAL",
            sensitivity_categories=[SensitiveCategory.EMPLOYEE_DATA],
            classification_confidence=0.90,
            action_type=ActionType.USB_TRANSFER,
            destination_type=DestinationType.USB_TRUSTED,
            destination_identifier="E:/Backups/salary_q3.csv",
            user_role=UserRiskRole.EMPLOYEE,
            device_trust=DeviceTrustLevel.KNOWN,
            is_business_hours=True,
            is_weekend=False,
            file_size_bytes=250000,
        ),
        "expected_risk_level": "MEDIUM",
        "expected_decision": "HOLD",
    },
    # 4. MEDIUM / WARNING RISK - Customer contact list sent to external partner off-hours
    {
        "id": "SCEN_04",
        "description": "Customer contact list transferred via network off-hours",
        "context": RiskContext(
            sensitivity_level="CONFIDENTIAL",
            sensitivity_categories=[SensitiveCategory.CUSTOMER_DATA],
            classification_confidence=0.85,
            action_type=ActionType.NETWORK_TRANSFER,
            destination_type=DestinationType.UNKNOWN_NETWORK,
            destination_identifier="https://files.partner-portal.com/upload",
            user_role=UserRiskRole.EMPLOYEE,
            device_trust=DeviceTrustLevel.MANAGED,
            is_business_hours=False,
            is_weekend=False,
            file_size_bytes=512000,
        ),
        "expected_risk_level": "MEDIUM",
        "expected_decision": "HOLD",
    },
    # 5. HIGH RISK - Highly confidential database passwords exfiltrated to unapproved destination
    {
        "id": "SCEN_05",
        "description": "Production credentials (.env) uploaded to unknown external cloud host",
        "context": RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            sensitivity_categories=[
                SensitiveCategory.CREDENTIALS,
                SensitiveCategory.AUTHENTICATION_SECRETS,
            ],
            classification_confidence=0.98,
            action_type=ActionType.EXTERNAL_UPLOAD,
            destination_type=DestinationType.PUBLIC_CLOUD,
            destination_identifier="https://anonymous-paste.example.org/api/paste",
            user_role=UserRiskRole.GUEST,
            device_trust=DeviceTrustLevel.UNTRUSTED,
            is_business_hours=False,
            is_weekend=True,
            file_size_bytes=1048576,
        ),
        "expected_risk_level": "HIGH",
        "expected_decision": "BLOCK",
    },
    # 6. HIGH RISK - Bulk payment card numbers exfiltrated via external storage
    {
        "id": "SCEN_06",
        "description": "Bulk customer credit card database dump transmitted externally",
        "context": RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            sensitivity_categories=[
                SensitiveCategory.PAYMENT_CARD_DATA,
                SensitiveCategory.FINANCIAL_DATA,
            ],
            classification_confidence=0.99,
            action_type=ActionType.EXTERNAL_UPLOAD,
            destination_type=DestinationType.EXTERNAL_STORAGE,
            destination_identifier="http://dropzone.external.net/upload",
            user_role=UserRiskRole.CONTRACTOR,
            device_trust=DeviceTrustLevel.UNTRUSTED,
            rapid_operations=True,
            unusual_destination=True,
            multiple_sensitive_files=True,
            recent_sensitive_ops=15,
            is_business_hours=False,
            is_weekend=True,
            file_size_bytes=104857600,
        ),
        "expected_risk_level": "HIGH",
        "expected_decision": "BLOCK",
    },
]


def evaluate_risk_and_policy() -> dict[str, Any]:
    """Runs all synthetic operational scenarios through RiskEngine and PolicyEngine."""
    risk_config = get_default_risk_config()
    policy_config = get_default_policy_config()

    risk_engine = RiskEngine(config=risk_config)
    policy_engine = PolicyEngine(config=policy_config)

    # Standard SentinelX policy set
    policies = [
        PolicyRule(
            id=1,
            name="Block High Risk Exfiltration",
            enabled=True,
            priority=100,
            decision="BLOCK",
            min_risk_score=70.0,
        ),
        PolicyRule(
            id=2,
            name="Hold Medium Risk Removable Storage",
            enabled=True,
            priority=80,
            decision="HOLD",
            min_risk_score=30.0,
            max_risk_score=69.99,
        ),
        PolicyRule(
            id=3,
            name="Allow Low Risk Operations",
            enabled=True,
            priority=10,
            decision="ALLOW",
            max_risk_score=29.99,
        ),
    ]

    scenario_results = []
    passed_count = 0

    for scen in SCENARIOS:
        assessment = risk_engine.assess(scen["context"])
        decision = policy_engine.evaluate(scen["context"], assessment, policies=policies)

        risk_level_str = assessment.risk_level.value if hasattr(assessment.risk_level, "value") else str(assessment.risk_level)
        dec_str = decision.decision

        expected_dec = scen["expected_decision"]
        is_pass = (dec_str == expected_dec)
        if is_pass:
            passed_count += 1

        scenario_results.append({
            "scenario_id": scen["id"],
            "description": scen["description"],
            "sensitivity": scen["context"].sensitivity_level,
            "action": scen["context"].action_type,
            "destination": scen["context"].destination_type,
            "calculated_risk_score": round(assessment.risk_score, 2),
            "calculated_risk_level": risk_level_str,
            "expected_decision": expected_dec,
            "actual_decision": dec_str,
            "status": "PASS" if is_pass else "FAIL",
            "explanation": decision.explanation,
            "component_breakdown": {
                factor.name: round(factor.contribution, 2)
                for factor in assessment.factors
            },
        })

    return {
        "total_scenarios": len(SCENARIOS),
        "passed_scenarios": passed_count,
        "pass_rate_percent": round((passed_count / len(SCENARIOS)) * 100, 2),
        "scenarios": scenario_results,
    }


if __name__ == "__main__":
    res = evaluate_risk_and_policy()
    print("=== Risk & Policy Engine Evaluation ===")
    print(f"Pass Rate: {res['passed_scenarios']}/{res['total_scenarios']} ({res['pass_rate_percent']}%)")
    for s in res["scenarios"]:
        print(f"[{s['status']}] {s['scenario_id']}: Score={s['calculated_risk_score']} ({s['calculated_risk_level']}) -> Decision={s['actual_decision']} (Expected={s['expected_decision']})")
