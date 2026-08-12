"""Add append-only policy revision proposals.

Revision ID: 20260804_0007
Revises: 20260803_0006
"""
from alembic import op
import sqlalchemy as sa

revision = "20260804_0007"
down_revision = "20260803_0006"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("policy_rule_revisions", sa.Column("revision_id", sa.Text(), primary_key=True), sa.Column("rule_id", sa.Text(), sa.ForeignKey("policy_rules.rule_id"), nullable=False), sa.Column("proposed_expression", sa.Text(), nullable=False), sa.Column("proposed_severity", sa.Text(), nullable=False), sa.Column("change_reason", sa.Text(), nullable=False), sa.Column("proposed_by", sa.Text(), nullable=False), sa.Column("status", sa.Text(), nullable=False), sa.Column("evaluation_run_id", sa.Text(), sa.ForeignKey("evaluation_runs.eval_run_id")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("idx_policy_rule_revisions_rule_id", "policy_rule_revisions", ["rule_id"])

def downgrade() -> None:
    op.drop_index("idx_policy_rule_revisions_rule_id", table_name="policy_rule_revisions")
    op.drop_table("policy_rule_revisions")
