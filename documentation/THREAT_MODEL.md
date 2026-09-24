# Security and Threat Model

| Threat | Control |
| --- | --- |
| Prompt injection in documents | Pattern detection, quarantine state, and generation retrieval limited to active non-quarantined evidence. |
| Hallucinated company rules | Schema-constrained output plus deterministic matrix and immutable-citation validation. |
| Obsolete policy use | Active version status and source-version validation. |
| Unauthorized changes | JWT authentication, role checks, and audit events. |
| Unbounded uploads | PDF/DOCX allow-list, empty-file rejection, duplicate hash check, and configurable size cap. |
| Silent model failures | JSON schema parsing, two bounded retries, and explicit errors. |

Production deployments must use HTTPS, environment-managed secrets, a managed database, malware scanning for uploads, rate limiting, backups, and a data-retention policy.
