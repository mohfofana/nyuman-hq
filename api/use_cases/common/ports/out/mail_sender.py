from abc import ABC, abstractmethod


class MailSender(ABC):
    """Envoie un email (ici : le lien de connexion à HQ)."""

    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def send(self, to: str, subject: str, text: str, html: str) -> None: ...
