"""Run one plan round-trip: generate (mock or live) then independently validate."""
import sys

sys.path.insert(0, ".")

from app.config import get_settings
from app.database import SessionLocal
from app.models import Employee, RoleRequirement
from app.schemas import GenerateRequest, OnboardingPlan
from app.services.generation import generate_plan
from app.services.validation import validate_plan

settings = get_settings()
print("genai_configured:", bool(settings.openai_api_key), "mode:", settings.generation_mode, "model:", settings.openai_model)

db = SessionLocal()
try:
    employee = db.query(Employee).first()
    requirements = db.query(RoleRequirement).filter(RoleRequirement.role == employee.role).all()
    print("employee:", employee.employee_id, employee.role)
    print("requirements:", len(requirements))
    request = GenerateRequest(employee_id=employee.employee_id, employee_name=employee.name, role=employee.role, experience_level="Beginner")
    versions = {item.source_document_id: item.source_document_version for item in requirements}
    plan = generate_plan(db, request, requirements, versions)
    print("modules:", len(plan.modules))
    first = plan.modules[0]
    print("sample module:", first.module_id, "|", first.module_title, "|", first.source_chunk_id, "| quiz:", len(first.quiz))
    parsing_check = OnboardingPlan.model_validate(plan.model_dump())
    print("schema round-trip:", "ok" if parsing_check.modules else "failed")
    result = validate_plan(plan, requirements)
    print("validation:", result.status, "| coverage:", result.coverage_score, "| traceability:", result.traceability_score)
    print("issues:", len(result.issues))
finally:
    db.close()