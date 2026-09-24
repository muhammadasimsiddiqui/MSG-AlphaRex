from app.schemas import GenerateRequest
from app.services.generation import generate_mock_plan
from app.services.validation import validate_plan


class FakeRequirement:
    def __init__(self, requirement_id="R001", mandatory=True, priority="High", due_stage="Week 1"):
        self.requirement_id = requirement_id
        self.role = "Customer Support Executive"
        self.requirement = "Follow escalation policy"
        self.competency = "Escalation"
        self.mandatory = mandatory
        self.priority = priority
        self.due_stage = due_stage
        self.source_document_id = "SOP-07"
        self.source_document_version = "2.0"
        self.source_section_id = "4.2"
        self.source_chunk_id = "SOP-07-C001"
        self.assessment_topic = "Escalation"
        self.prerequisites = []


def test_mock_generator_produces_fully_verifiable_plan():
    requirements = [FakeRequirement("R001"), FakeRequirement("R002", mandatory=True, due_stage="Week 2")]
    versions = {"SOP-07": "2.0"}
    request = GenerateRequest(employee_id="E1", employee_name="Ayesha Khan", role="Customer Support Executive")
    plan = generate_mock_plan(request, requirements, {}, versions)
    assert len(plan.modules) == 2
    assert all(module.quiz and len(module.quiz[0].options) >= 2 for module in plan.modules)
    result = validate_plan(plan, requirements)
    assert result.status == "Verified"