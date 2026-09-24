from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("document_id", "version", name="uq_document_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64))
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version: Mapped[str] = mapped_column(String(32))
    effective_date: Mapped[date] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_quarantined: Mapped[bool] = mapped_column(Boolean, default=False)
    injection_flags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_db_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    document_id: Mapped[str] = mapped_column(String(64), index=True)
    document_version: Mapped[str] = mapped_column(String(32))
    chunk_id: Mapped[str] = mapped_column(String(96), unique=True)
    section_id: Mapped[str] = mapped_column(String(64))
    heading: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_location: Mapped[str] = mapped_column(String(128))
    text: Mapped[str] = mapped_column(Text)


class RoleRequirement(Base):
    __tablename__ = "role_requirements"
    __table_args__ = (UniqueConstraint("requirement_id", "role", name="uq_requirement_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(128), index=True)
    requirement: Mapped[str] = mapped_column(Text)
    competency: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean)
    priority: Mapped[str] = mapped_column(String(16))
    due_stage: Mapped[str] = mapped_column(String(32))
    source_document_id: Mapped[str] = mapped_column(String(64))
    source_document_version: Mapped[str] = mapped_column(String(32))
    source_section_id: Mapped[str] = mapped_column(String(64))
    source_chunk_id: Mapped[str] = mapped_column(String(96))
    assessment_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)
    approval_status: Mapped[str] = mapped_column(String(32), default="Approved")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="employee")
    employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(128), index=True)
    department: Mapped[str] = mapped_column(String(128))
    experience_level: Mapped[str] = mapped_column(String(32))
    joining_date: Mapped[date] = mapped_column(Date)
    manager: Mapped[str | None] = mapped_column(String(128), nullable=True)
    training_status: Mapped[str] = mapped_column(String(32), default="Not Started")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="Draft")
    prompt_version: Mapped[str] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_versions: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(128))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(128))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
