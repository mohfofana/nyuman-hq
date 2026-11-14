"""Envoi des e-mails de HQ (les liens de connexion), par le compte @nyuman.app de Netim.

Les identifiants viennent de l'environnement (HQ_SMTP_*) : ils ne sont ni écrits ici, ni affichés,
ni enregistrés. En local, sans réglage, on n'envoie rien : le lien s'affiche dans le journal du
serveur, ce qui suffit pour essayer.
"""
from __future__ import annotations

import asyncio
import smtplib
import socket
from email.message import EmailMessage

from app.config import settings


def configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def sender() -> str:
    return settings.mail_from or settings.smtp_user


def _deliver(s: smtplib.SMTP, msg: EmailMessage, to: str) -> str:
    """Envoie et renvoie la réponse du serveur (souvent un numéro de suivi), pour pouvoir la retrouver."""
    s.login(settings.smtp_user, settings.smtp_password)
    s.mail(settings.smtp_user)  # expéditeur réel : la boîte authentifiée
    code, resp = s.rcpt(to)
    if code >= 400:
        raise smtplib.SMTPRecipientsRefused({to: (code, resp)})
    code, resp = s.data(msg.as_bytes())
    return f"{code} {resp.decode(errors='replace')[:120]}"


def _send_now(to: str, subject: str, text: str, html: str) -> str:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender()
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, 465, timeout=25) as s:
            return _deliver(s, msg, to)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=25) as s:
        s.starttls()
        return _deliver(s, msg, to)


async def send(to: str, subject: str, text: str, html: str) -> bool:
    """Renvoie True si le message est parti. Un échec n'interrompt jamais la page."""
    if not configured():
        print(f"[courrier non configuré] à {to} : {text.splitlines()[0] if text else subject}", flush=True)
        return False
    try:
        reponse = await asyncio.to_thread(_send_now, to, subject, text, html)
        print(f"[courrier] accepté pour {to} par {settings.smtp_host} — {reponse}", flush=True)
        return True
    except Exception as e:  # jamais le mot de passe dans le journal
        # On montre ce que dit le serveur (jamais le mot de passe : il n'apparaît pas dans sa réponse).
        detail = "" if isinstance(e, (TimeoutError, socket.timeout)) else str(e)[:220]
        print(f"[courrier] échec de l'envoi à {to} : {type(e).__name__} {detail}", flush=True)
        return False


def login_link_message(url: str, minutes: int) -> tuple[str, str, str]:
    """Le message envoyé : court, clair, sans jargon."""
    subject = "Votre lien pour entrer dans Nyuman HQ"
    text = (
        "Bonjour,\n\n"
        f"Voici votre lien pour entrer dans Nyuman HQ :\n{url}\n\n"
        f"Il est valable {minutes} minutes et ne sert qu'une fois.\n"
        "Si vous n'avez rien demandé, ignorez ce message : personne ne peut entrer sans ce lien.\n\n"
        "— Nyuman HQ"
    )
    html = f"""<!doctype html><html lang="fr"><body style="margin:0;background:#F7F6F4;padding:24px;
font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1E1A17">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:16px;padding:28px">
    <p style="margin:0 0 4px;font-size:13px;color:#66615B">Nyuman HQ</p>
    <h1 style="margin:0 0 16px;font-size:20px">Votre lien pour entrer</h1>
    <p style="margin:0 0 20px;font-size:15px;line-height:1.5">Cliquez sur le bouton : vous serez connecté, sans mot de passe.</p>
    <p style="margin:0 0 20px"><a href="{url}" style="display:inline-block;background:#BC600D;color:#fff;
      text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:600;font-size:15px">Entrer dans HQ</a></p>
    <p style="margin:0 0 8px;font-size:13px;color:#66615B">Ce lien est valable {minutes} minutes et ne sert qu'une fois.</p>
    <p style="margin:0;font-size:13px;color:#9B968F">Si vous n'avez rien demandé, ignorez ce message.</p>
  </div>
</body></html>"""
    return subject, text, html
