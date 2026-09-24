# Architecture

1. An authorized administrator uploads a PDF or DOCX with business metadata.
2. The document pipeline validates it, extracts text, chunks it, and persists each chunk with document version and source location.
3. Suspicious instruction patterns result in quarantine. Quarantined documents cannot become active evidence.
4. A training manager creates Role Requirement Matrix rows pointing to immutable active chunks.
5. The generation service retrieves only those approved chunks and sends them as untrusted data alongside the versioned prompt template and JSON schema.
6. The generated plan is saved as a draft, retaining prompt version, model, and source versions.
7. The Python validation service independently compares every generated module to the matrix. It never uses an AI model.
8. A reviewer validates and approves, rejects, or overrides a plan. All decisions are audit events.

## Policy Precedence

Latest active approved policy or compliance standard > department SOP > process procedure > FAQ. A quarantined or obsolete document cannot be selected as source evidence.

## Verification Gate

A plan is `Verified` only when all mandatory requirements are present, every generated item matches its immutable evidence fields, and no validation errors remain. Plans with warnings may be approved by a reviewer; any override is explicitly recorded.
