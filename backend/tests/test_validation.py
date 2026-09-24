from app.schemas import OnboardingPlan
from app.services.validation import validate_plan


class Requirement:
    def __init__(self, requirement_id, mandatory=True):
        self.requirement_id = requirement_id
        self.role = "Customer Support Executive"
        self.requirement = "Follow escalation policy"
        self.competency = "Escalation"
        self.mandatory = mandatory
        self.priority = "High"
        self.due_stage = "Week 1"
        self.source_document_id = "SOP-07"
        self.source_document_version = "2.0"
        self.source_section_id = "4.2"
        self.source_chunk_id = "SOP-07-C001"


def make_plan(requirement_id="R001", source="SOP-07"):
    return OnboardingPlan.model_validate({
        "role": "Customer Support Executive",
        "employee_name": "Ayesha Khan",
        "prompt_version": "onboarding_v1",
        "source_document_versions": {"SOP-07": "2.0"},
        "modules": [{
            "requirement_id": requirement_id, "role": "Customer Support Executive", "module_id": "M001",
            "module_title": "Escalation process", "mandatory": True, "source_document_id": source,
            "source_document_version": "2.0", "source_section_id": "4.2", "source_chunk_id": "SOP-07-C001", "priority": "High", "due_stage": "Week 1",
            "learning_objectives": ["Apply the process"], "tasks": ["Complete a scenario"], "quiz": []
        }]
    })


def test_validator_reports_missing_mandatory_requirement():
    result = validate_plan(make_plan(), [Requirement("R001"), Requirement("R002")])
    assert result.status == "Incomplete"
    assert result.coverage_score == 50
    assert result.missing_requirement_ids == ["R002"]


def test_validator_rejects_unsupported_requirement():
    result = validate_plan(make_plan("UNKNOWN"), [Requirement("R001")])
    assert result.status == "Incomplete"
    assert "UNKNOWN" in result.unsupported_requirement_ids


def test_validator_reports_source_mismatch_for_manual_review():
    result = validate_plan(make_plan(source="SOP-OLD"), [Requirement("R001")])
    assert result.status == "Manual Review Required"
    assert result.traceability_score == 0
