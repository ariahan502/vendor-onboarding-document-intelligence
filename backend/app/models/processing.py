from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import json_type

if TYPE_CHECKING:
    from app.models.documents import Document


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    processing_run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False
    )
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.document_id"))
    run_type: Mapped[str] = mapped_column(Text, nullable=False)
    run_status: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    document: Mapped["Document | None"] = relationship(back_populates="processing_runs")
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(
        back_populates="processing_run"
    )


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    field_id: Mapped[str] = mapped_column(Text, primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.document_id"), nullable=False, index=True
    )
    processing_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("processing_runs.processing_run_id")
    )
    field_name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_span_text: Mapped[str | None] = mapped_column(Text)
    source_bbox: Mapped[dict | None] = mapped_column(json_type)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document: Mapped["Document"] = relationship(back_populates="extracted_fields")
    processing_run: Mapped["ProcessingRun | None"] = relationship(
        back_populates="extracted_fields"
    )
    normalizations: Mapped[list["FieldNormalization"]] = relationship(
        back_populates="field"
    )


class FieldNormalization(Base):
    __tablename__ = "field_normalizations"

    normalization_id: Mapped[str] = mapped_column(Text, primary_key=True)
    field_id: Mapped[str] = mapped_column(
        ForeignKey("extracted_fields.field_id"), nullable=False
    )
    normalized_value: Mapped[str | None] = mapped_column(Text)
    normalized_value_json: Mapped[dict | None] = mapped_column(json_type)
    normalization_method: Mapped[str] = mapped_column(Text, nullable=False)
    normalization_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    field: Mapped["ExtractedField"] = relationship(back_populates="normalizations")


class FieldComparison(Base):
    __tablename__ = "field_comparisons"

    comparison_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    left_field_id: Mapped[str] = mapped_column(
        ForeignKey("extracted_fields.field_id"), nullable=False
    )
    right_field_id: Mapped[str] = mapped_column(
        ForeignKey("extracted_fields.field_id"), nullable=False
    )
    comparison_type: Mapped[str] = mapped_column(Text, nullable=False)
    comparison_status: Mapped[str] = mapped_column(Text, nullable=False)
    similarity_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    requires_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    explanation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
