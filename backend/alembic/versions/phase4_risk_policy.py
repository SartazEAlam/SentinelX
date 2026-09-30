"""Phase 4 — Risk Assessment and Policy Engine

Revision ID: phase4_risk_policy
Revises: 711bca788751
Create Date: 2026-09-28

Creates:
  - risk_assessments table
  - Adds Phase 4 columns to policies (version, is_deleted, updated_by,
    min_risk_score, max_risk_score, action_types, destination_types)
  - Adds Phase 4 columns to approval_requests (risk_assessment_id,
    requested_action, expires_at, policy_id, policy_version)
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "phase4_risk_policy"
down_revision: str | None = "711bca788751"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Create risk_assessments table ────────────────────────────────────
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(64), nullable=False, index=True),
        sa.Column("risk_engine_version", sa.String(32), nullable=False),
        sa.Column("policy_engine_version", sa.String(32), nullable=False),
        sa.Column("risk_config_version", sa.String(32), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=True),
        sa.Column("policy_name", sa.String(128), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=True),
        sa.Column("factor_breakdown_json", sa.Text(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_risk_assessments_event_id", "risk_assessments", ["event_id"])
    op.create_index("ix_risk_assessments_risk_level", "risk_assessments", ["risk_level"])
    op.create_index("ix_risk_assessments_decision", "risk_assessments", ["decision"])
    op.create_index("ix_risk_assessments_created_at", "risk_assessments", ["created_at"])

    # ── Extend policies table ────────────────────────────────────────────
    with op.batch_alter_table("policies") as batch_op:
        batch_op.add_column(
            sa.Column("min_risk_score", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("max_risk_score", sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("action_types", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("destination_types", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("version", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.add_column(
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column(
                "updated_by",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=True,
            )
        )

    op.create_index("ix_policies_is_deleted", "policies", ["is_deleted"])

    # ── Extend approval_requests table ───────────────────────────────────
    with op.batch_alter_table("approval_requests") as batch_op:
        batch_op.add_column(
            sa.Column("risk_assessment_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("requested_action", sa.String(64), nullable=True)
        )
        batch_op.add_column(
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("policy_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("policy_version", sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    # ── Remove approval_requests Phase 4 columns ────────────────────────
    with op.batch_alter_table("approval_requests") as batch_op:
        batch_op.drop_column("policy_version")
        batch_op.drop_column("policy_id")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("requested_action")
        batch_op.drop_column("risk_assessment_id")

    # ── Remove policies Phase 4 columns ─────────────────────────────────
    op.drop_index("ix_policies_is_deleted", table_name="policies")
    with op.batch_alter_table("policies") as batch_op:
        batch_op.drop_column("updated_by")
        batch_op.drop_column("is_deleted")
        batch_op.drop_column("version")
        batch_op.drop_column("destination_types")
        batch_op.drop_column("action_types")
        batch_op.drop_column("max_risk_score")
        batch_op.drop_column("min_risk_score")

    # ── Drop risk_assessments table ──────────────────────────────────────
    op.drop_index("ix_risk_assessments_created_at", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_decision", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_risk_level", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_event_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
