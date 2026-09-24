from datetime import date
import csv
import copy
from io import StringIO
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .config import get_settings
from .database import Base, engine, get_db
from .models import AuditEvent, Document, DocumentChunk, Employee, Plan, RoleRequirement, User, ValidationRun
from .schemas import DocumentOut, EmployeeCreate, EmployeeOut, GenerateRequest, LoginRequest, OnboardingPlan, PlanOut, ProgressUpdate, RequirementCreate, RequirementOut, ReviewDecision, UserOut, ValidationResult
from .security import create_token, current_user, hash_password, require_roles, verify_password
from .services.audit import record_audit
from .services.documents import ingest_document
from .services.generation import generate_plan
from .services.validation import validate_plan

settings = get_settings()
Path("../data").mkdir(exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)


def ensure_default_users():
    from .database import SessionLocal
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@skillsprint.local").first():
            db.add(User(email="admin@skillsprint.local", display_name="System Administrator", password_hash=hash_password("ChangeMe123!"), role="admin"))
            db.add(User(email="reviewer@skillsprint.local", display_name="Quality Reviewer", password_hash=hash_password("ChangeMe123!"), role="reviewer"))
            db.commit()
    finally:
        db.close()


ensure_default_users()

app = FastAPI(title="SkillSprint AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "genai_configured": bool(settings.openai_api_key)}


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    return {"access_token": create_token(user), "token_type": "bearer", "user": {"email": user.email, "display_name": user.display_name, "role": user.role}}


@app.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.post("/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_id: str = Form(...),
    title: str = Form(...),
    category: str = Form(...),
    version: str = Form(...),
    effective_date: date = Form(...),
    department: str | None = Form(None),
    expiry_date: date | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin", "training_manager")),
):
    document = await ingest_document(db, file, document_id, title, category, department, version, effective_date, expiry_date, settings.max_upload_bytes)
    record_audit(db, user.email, "DOCUMENT_UPLOADED", "Document", document_id, {"version": version, "quarantined": document.is_quarantined})
    db.commit()
    return document


@app.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(Document).order_by(Document.document_id, Document.effective_date.desc()).all()


@app.get("/documents/{document_id}/chunks")
def list_chunks(document_id: str, version: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id, DocumentChunk.document_version == version).all()


@app.get("/documents/{document_id}/impact")
def document_impact(document_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager", "reviewer"))):
    requirements = db.query(RoleRequirement).filter(RoleRequirement.source_document_id == document_id).all()
    affected = [plan for plan in db.query(Plan).all() if document_id in plan.source_versions]
    active = db.query(Document).filter(Document.document_id == document_id, Document.is_active.is_(True)).first()
    return {
        "document_id": document_id,
        "active_version": active.version if active else None,
        "affected_requirement_ids": [item.requirement_id for item in requirements],
        "affected_plan_ids": [plan.id for plan in affected],
        "action": "Regenerate only the listed plans after reviewing matrix requirements tied to the updated source.",
    }


@app.post("/requirements", response_model=RequirementOut, status_code=201)
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager"))):
    source = db.query(Document).filter(Document.document_id == payload.source_document_id, Document.version == payload.source_document_version, Document.is_active.is_(True), Document.is_quarantined.is_(False)).first()
    if not source:
        raise HTTPException(422, "Requirement source must be an active, non-quarantined uploaded document version.")
    if not db.query(DocumentChunk).filter(DocumentChunk.chunk_id == payload.source_chunk_id, DocumentChunk.document_version == payload.source_document_version).first():
        raise HTTPException(422, "Requirement must cite an existing immutable source chunk.")
    if db.query(RoleRequirement).filter(RoleRequirement.requirement_id == payload.requirement_id, RoleRequirement.role == payload.role).first():
        raise HTTPException(409, "Requirement ID already exists.")
    requirement = RoleRequirement(**payload.model_dump())
    db.add(requirement)
    record_audit(db, user.email, "REQUIREMENT_CREATED", "RoleRequirement", payload.requirement_id, {"role": payload.role})
    db.commit()
    db.refresh(requirement)
    return requirement


@app.get("/requirements", response_model=list[RequirementOut])
def list_requirements(role: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(RoleRequirement)
    if role:
        query = query.filter(RoleRequirement.role == role)
    return query.order_by(RoleRequirement.role, RoleRequirement.requirement_id).all()


@app.post("/employees", response_model=EmployeeOut, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager", "manager"))):
    if db.query(Employee).filter(Employee.employee_id == payload.employee_id).first():
        raise HTTPException(409, "Employee ID already exists.")
    employee = Employee(**payload.model_dump())
    db.add(employee)
    record_audit(db, user.email, "EMPLOYEE_CREATED", "Employee", employee.employee_id, {"role": employee.role})
    db.commit(); db.refresh(employee)
    return employee


@app.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(Employee).order_by(Employee.name).all()


@app.post("/plans/generate", response_model=PlanOut, status_code=201)
def create_plan(payload: GenerateRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager"))):
    employee = db.query(Employee).filter(Employee.employee_id == payload.employee_id).first()
    if not employee or employee.role != payload.role:
        raise HTTPException(422, "Employee must exist and match the selected onboarding role.")
    requirements = db.query(RoleRequirement).filter(RoleRequirement.role == payload.role).all()
    document_ids = {item.source_document_id for item in requirements}
    active_documents = db.query(Document).filter(Document.document_id.in_(document_ids), Document.is_active.is_(True)).all()
    versions = {document.document_id: document.version for document in active_documents}
    generated = generate_plan(db, payload, requirements, versions)
    model_label = None if (not settings.openai_api_key or settings.generation_mode == "mock") else settings.openai_model
    plan = Plan(employee_id=payload.employee_id, role=payload.role, payload=generated.model_dump(), prompt_version=generated.prompt_version, model=model_label, source_versions=versions)
    db.add(plan)
    record_audit(db, user.email, "PLAN_GENERATED", "Plan", payload.employee_id, {"role": payload.role, "prompt_version": generated.prompt_version})
    db.commit(); db.refresh(plan)
    return plan


@app.post("/plans/validate", response_model=ValidationResult)
def validate_generated_plan(plan: OnboardingPlan, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager", "reviewer"))):
    requirements = db.query(RoleRequirement).filter(RoleRequirement.role == plan.role).all()
    if not requirements:
        raise HTTPException(422, "No approved matrix requirements exist for this role.")
    return validate_plan(plan, requirements)


@app.get("/plans", response_model=list[PlanOut])
def list_plans(employee_id: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(Plan)
    if employee_id:
        query = query.filter(Plan.employee_id == employee_id)
    return query.order_by(Plan.created_at.desc()).all()


@app.post("/plans/{plan_id}/validate", response_model=ValidationResult)
def validate_saved_plan(plan_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager", "reviewer"))):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found.")
    result = validate_plan(OnboardingPlan.model_validate(plan.payload), db.query(RoleRequirement).filter(RoleRequirement.role == plan.role).all())
    db.add(ValidationRun(plan_id=plan.id, result=result.model_dump()))
    plan.status = result.status
    record_audit(db, user.email, "PLAN_VALIDATED", "Plan", str(plan_id), {"status": result.status, "coverage": result.coverage_score})
    db.commit()
    return result


@app.post("/plans/{plan_id}/review", response_model=PlanOut)
def review_plan(plan_id: int, decision: ReviewDecision, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "reviewer"))):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found.")
    latest = db.query(ValidationRun).filter(ValidationRun.plan_id == plan_id).order_by(ValidationRun.created_at.desc()).first()
    if decision.decision == "Approved" and (not latest or latest.result.get("status") not in {"Verified", "Verified with Warning"}):
        raise HTTPException(422, "Only a verified plan can be approved without an override.")
    plan.status = decision.decision
    record_audit(db, user.email, f"PLAN_{decision.decision.upper()}", "Plan", str(plan_id), {"comment": decision.comment, "prior_validation": latest.result if latest else None})
    db.commit(); db.refresh(plan)
    return plan


@app.get("/plans/{plan_id}/evidence")
def plan_evidence(plan_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found.")
    evidence = []
    for module in plan.payload.get("modules", []):
        chunk = db.query(DocumentChunk).filter(DocumentChunk.chunk_id == module["source_chunk_id"]).first()
        evidence.append({"module_id": module["module_id"], "requirement_id": module["requirement_id"], "document_id": module["source_document_id"], "document_version": module["source_document_version"], "section_id": module["source_section_id"], "chunk_id": module["source_chunk_id"], "excerpt": chunk.text if chunk else None})
    return evidence


@app.post("/plans/{plan_id}/progress", response_model=PlanOut)
def update_progress(plan_id: int, update: ProgressUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found.")
    payload = copy.deepcopy(plan.payload)
    modules = payload.get("modules", [])
    matching = next((module for module in modules if module["module_id"] == update.module_id), None)
    if not matching:
        raise HTTPException(404, "Module not found in this plan.")
    matching["progress"] = update.model_dump(exclude_none=True)
    payload["modules"] = modules
    completed = sum(bool(module.get("progress", {}).get("completed")) for module in modules)
    employee = db.query(Employee).filter(Employee.employee_id == plan.employee_id).first()
    if employee:
        employee.training_status = "Completed" if completed == len(modules) else "On Track" if completed else "Requires Attention"
    plan.payload = payload
    record_audit(db, user.email, "PROGRESS_UPDATED", "Plan", str(plan_id), {"module_id": update.module_id})
    db.commit(); db.refresh(plan)
    return plan


@app.get("/plans/{plan_id}/recommendations")
def recommendations(plan_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found.")
    results = []
    for module in plan.payload.get("modules", []):
        progress = module.get("progress", {})
        if progress.get("quiz_score") is not None and progress["quiz_score"] < 70:
            results.append({"module_id": module["module_id"], "recommendation": "Assign revision module and additional quiz.", "reason": "Quiz score below 70%."})
        elif not progress.get("task_complete", False):
            results.append({"module_id": module["module_id"], "recommendation": "Schedule manager review for incomplete practical task.", "reason": "Task incomplete."})
    return results


@app.get("/audit-events")
def list_audit_events(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "reviewer"))):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(min(limit, 500)).all()


@app.get("/reviews/queue")
def review_queue(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "reviewer"))):
    return db.query(Plan).filter(Plan.status.in_(["Manual Review Required", "Incomplete", "Unsupported", "Contradictory", "Draft"])).order_by(Plan.updated_at.desc()).all()


@app.get("/roles/dashboard")
def role_dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = []
    for role in sorted({item.role for item in db.query(RoleRequirement).all()}):
        requirements = db.query(RoleRequirement).filter(RoleRequirement.role == role).all()
        plans = db.query(Plan).filter(Plan.role == role).all()
        rows.append({"role": role, "requirements": len(requirements), "mandatory": sum(item.mandatory for item in requirements), "plans": len(plans), "approved_plans": sum(plan.status == "Approved" for plan in plans)})
    return rows


@app.get("/reports/overview")
def overview_report(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager", "reviewer", "manager"))):
    requirements = db.query(RoleRequirement).all()
    plans = db.query(Plan).all()
    validations = db.query(ValidationRun).all()
    latest_results = [run.result for run in validations]
    return {
        "employees": db.query(Employee).count(),
        "roles": len({item.role for item in requirements}),
        "documents": db.query(Document).count(),
        "quarantined_documents": db.query(Document).filter(Document.is_quarantined.is_(True)).count(),
        "requirements": len(requirements),
        "mandatory_requirements": sum(item.mandatory for item in requirements),
        "plans": len(plans),
        "approved_plans": sum(plan.status == "Approved" for plan in plans),
        "manual_review_plans": sum(result.get("status") == "Manual Review Required" for result in latest_results),
    }


@app.get("/reports/requirements.csv")
def export_requirements_csv(db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "training_manager", "reviewer"))):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Requirement ID", "Role", "Mandatory", "Priority", "Due Stage", "Source Document", "Source Version", "Source Section", "Source Chunk"])
    for item in db.query(RoleRequirement).order_by(RoleRequirement.role, RoleRequirement.requirement_id):
        writer.writerow([item.requirement_id, item.role, item.mandatory, item.priority, item.due_stage, item.source_document_id, item.source_document_version, item.source_section_id, item.source_chunk_id])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=skillsprint-requirements.csv"})
