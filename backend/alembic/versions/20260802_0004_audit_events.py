"""Add hash-chained, append-only audit events.

Revision ID: 20260802_0004
Revises: 20260731_0003
Create Date: 2026-08-02 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260802_0004"
down_revision = "20260731_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("actor_role", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("package_id", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("event_metadata", sa.JSON(), nullable=True),
        sa.Column("previous_event_hash", sa.Text(), nullable=True),
        sa.Column("event_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_audit_events_actor_id", "audit_events", ["actor_id"], unique=False)
    op.create_index("idx_audit_events_package_id", "audit_events", ["package_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_audit_events_package_id", table_name="audit_events")
    op.drop_index("idx_audit_events_actor_id", table_name="audit_events")
    op.drop_table("audit_events")
