from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RequirementCreate(BaseModel):
    requirement_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    role: str
    requirement: str
    competency: str | None = None
    mandatory: bool
    priority: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    due_stage: Literal["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"]
    source_document_id: str
    source_document_version: str
    source_section_id: str
    source_chunk_id: str
    assessment_topic: str | None = None
    prerequisites: list[str] = Field(default_factory=list)


class RequirementOut(RequirementCreate):
    model_config = ConfigDict(from_attributes=True)


class GeneratedItem(BaseModel):
    requirement_id: str
    role: str
    module_id: str
    module_title: str
    mandatory: bool
    source_document_id: str
    source_document_version: str
    source_section_id: str
    source_chunk_id: str
    priority: str
    due_stage: str
    learning_objectives: list[str] = Field(min_length=1)
    tasks: list[str] = Field(min_length=1)
    quiz: list["QuizItem"] = Field(default_factory=list)
    assessment_topic: str | None = None
    prerequisites: list[str] = Field(default_factory=list)


class QuizItem(BaseModel):
    question: str
    options: list[str] = Field(min_length=2)
    correct_answer: str
    explanation: str | None = None


class OnboardingPlan(BaseModel):
    role: str
    employee_name: str
    prompt_version: str
    source_document_versions: dict[str, str]
    modules: list[GeneratedItem] = Field(min_length=1)


class GenerateRequest(BaseModel):
    employee_id: str
    role: str
    employee_name: str
    experience_level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"


class ValidationIssue(BaseModel):
    code: str
    message: str
    requirement_id: str | None = None
    severity: Literal["warning", "error"]


class ValidationResult(BaseModel):
    status: Literal["Verified", "Verified with Warning", "Incomplete", "Unsupported", "Contradictory", "Manual Review Required"]
    coverage_score: float
    traceability_score: float
    consistency_score: float
    missing_requirement_ids: list[str]
    unsupported_requirement_ids: list[str]
    duplicate_module_ids: list[str]
    issues: list[ValidationIssue]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    document_id: str
    title: str
    category: str
    department: str | None
    version: str
    effective_date: date
    is_active: bool
    is_quarantined: bool
    injection_flags: list[str]


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    email: str
    display_name: str
    role: str


class EmployeeCreate(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    experience_level: Literal["Beginner", "Intermediate", "Advanced"]
    joining_date: date
    manager: str | None = None


class EmployeeOut(EmployeeCreate):
    model_config = ConfigDict(from_attributes=True)
    training_status: str


class ReviewDecision(BaseModel):
    decision: Literal["Approved", "Rejected", "Override"]
    comment: str = Field(min_length=3, max_length=1000)


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_id: str
    role: str
    payload: dict
    status: str
    prompt_version: str
    model: str | None
    source_versions: dict[str, str]


class ProgressUpdate(BaseModel):
    module_id: str
    completed: bool = False
    checklist_complete: bool = False
    task_complete: bool = False
    quiz_score: float | None = Field(default=None, ge=0, le=100)
    assessment_score: float | None = Field(default=None, ge=0, le=100)
