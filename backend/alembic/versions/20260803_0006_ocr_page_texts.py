"""Retain page-level OCR text for traceability.

Revision ID: 20260803_0006
Revises: 20260803_0005
"""
from alembic import op
import sqlalchemy as sa

revision = "20260803_0006"
down_revision = "20260803_0005"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("ocr_page_texts", sa.Column("ocr_page_text_id", sa.Text(), primary_key=True), sa.Column("document_id", sa.Text(), sa.ForeignKey("documents.document_id"), nullable=False), sa.Column("processing_run_id", sa.Text(), sa.ForeignKey("processing_runs.processing_run_id")), sa.Column("page_number", sa.Integer(), nullable=False), sa.Column("source", sa.Text(), nullable=False), sa.Column("text_content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("idx_ocr_page_texts_document_id", "ocr_page_texts", ["document_id"])

def downgrade() -> None:
    op.drop_index("idx_ocr_page_texts_document_id", table_name="ocr_page_texts")
    op.drop_table("ocr_page_texts")
