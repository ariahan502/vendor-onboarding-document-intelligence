"""Add append-only reviewer corrections for extracted fields.

Revision ID: 20260731_0002
Revises: 20260730_0001
Create Date: 2026-07-31 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260731_0002"
down_revision = "20260730_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "field_review_overrides",
        sa.Column("override_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column(
            "field_id",
            sa.Text(),
            sa.ForeignKey("extracted_fields.field_id"),
            nullable=False,
        ),
        sa.Column("reviewer", sa.Text(), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=True),
        sa.Column("corrected_value", sa.Text(), nullable=False),
        sa.Column("correction_reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_field_review_overrides_package_id",
        "field_review_overrides",
        ["package_id"],
        unique=False,
    )
    op.create_index(
        "idx_field_review_overrides_field_id",
        "field_review_overrides",
        ["field_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_field_review_overrides_field_id", table_name="field_review_overrides")
    op.drop_index("idx_field_review_overrides_package_id", table_name="field_review_overrides")
    op.drop_table("field_review_overrides")
