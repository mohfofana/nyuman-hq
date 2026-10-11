import asyncio
import json

from core.realtime.broker import Broker
from core.realtime.presence import PresenceRegistry
from adapters.core.presence.controller.presence_controller import live_stream


def _data(chunk: str) -> dict:
    assert chunk.startswith("data: ")
    return json.loads(chunk[len("data: "):])


def test_la_presence_suit_les_ecrans_ouverts():
    registry = PresenceRegistry()
    registry.connect(1)
    registry.connect(1)  # deux onglets
    registry.update(1, "bibliotheque", "lit « Pitch »", 4, False)
    assert registry.snapshot()[1].piece == "bibliotheque"
    assert registry.disconnect(1) is False  # un onglet reste ouvert
    assert registry.disconnect(1) is True
    assert registry.snapshot() == {}


async def test_le_flux_annonce_l_arrivee_relaie_et_annonce_le_depart():
    registry, bus = PresenceRegistry(), Broker()
    disconnected = asyncio.Event()

    async def is_disconnected() -> bool:
        return disconnected.is_set()

    stream = live_stream(7, registry, bus, is_disconnected, ping_seconds=0.05)
    hello = _data(await stream.__anext__())
    assert hello["type"] == "bonjour" and "7" in hello["presences"]

    watcher = bus.subscribe()
    bus.publish({"type": "evenement", "text": "a créé le document « Pitch »."})
    relayed = _data(await stream.__anext__())
    assert relayed["text"] == "a créé le document « Pitch »."

    assert await stream.__anext__() == ": ping\n\n"  # signe de vie

    disconnected.set()
    await stream.aclose()
    messages = []
    while not watcher.empty():
        messages.append(watcher.get_nowait())
    assert {"type": "presence", "membre_id": 7, "presence": None} in messages
    assert bus.subscribers == 1  # seul le témoin reste abonné
