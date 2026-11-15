#!/usr/bin/env python3
"""Attend qu'un humain écrive à un agent dans le HQ en ligne, puis s'arrête en l'affichant.

Sert à la discussion Claude d'un agent (Kwame) : l'app la prévient quand ce programme s'arrête,
et l'agent répond lui-même dans HQ avec tout le contexte de son travail en cours.

    python3 scripts/attendre-message-en-ligne.py kwame [minutes] [adresse]
"""
import asyncio
import json
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.wake import TOKENS_FILE  # noqa: E402

AGENT = sys.argv[1] if len(sys.argv) > 1 else "kwame"
MINUTES = float(sys.argv[2]) if len(sys.argv) > 2 else 720
HQ = (sys.argv[3] if len(sys.argv) > 3 else "https://teams.nyuman.app").rstrip("/")
EVERY_S = 15
HEAD = "mohamed"


async def token_for(c: httpx.AsyncClient, agent: str) -> str:
    """Une clé pour lire HQ au nom de l'agent. Rangée localement, jamais affichée."""
    tokens = {}
    try:
        with open(TOKENS_FILE, encoding="utf-8") as f:
            tokens = json.load(f)
    except (OSError, ValueError):
        pass
    if not tokens.get(agent):
        r = await c.post(f"{HQ}/api/auth/dev-login", json={"member_id": HEAD})
        if r.status_code != 200:
            raise SystemExit("Impossible d'ouvrir une session responsable sur HQ.")
        r = await c.post(f"{HQ}/api/auth/agents/{agent}/token")
        if r.status_code != 200:
            raise SystemExit(f"Impossible de créer la clé de {agent} ({r.status_code}).")
        tokens[agent] = r.json()["token"]
        with open(TOKENS_FILE, "w", encoding="utf-8") as f:
            json.dump(tokens, f)
        os.chmod(TOKENS_FILE, 0o600)
    return tokens[agent]


async def main() -> int:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        jeton = await token_for(c, AGENT)
        h = {"X-HQ-Agent": AGENT, "Authorization": f"Bearer {jeton}"}
        noms = {m["id"]: m["name"] for m in (await c.get(f"{HQ}/api/members", headers=h)).json()}
        humains = {m["id"] for m in (await c.get(f"{HQ}/api/members", headers=h)).json() if m["kind"] == "human"}
        # Premier tour : on marque tout comme lu, on n'attend que la suite.
        for ch in (await c.get(f"{HQ}/api/channels", headers=h)).json():
            await c.post(f"{HQ}/api/channels/{ch['id']}/read", headers=h)
        print(f"Guetteur HQ en ligne pour {noms.get(AGENT, AGENT)} sur {HQ}.", flush=True)
        fin = asyncio.get_event_loop().time() + MINUTES * 60
        while asyncio.get_event_loop().time() < fin:
            await asyncio.sleep(EVERY_S)
            try:
                for ch in (await c.get(f"{HQ}/api/channels", headers=h)).json():
                    if not (ch.get("unread") or ch.get("mentions")):
                        continue
                    msgs = (await c.get(f"{HQ}/api/channels/{ch['id']}/messages?limit=5", headers=h)).json()
                    await c.post(f"{HQ}/api/channels/{ch['id']}/read", headers=h)
                    dits = [m for m in msgs if m["author_id"] in humains]
                    if not dits:
                        continue
                    m = dits[-1]
                    ou = f"#{ch['name']}" if ch["kind"] == "channel" else "message privé"
                    print(f"\nNouveau message dans HQ ({ou}) de {noms.get(m['author_id'], '?')} :\n{m['body'][:600]}",
                          flush=True)
                    return 0
            except Exception as e:
                print(f"(guetteur : {type(e).__name__}, il continue)", flush=True)
        print("Guetteur arrêté : rien reçu dans le temps imparti.", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
