from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import json_type


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    eval_case_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str | None] = mapped_column(ForeignKey("document_packages.package_id"))
    case_name: Mapped[str] = mapped_column(Text, nullable=False)
    case_slice: Mapped[str | None] = mapped_column(Text)
    expected_fields: Mapped[dict | None] = mapped_column(json_type)
    expected_findings: Mapped[dict | None] = mapped_column(json_type)
    expected_decision: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    eval_run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    eval_case_id: Mapped[str] = mapped_column(
        ForeignKey("evaluation_cases.eval_case_id"), nullable=False, index=True
    )
    run_label: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    rule_version: Mapped[str | None] = mapped_column(Text)
    extraction_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    finding_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    routing_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    reviewer_agreement_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    run_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    run_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
