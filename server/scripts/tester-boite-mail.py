#!/usr/bin/env python3
"""Vérifie qu'une boîte mail accepte l'envoi, sans rien afficher ni enregistrer.

Le mot de passe est tapé ici, reste dans cette fenêtre, et n'est écrit nulle part.
    python3 scripts/tester-boite-mail.py
"""
import getpass
import smtplib
import sys

HOST = input("Serveur d'envoi [mail.netim.net] : ").strip() or "mail.netim.net"
PORT = int(input("Port [587] : ").strip() or "587")
USER = input("Identifiant [reply@nyuman.app] : ").strip() or "reply@nyuman.app"
PWD = getpass.getpass("Mot de passe (invisible) : ")

try:
    s = smtplib.SMTP_SSL(HOST, PORT, timeout=20) if PORT == 465 else smtplib.SMTP(HOST, PORT, timeout=20)
    if PORT != 465:
        s.starttls()
    s.login(USER, PWD)
    print("\n✓ La boîte accepte l'envoi. Le mot de passe est bon : reposez-le tel quel dans Railway.")
    s.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"\n✗ Refusé par le serveur : {e.smtp_code} {e.smtp_error.decode(errors='replace')[:100]}")
    print("  → le mot de passe ou l'identifiant n'est pas le bon.")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Impossible de joindre {HOST}:{PORT} — {type(e).__name__}")
    print("  → serveur ou port à vérifier auprès de Netim.")
    sys.exit(2)
