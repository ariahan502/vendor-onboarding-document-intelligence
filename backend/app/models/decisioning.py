from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import json_type


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    rule_id: Mapped[str] = mapped_column(Text, primary_key=True)
    rule_name: Mapped[str] = mapped_column(Text, nullable=False)
    rule_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    rule_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    decision_impact: Mapped[str | None] = mapped_column(Text)
    condition_expression: Mapped[str] = mapped_column(Text, nullable=False)
    rule_version: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RoutingPolicy(Base):
    __tablename__ = "routing_policies"

    routing_policy_id: Mapped[str] = mapped_column(Text, primary_key=True)
    policy_name: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    routing_expression: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ValidationFinding(Base):
    __tablename__ = "validation_findings"

    finding_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.document_id"))
    comparison_id: Mapped[str | None] = mapped_column(
        ForeignKey("field_comparisons.comparison_id")
    )
    rule_id: Mapped[str | None] = mapped_column(ForeignKey("policy_rules.rule_id"))
    finding_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    finding_status: Mapped[str] = mapped_column(Text, nullable=False, default="open")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action: Mapped[str | None] = mapped_column(Text)
    requires_human_review: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DecisionEvidence(Base):
    __tablename__ = "decision_evidence"

    evidence_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("validation_findings.finding_id")
    )
    field_id: Mapped[str | None] = mapped_column(ForeignKey("extracted_fields.field_id"))
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.document_id"))
    evidence_type: Mapped[str] = mapped_column(Text, nullable=False)
    page_num: Mapped[int | None] = mapped_column(Integer)
    snippet_text: Mapped[str | None] = mapped_column(Text)
    bbox: Mapped[dict | None] = mapped_column(json_type)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    decision_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(Text, nullable=False)
    system_recommendation: Mapped[str | None] = mapped_column(Text)
    final_decision: Mapped[str] = mapped_column(Text, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text)
    reviewer_comment: Mapped[str | None] = mapped_column(Text)
    decision_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FieldReviewOverride(Base):
    """Append-only reviewer corrections for extracted fields."""

    __tablename__ = "field_review_overrides"

    override_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    field_id: Mapped[str] = mapped_column(
        ForeignKey("extracted_fields.field_id"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(Text, nullable=False)
    original_value: Mapped[str | None] = mapped_column(Text)
    corrected_value: Mapped[str] = mapped_column(Text, nullable=False)
    correction_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FindingResolution(Base):
    """Append-only reviewer actions that close or accept a validation finding."""

    __tablename__ = "finding_resolutions"

    resolution_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("validation_findings.finding_id"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
