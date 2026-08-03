"""Add auditable reviewer resolutions for validation findings.

Revision ID: 20260731_0003
Revises: 20260731_0002
Create Date: 2026-07-31 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_0003"
down_revision = "20260731_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finding_resolutions",
        sa.Column("resolution_id", sa.Text(), primary_key=True),
        sa.Column("package_id", sa.Text(), sa.ForeignKey("document_packages.package_id"), nullable=False),
        sa.Column("finding_id", sa.Text(), sa.ForeignKey("validation_findings.finding_id"), nullable=False),
        sa.Column("reviewer", sa.Text(), nullable=False),
        sa.Column("resolution_status", sa.Text(), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_finding_resolutions_package_id", "finding_resolutions", ["package_id"], unique=False)
    op.create_index("idx_finding_resolutions_finding_id", "finding_resolutions", ["finding_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_finding_resolutions_finding_id", table_name="finding_resolutions")
    op.drop_index("idx_finding_resolutions_package_id", table_name="finding_resolutions")
    op.drop_table("finding_resolutions")
