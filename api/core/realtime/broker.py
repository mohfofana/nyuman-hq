import asyncio
from typing import Any, Dict, Set


class Broker:
    """Diffuse les changements de la maison à tous les écrans ouverts (Server-Sent Events).

    En mémoire : suffit pour un seul serveur. Avec plusieurs serveurs, il faudra passer par
    Postgres LISTEN/NOTIFY ou Redis.
    """

    def __init__(self) -> None:
        self._queues: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._queues.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._queues.discard(queue)

    def publish(self, message: Dict[str, Any]) -> None:
        for queue in list(self._queues):
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass  # écran trop lent : il se remettra à jour à sa prochaine lecture

    @property
    def subscribers(self) -> int:
        return len(self._queues)


broker = Broker()
