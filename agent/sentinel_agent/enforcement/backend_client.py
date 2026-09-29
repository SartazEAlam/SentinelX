"""Backend enforcement client — connects the agent to Phase 4 policies.

Allows the endpoint agent to request risk evaluations and send
enforcement results to the server.
"""

from __future__ import annotations

import logging
from typing import Any

from sentinel_agent.enforcement.errors import EnforcementError, EnforcementErrorCode
from sentinel_agent.enforcement.models import Decision, EnforcementDecision, OfflineDecision
from sentinel_agent.pipeline.models import EndpointEvent
from sentinel_agent.transport.http_transport import HTTPTransport

logger = logging.getLogger(__name__)


class EnforcementBackendClient:
    """Communicates with the SentinelX backend for enforcement APIs.

    Provides resilient requests, polling for approval updates,
    and offline fail-safe fallbacks.
    """

    def __init__(
        self,
        transport: HTTPTransport,
        offline_policy_high: str = "BLOCK",
        offline_policy_med: str = "HOLD",
        offline_policy_low: str = "ALLOW",
    ) -> None:
        self._transport = transport
        self._offline_policy = {
            "CRITICAL": Decision(offline_policy_high),
            "HIGHLY_CONFIDENTIAL": Decision(offline_policy_high),
            "CONFIDENTIAL": Decision(offline_policy_med),
            "INTERNAL": Decision(offline_policy_low),
            "PUBLIC": Decision(offline_policy_low),
            "UNKNOWN": Decision(offline_policy_med),
        }

    async def evaluate_operation(self, event: EndpointEvent) -> EnforcementDecision:
        """Request a risk evaluation and policy decision from the backend.

        Args:
            event: The fully normalized event, including local classification.

        Returns:
            An EnforcementDecision from the server, or an OfflineDecision
            if the server is unreachable.
        """
        # We must first ensure the event is ingested by the server so it can
        # evaluate it properly (Phase 4 requires the event in the DB)
        event_dict = event.to_api_dict()
        result = await self._transport.send_event(event_dict)

        if not result.success:
            logger.warning(
                "Could not send event %s to server for evaluation: %s",
                event.event_id[:12],
                result.error,
            )
            return self._create_offline_decision(event)

        # Now request evaluation
        eval_payload = {
            "event_id": event.event_id,
            "classification_id": None,  # Let backend pick the latest
        }

        # We need a new endpoint on the backend or we use the Phase 4 evaluate
        # endpoint (POST /api/v1/risk/evaluate)
        eval_result = await self._transport._request_with_retry(
            "POST", "/api/v1/risk/evaluate", json_data=eval_payload
        )

        if not eval_result.success or not eval_result.data:
            logger.warning(
                "Evaluation failed for event %s: %s",
                event.event_id[:12],
                eval_result.error,
            )
            return self._create_offline_decision(event)

        data = eval_result.data
        try:
            return EnforcementDecision(
                event_id=event.event_id,
                risk_assessment_id=data.get("id"),
                decision=Decision(data.get("decision", "BLOCK")),
                policy_id=data.get("policy_id"),
                risk_score=data.get("risk_score", 0.0),
                risk_level=data.get("risk_level", "UNKNOWN"),
                explanation=data.get("explanation", ""),
            )
        except (ValueError, TypeError) as exc:
            logger.error("Invalid decision payload from server: %s", exc)
            return self._create_offline_decision(event)

    def _create_offline_decision(self, event: EndpointEvent) -> EnforcementDecision:
        """Generate a fail-safe decision when the server is unreachable."""
        sensitivity = "UNKNOWN"
        if event.classification:
            sensitivity = event.classification.sensitivity_level.value

        decision = self._offline_policy.get(sensitivity, Decision.HOLD)
        logger.info(
            "Offline policy applied for %s sensitivity: %s",
            sensitivity,
            decision.value,
        )

        return EnforcementDecision(
            event_id=event.event_id,
            decision=decision,
            risk_level=sensitivity,
            explanation="Server unavailable — applied offline fail-safe policy",
            source="offline_fallback",
        )

    async def check_approval_status(self, operation_id: str, event_id: str) -> dict[str, Any]:
        """Poll the server for the status of an approval request.

        Returns:
            Dict with 'status', 'approval_id', 'reason'
        """
        # Query approval requests for this event
        result = await self._transport._request_with_retry(
            "GET", f"/api/v1/approvals?event_id={event_id}"
        )

        if not result.success or not result.data:
            return {"status": "PENDING"}

        items = result.data.get("items", [])
        if not items:
            return {"status": "PENDING"}

        # Use the most recent request
        latest = items[0]
        return {
            "status": latest.get("status", "PENDING"),
            "approval_id": str(latest.get("id", "")),
            "reason": latest.get("reviewer_comment", ""),
        }

    async def submit_result(self, result_dict: dict[str, Any]) -> bool:
        """Submit the final enforcement result to the server."""
        # We need a new endpoint for Phase 5 to store enforcement results
        response = await self._transport._request_with_retry(
            "POST", "/api/v1/enforcement/results", json_data=result_dict
        )
        if not response.success:
            logger.warning(
                "Failed to submit enforcement result for operation %s: %s",
                result_dict.get("operation_id", "unknown")[:12],
                response.error,
            )
            return False
        return True
