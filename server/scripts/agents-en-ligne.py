#!/usr/bin/env python3
"""Fait répondre les agents dans le HQ en ligne, depuis le Mac.

Le serveur en ligne n'a pas Claude : ce programme-ci surveille HQ à distance et, dès qu'un
humain écrit à un agent (message privé ou @mention), lance Claude sur le Mac au nom de cet
agent. L'agent répond ensuite dans HQ avec ses propres outils.

    python3 scripts/agents-en-ligne.py            # surveille https://teams.nyuman.app
    python3 scripts/agents-en-ligne.py <adresse>  # une autre adresse

Ne marche que tant que le Mac est allumé. Les clés des agents sont rangées dans server/.agents.json,
jamais affichées ni commitées.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HQ = (sys.argv[1] if len(sys.argv) > 1 else "https://teams.nyuman.app").rstrip("/")
os.environ.setdefault("HQ_HQ_URL", HQ)  # les agents écriront là

from app.config import settings  # noqa: E402  (après le réglage de HQ_HQ_URL)
from app.wake import TOKENS_FILE, AGENT_MODELS, DEFAULT_MODEL, claude_runner, system_prompt  # noqa: E402

settings.hq_url = HQ
EVERY_S = 12
HEAD = "mohamed"          # le responsable qui crée les clés des agents
SKIP = {"kwame"}          # Kwame répond depuis sa propre discussion


async def head_session(c: httpx.AsyncClient) -> None:
    r = await c.post(f"{HQ}/api/auth/dev-login", json={"member_id": HEAD})
    if r.status_code != 200:
        raise SystemExit("Impossible d'ouvrir une session responsable sur HQ "
                         f"({r.status_code}). La connexion par le nom est-elle active ?")


async def ensure_tokens(c: httpx.AsyncClient, agents: list[str]) -> dict:
    """Une clé par agent, créée par le responsable. Rangées localement, jamais affichées."""
    tokens = {}
    try:
        with open(TOKENS_FILE, encoding="utf-8") as f:
            tokens = json.load(f)
    except (OSError, ValueError):
        pass
    for a in agents:
        if tokens.get(a):
            continue
        r = await c.post(f"{HQ}/api/auth/agents/{a}/token")
        if r.status_code == 200:
            tokens[a] = r.json()["token"]
    with open(TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f)
    os.chmod(TOKENS_FILE, 0o600)
    return tokens


def agent_headers(agent: str, tokens: dict) -> dict:
    return {"X-HQ-Agent": agent, "Authorization": f"Bearer {tokens[agent]}"}


async def answer(agent: str, author: str, where: str, body: str) -> None:
    model = AGENT_MODELS.get(agent, DEFAULT_MODEL)
    prompt = (f"Vous êtes {agent}. Dans Nyuman HQ, {author} vient de vous écrire dans {where} :\n\n"
              f"« {body} »\n\n"
              "Répondez au même endroit avec vos outils hq_ (hq_ecrire pour un canal, "
              "hq_message_prive pour une discussion privée). Une seule réponse, courte et utile. "
              "Au besoin, lisez d'abord HQ (hq_lire, hq_activite, hq_projets, hq_taches).")
    print(f"  → {agent} réfléchit…", flush=True)
    res = await claude_runner(agent, model, prompt)
    if res.get("error"):
        print(f"  ✗ {agent} : {res['error'][:120]}", flush=True)
    else:
        print(f"  ✓ {agent} a répondu ({res.get('cost', 0):.3f} $)", flush=True)


async def main() -> None:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as c:
        await head_session(c)
        members = (await c.get(f"{HQ}/api/members")).json()
        agents = [m["id"] for m in members if m["kind"] == "agent" and m["id"] not in SKIP]
        noms = {m["id"]: m["name"] for m in members}
        humains = {m["id"] for m in members if m["kind"] == "human"}
        tokens = await ensure_tokens(c, agents)
        agents = [a for a in agents if a in tokens]
        if not agents:
            raise SystemExit("Aucune clé d'agent : vérifiez que vous êtes responsable sur ce HQ.")
        print(f"Agents en ligne sur {HQ} : {', '.join(noms[a] for a in agents)}.", flush=True)
        print(f"Je regarde toutes les {EVERY_S} s. Laissez cette fenêtre ouverte.", flush=True)
        vus: set[tuple[str, str]] = set()   # (agent, message) : chacun répond pour son compte
        premier_tour = True
        while True:
            for agent in agents:
                try:
                    h = agent_headers(agent, tokens)
                    r = await c.get(f"{HQ}/api/channels", headers=h)
                    chans = r.json() if r.status_code == 200 else []
                    if not isinstance(chans, list):
                        continue
                    for ch in chans:
                        if not (ch.get("unread") or ch.get("mentions")):
                            continue
                        r = await c.get(f"{HQ}/api/channels/{ch['id']}/messages?limit=5", headers=h)
                        msgs = r.json() if r.status_code == 200 else []
                        if not isinstance(msgs, list):
                            continue
                        await c.post(f"{HQ}/api/channels/{ch['id']}/read", headers=h)
                        if premier_tour:
                            continue
                        # On ne réveille un agent que si on s'adresse vraiment à lui :
                        # une discussion privée, ou son nom cité. Pas tout ce qui passe dans un canal.
                        for m in msgs:
                            if m["author_id"] not in humains or (agent, m["id"]) in vus:
                                continue
                            cite = f"<@{agent}>" in (m.get("body") or "")
                            if ch["kind"] != "dm" and not cite:
                                continue
                            vus.add((agent, m["id"]))
                            where = f"le canal #{ch['name']}" if ch["kind"] == "channel" else "votre discussion privée"
                            print(f"{noms.get(m['author_id'], '?')} → {noms[agent]} : {m['body'][:70]}", flush=True)
                            await answer(agent, noms.get(m["author_id"], "quelqu'un"), where, m["body"])
                except Exception as e:
                    print(f"  ({noms.get(agent, agent)} : {type(e).__name__}, on continue)", flush=True)
            premier_tour = False
            await asyncio.sleep(EVERY_S)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSurveillance arrêtée : les agents ne répondront plus en ligne.")
