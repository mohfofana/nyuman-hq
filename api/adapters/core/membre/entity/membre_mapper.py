from adapters.core.membre.entity.membre_entity import MembreEntity
from domain.entities.membre import Membre

_FIELDS = ("kind", "name", "email", "role", "title", "pole", "initials", "color", "status", "active", "last_seen_at", "created_at")


class MembreMapper:
    @staticmethod
    def to_domain(entity: MembreEntity) -> Membre:
        return Membre(id=entity.id, **{f: getattr(entity, f) for f in _FIELDS})

    @staticmethod
    def apply(membre: Membre, entity: MembreEntity) -> MembreEntity:
        for f in _FIELDS:
            setattr(entity, f, getattr(membre, f))
        return entity
