import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from fastapi.concurrency import run_in_threadpool

from use_cases.common.ports.out.mail_sender import MailSender

logger = logging.getLogger("hq")


class SmtpMailSender(MailSender):
    """Envoi par la boîte Netim de Nyuman (SSL sur le port 465, ou STARTTLS sur le 587)."""

    def __init__(self, host: Optional[str], port: int, user: Optional[str], password: Optional[str], sender: Optional[str]):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._sender = sender or user

    @property
    def configured(self) -> bool:
        return all([self._host, self._user, self._password, self._sender])

    async def send(self, to: str, subject: str, text: str, html: str) -> None:
        message = EmailMessage()
        message["From"] = f"Nyuman HQ <{self._sender}>"
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        await run_in_threadpool(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        context = ssl.create_default_context()
        if self._port == 465:
            with smtplib.SMTP_SSL(self._host, self._port, context=context, timeout=15) as smtp:
                smtp.login(self._user, self._password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(self._host, self._port, timeout=15) as smtp:
                smtp.starttls(context=context)
                smtp.login(self._user, self._password)
                smtp.send_message(message)


class ConsoleMailSender(MailSender):
    """En développement, sans boîte mail : le lien s'affiche dans le journal du serveur au lieu d'être envoyé."""

    @property
    def configured(self) -> bool:
        return True

    async def send(self, to: str, subject: str, text: str, html: str) -> None:
        logger.warning("EMAIL (développement, non envoyé) à %s — %s\n%s", to, subject, text)
