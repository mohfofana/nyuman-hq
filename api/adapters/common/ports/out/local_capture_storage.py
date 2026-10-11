import re
from pathlib import Path

from use_cases.common.ports.out.testflight_gateway import CaptureStorage

_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]{1,120}$")


class LocalCaptureStorage(CaptureStorage):
    """Captures gardées sur le disque du serveur (sur le serveur de Nyuman : un volume Docker persistant)."""

    def __init__(self, base_dir: Path):
        self._dir = Path(base_dir) / "captures"

    def save(self, name: str, content: bytes) -> str:
        target = self.path(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return name

    def path(self, name: str) -> Path:
        # Un nom de fichier seul, jamais de chemin : impossible de sortir du dossier des captures.
        if not _SAFE_NAME.match(name) or name.startswith("."):
            raise ValueError("Nom de capture invalide.")
        return self._dir / name
