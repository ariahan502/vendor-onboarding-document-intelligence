from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.processing import ExtractedField, ProcessingRun


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id: Mapped[str] = mapped_column(Text, primary_key=True)
    legal_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_legal_name: Mapped[str | None] = mapped_column(Text)
    tax_id: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    packages: Mapped[list["DocumentPackage"]] = relationship(back_populates="vendor")


class DocumentPackage(Base):
    __tablename__ = "document_packages"

    package_id: Mapped[str] = mapped_column(Text, primary_key=True)
    vendor_id: Mapped[str] = mapped_column(
        ForeignKey("vendors.vendor_id"), nullable=False, index=True
    )
    package_status: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    assigned_reviewer: Mapped[str | None] = mapped_column(Text)
    system_recommendation: Mapped[str | None] = mapped_column(Text)
    final_decision: Mapped[str | None] = mapped_column(Text)
    priority_score: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    vendor: Mapped["Vendor"] = relationship(back_populates="packages")
    requirements: Mapped[list["DocumentRequirement"]] = relationship(
        back_populates="package"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="package")


class DocumentRequirement(Base):
    __tablename__ = "document_requirements"

    requirement_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False
    )
    required_doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_satisfied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    missing_reason: Mapped[str | None] = mapped_column(Text)

    package: Mapped["DocumentPackage"] = relationship(back_populates="requirements")


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[str] = mapped_column(Text, primary_key=True)
    package_id: Mapped[str] = mapped_column(
        ForeignKey("document_packages.package_id"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    document_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    upload_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="uploaded"
    )
    ocr_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    parse_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    package: Mapped["DocumentPackage"] = relationship(back_populates="documents")
    processing_runs: Mapped[list["ProcessingRun"]] = relationship(
        back_populates="document"
    )
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(
        back_populates="document"
    )
