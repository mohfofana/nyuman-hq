from adapters.core.document.entity.document_entity import DocumentEntity, DocumentVersionEntity
from domain.entities.document import Document, DocumentVersion

_DOC_FIELDS = ("title", "category", "content", "version", "archived", "created_by", "created_at", "updated_by", "updated_at")
_VERSION_FIELDS = ("document_id", "version", "title", "category", "content", "author_id", "created_at")


class DocumentMapper:
    @staticmethod
    def to_domain(entity: DocumentEntity) -> Document:
        return Document(id=entity.id, **{f: getattr(entity, f) for f in _DOC_FIELDS})

    @staticmethod
    def apply(document: Document, entity: DocumentEntity) -> DocumentEntity:
        for f in _DOC_FIELDS:
            setattr(entity, f, getattr(document, f))
        return entity

    @staticmethod
    def version_to_domain(entity: DocumentVersionEntity) -> DocumentVersion:
        return DocumentVersion(id=entity.id, **{f: getattr(entity, f) for f in _VERSION_FIELDS})

    @staticmethod
    def version_to_entity(version: DocumentVersion) -> DocumentVersionEntity:
        return DocumentVersionEntity(**{f: getattr(version, f) for f in _VERSION_FIELDS})
