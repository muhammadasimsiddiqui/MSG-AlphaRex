from sqlalchemy.orm import Session

from ..models import Document, DocumentChunk


def evidence_for_requirements(db: Session, requirements) -> list[dict]:
    """Retrieve immutable approved chunks; no document text is trusted as instructions."""
    evidence = []
    for requirement in requirements:
        document = db.query(Document).filter(
            Document.document_id == requirement.source_document_id,
            Document.version == requirement.source_document_version,
            Document.is_active.is_(True),
            Document.is_quarantined.is_(False),
        ).first()
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.chunk_id == requirement.source_chunk_id,
            DocumentChunk.document_version == requirement.source_document_version,
        ).first()
        if document and chunk:
            evidence.append({
                "requirement_id": requirement.requirement_id,
                "document_id": document.document_id,
                "document_version": document.version,
                "section_id": chunk.section_id,
                "chunk_id": chunk.chunk_id,
                "evidence_text": chunk.text,
            })
    return evidence
