# Evaluator Guide

1. Run the seed command documented in the README.
2. Sign in with the local administrator account.
3. Review the Knowledge registry. The ten `NSF-ADV-*` records are quarantined injection cases and cannot be selected as sources.
4. Inspect `NSF-SEC` versions 1.0 and 2.0 to demonstrate active versus obsolete handling.
5. Review the 160 matrix records, each linked to a chunk ID and document version.
6. Use the generated employee IDs `NSF-E001` through `NSF-E010` when creating a plan. With `GENERATION_MODE=mock`, plans are produced offline from approved evidence; switch to `auto` and add OpenAI credits to exercise live structured generation.
7. Validate a generated plan, then approve it only after a verified result. Use the audit endpoint to inspect the resulting record.
8. Call `/documents/NSF-SEC/impact` after uploading a replacement version to identify impacted requirements and plans.

The requirements CSV is available at `/reports/requirements.csv` to authenticated administrators, training managers, and reviewers.
