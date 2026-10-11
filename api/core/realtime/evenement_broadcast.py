from sqlalchemy import event
from sqlalchemy.orm import Session

from core.realtime.broker import broker

# Ce qui part vers les écrans ne part qu'une fois enregistré pour de bon (après le commit).
PENDING_KEY = "hq_evenements_a_diffuser"
CHANGED_KEY = "hq_sujets_modifies"


def mark_changed(session, sujet: str) -> None:
    """Signale qu'un sujet (« taches », « retours »…) a changé : les écrans ouverts se mettront à jour."""
    session.info.setdefault(CHANGED_KEY, set()).add(sujet)


@event.listens_for(Session, "after_commit")
def _diffuser(session: Session) -> None:
    for entity in session.info.pop(PENDING_KEY, []):
        broker.publish(
            {
                "type": "evenement",
                "id": entity.id,
                "actor_id": entity.actor_id,
                "text": entity.text,
                "link": entity.link,
                "created_at": entity.created_at.isoformat(),
            }
        )
    sujets = session.info.pop(CHANGED_KEY, None)
    if sujets:
        broker.publish({"type": "changement", "sujets": sorted(sujets)})


@event.listens_for(Session, "after_rollback")
def _oublier(session: Session) -> None:
    session.info.pop(PENDING_KEY, None)
    session.info.pop(CHANGED_KEY, None)
