from collections import Counter

from ..schemas import OnboardingPlan, ValidationIssue, ValidationResult


def validate_plan(plan: OnboardingPlan, expected_requirements) -> ValidationResult:
    """Verify structured fields against the matrix without using an AI model."""
    expected = {item.requirement_id: item for item in expected_requirements}
    mandatory_ids = {item.requirement_id for item in expected_requirements if item.mandatory}
    generated = {module.requirement_id: module for module in plan.modules}
    issues: list[ValidationIssue] = []
    missing = sorted(mandatory_ids - generated.keys())
    unsupported = sorted(set(generated) - set(expected))

    for requirement_id in missing:
        issues.append(ValidationIssue(code="REQUIREMENT_MISSING", severity="error", requirement_id=requirement_id, message="Mandatory matrix requirement is absent from the plan."))
    for requirement_id in unsupported:
        issues.append(ValidationIssue(code="UNSUPPORTED_REQUIREMENT", severity="error", requirement_id=requirement_id, message="Generated requirement does not exist in the approved matrix."))

    traced = 0
    module_counts = Counter(module.module_id for module in plan.modules)
    duplicates = sorted(module_id for module_id, count in module_counts.items() if count > 1)
    for module_id in duplicates:
        issues.append(ValidationIssue(code="DUPLICATE_MODULE", severity="warning", message="Duplicate module ID detected.", requirement_id=None))

    stages = ["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"]
    for module in plan.modules:
        requirement = expected.get(module.requirement_id)
        if not requirement:
            continue
        source_matches = (
            module.source_document_id == requirement.source_document_id
            and module.source_document_version == requirement.source_document_version
            and module.source_section_id == requirement.source_section_id
            and module.source_chunk_id == requirement.source_chunk_id
        )
        if source_matches:
            traced += 1
        else:
            issues.append(ValidationIssue(code="SOURCE_MISMATCH", severity="error", requirement_id=module.requirement_id, message="Generated source does not match the approved matrix."))
        if module.role != plan.role or module.role != requirement.role:
            issues.append(ValidationIssue(code="ROLE_MISMATCH", severity="error", requirement_id=module.requirement_id, message="Generated item is not relevant to the selected role."))
        if module.mandatory != requirement.mandatory:
            issues.append(ValidationIssue(code="MANDATORY_MISMATCH", severity="error", requirement_id=module.requirement_id, message="Mandatory status differs from the matrix."))
        if module.priority != requirement.priority:
            issues.append(ValidationIssue(code="PRIORITY_MISMATCH", severity="error", requirement_id=module.requirement_id, message="Priority differs from the matrix."))
        if module.due_stage not in stages or stages.index(module.due_stage) < max((stages.index(expected[p].due_stage) for p in module.prerequisites if p in expected), default=-1):
            issues.append(ValidationIssue(code="SEQUENCE_ERROR", severity="error", requirement_id=module.requirement_id, message="Module is scheduled before a required prerequisite."))

    coverage = round((len(mandatory_ids - set(missing)) / len(mandatory_ids) * 100) if mandatory_ids else 100, 2)
    traceability = round((traced / len(plan.modules) * 100) if plan.modules else 0, 2)
    consistency = round((sum(1 for issue in issues if issue.severity == "error") == 0) * 100, 2)
    if missing:
        status = "Incomplete"
    elif unsupported:
        status = "Unsupported"
    elif any(issue.severity == "error" for issue in issues):
        status = "Manual Review Required"
    elif issues:
        status = "Verified with Warning"
    else:
        status = "Verified"
    return ValidationResult(status=status, coverage_score=coverage, traceability_score=traceability, consistency_score=consistency, missing_requirement_ids=missing, unsupported_requirement_ids=unsupported, duplicate_module_ids=duplicates, issues=issues)
