"""Service layer for handling enforcement result records."""

from sqlalchemy.orm import Session

from app.models.enforcement import EnforcementResultRecord
from app.schemas.enforcement import EnforcementResultCreate


def create_enforcement_result(
    db: Session,
    result_in: EnforcementResultCreate,
) -> EnforcementResultRecord:
    """Create a new enforcement result record reported by an agent."""
    db_result = EnforcementResultRecord(
        operation_id=result_in.operation_id,
        status=result_in.status,
        decision=result_in.decision,
        started_at=result_in.started_at,
        completed_at=result_in.completed_at,
        source_hash=result_in.source_hash,
        destination_hash=result_in.destination_hash,
        bytes_transferred=result_in.bytes_transferred,
        reason_code=result_in.reason_code,
        error_code=result_in.error_code,
        message=result_in.message,
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


def get_enforcement_results(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[EnforcementResultRecord]:
    """Retrieve enforcement results."""
    return db.query(EnforcementResultRecord).offset(skip).limit(limit).all()
