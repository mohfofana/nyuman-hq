# Importe toutes les tables pour que Base.metadata soit complet (migrations, tests).
from adapters.core.decision.entity.decision_entity import DecisionEntity, VoteEntity  # noqa: F401
from adapters.core.document.entity.document_entity import DocumentEntity, DocumentVersionEntity  # noqa: F401
from adapters.core.etape.entity.etape_entity import EtapeEntity  # noqa: F401
from adapters.core.evenement.entity.evenement_entity import EvenementEntity  # noqa: F401
from adapters.core.lien.entity.lien_entity import LienEntity  # noqa: F401
from adapters.core.membre.entity.membre_entity import MembreEntity  # noqa: F401
from adapters.core.objectif.entity.objectif_entity import ObjectifEntity  # noqa: F401
from adapters.core.pro.entity.pro_entity import ProEntity  # noqa: F401
from adapters.core.rapport.entity.rapport_entity import RapportEntity  # noqa: F401
from adapters.core.retour.entity.retour_entity import RetourEntity  # noqa: F401
from adapters.core.tache.entity.tache_entity import TacheEntity  # noqa: F401
