"""Réveil des agents.

Quand un humain écrit en privé à un agent, ou le mentionne avec @, HQ lance l'agent en arrière-plan
(Claude en mode non interactif, avec le connecteur HQ à son nom). L'agent lit le message et répond dans HQ.

Garde-fous : seuls les messages des humains réveillent un agent (pas de ping-pong entre agents),
un réveil à la fois par agent (les messages arrivés entre-temps sont traités au tour suivant),
un plafond de réveils par jour et par agent, un budget et une durée maximum par réveil,
et l'agent n'a que les outils de HQ (pas de commandes, pas d'écriture de fichiers, rien vers l'extérieur).
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List, Optional, Set

from sqlalchemy import func, select

from app.config import settings
from app.db import SessionLocal
from app.domain.models import AgentRun, Channel, ChannelMember, Member, Message
from app.realtime import hub, now

MCP_SERVER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "mcp", "server.mjs"))
# Choix de Mohamed (13/11) : Opus 4.6 effort low pour tous, Sonnet 5.5 pour Mariam.
AGENT_MODELS = {"mariam": "claude-sonnet-5-5"}
DEFAULT_MODEL = "claude-opus-4-6"
MENTION = "<@{}>"

Runner = Callable[[str, str, str], Awaitable[dict]]


def decode(body: str, names: Dict[str, str]) -> str:
    import re

    return re.sub(r"<@([a-z0-9_-]+)>", lambda m: "@" + names.get(m.group(1), m.group(1)), body)


async def build_prompt(agent: Member, trigger: Message, channel: Channel, author: Member, extra: int) -> str:
    async with SessionLocal() as s:
        names = {m.id: m.name for m in (await s.scalars(select(Member))).all()}
    where = f"le canal #{channel.name}" if channel.kind == "channel" else "votre discussion privée"
    thread = f" (dans le fil du message {trigger.parent_id})" if trigger.parent_id else ""
    more = f"\nD'autres messages vous concernent peut-être depuis (environ {extra}) : regardez hq_activite." if extra else ""
    return f"""Vous êtes {agent.name}, {agent.title} chez Nyuman (app de réservation beauté à Abidjan). Vous êtes un agent IA, membre de l'équipe à part entière, dans Nyuman HQ, le QG interne.
Votre rôle : {agent.role}

{author.name} ({author.title}) vient de vous écrire dans {where}{thread} :
« {decode(trigger.body, names)} »
(identifiant du canal : {channel.id} ; identifiant du message : {trigger.id}){more}

Ce que vous devez faire maintenant :
1. Si besoin, lisez le contexte avec les outils HQ (hq_lire avec l'identifiant du canal, hq_lire_fil, hq_activite, hq_taches, hq_lire_page…).
2. Répondez dans HQ, au même endroit : hq_ecrire avec canal = {channel.id}{f' et fil_id = {trigger.parent_id}' if trigger.parent_id else ''}. Une seule réponse, sauf si on vous demande plusieurs choses.
3. Si on vous confie une tâche, vous pouvez la créer ou la mettre à jour (hq_creer_tache, hq_maj_tache) et mettre votre statut (hq_statut).
"""


MEMORY_DIR = os.path.expanduser("~/.claude/projects/-Users-melyohthesun-Documents-nyuman-app/memory")

RULES = """Vous êtes un agent IA de l'équipe Nyuman (app de réservation beauté à Abidjan, lancement public le 12/12/2026), membre à part entière de Nyuman HQ, le QG interne où humains et agents travaillent ensemble.

Règles de l'équipe :
- Français simple, phrases courtes, vouvoiement (en particulier avec Mohamed, le fondateur). Donnez une recommandation quand on vous pose une question.
- Restez dans votre rôle. Si la demande sort de votre périmètre, dites-le et proposez qui peut s'en charger (avec @Prénom).
- Vous n'agissez que dans HQ, avec les outils hq_… : rien vers l'extérieur (pas d'e-mail, pas de publication, pas d'argent, pas de code).
- Vous ne vous faites jamais passer pour un humain. Vous n'inventez pas de chiffres : si vous ne savez pas, dites-le.
- Répondez une seule fois, au bon endroit (même canal, même fil). Soyez bref.

Mémoire partagée de l'équipe : l'index est ci-dessous. Pour le détail d'une décision, lisez le fichier avec l'outil Read (ex. Read fees-and-refund-decisions.md).
"""


def system_prompt() -> str:
    try:
        with open(os.path.join(MEMORY_DIR, "MEMORY.md"), encoding="utf-8") as f:
            index = f.read()
    except OSError:
        index = "(mémoire indisponible)"
    return RULES + "\n" + index


async def claude_runner(agent_id: str, model: str, prompt: str) -> dict:
    """Lance Claude en arrière-plan avec le connecteur HQ au nom de l'agent. Renvoie {cost, error}."""
    claude = shutil.which(settings.claude_bin) or settings.claude_bin
    node = shutil.which("node") or "node"
    mcp = {"mcpServers": {"nyuman-hq": {"command": node, "args": [MCP_SERVER],
                                       "env": {"HQ_AGENT": agent_id, "HQ_URL": "http://127.0.0.1:8030"}}}}
    # Prompt système court et identique pour tous (mis en cache) : seulement les outils HQ + la lecture de la mémoire.
    args = [claude, "-p", prompt, "--model", model, "--effort", "low", "--output-format", "json",
            "--system-prompt", system_prompt(), "--tools", "Read",
            "--mcp-config", json.dumps(mcp), "--strict-mcp-config",
            "--allowedTools", "mcp__nyuman-hq__*", "Read",
            "--max-budget-usd", str(settings.agent_max_budget_usd)]
    cwd = settings.agent_workdir or MEMORY_DIR
    proc = await asyncio.create_subprocess_exec(*args, cwd=cwd if os.path.isdir(cwd) else None,
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                                                stdin=asyncio.subprocess.DEVNULL)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=settings.agent_run_timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        return {"cost": 0.0, "error": "trop long : arrêté"}
    try:
        data = json.loads(out.decode() or "{}")
    except ValueError:
        return {"cost": 0.0, "error": (err.decode() or out.decode())[-500:]}
    return {"cost": float(data.get("total_cost_usd") or 0), "error": data.get("result", "")[:500] if data.get("is_error") else ""}


class Waker:
    def __init__(self) -> None:
        self.runner: Runner = claude_runner
        self.pending: Dict[str, List[str]] = {}  # agent -> messages en attente
        self.busy: Set[str] = set()
        self.capped_notice: Dict[str, str] = {}  # agent -> jour où l'on a prévenu du plafond
        self.tasks: Set[asyncio.Task] = set()

    @property
    def enabled(self) -> bool:
        return settings.agent_wake

    async def on_message(self, msg: Message, channel: Channel, author: Member, mentioned: Set[str],
                         force: bool = False) -> List[str]:
        """Appelé après chaque nouveau message. Renvoie les agents réveillés (ou mis en attente).
        force : réveil voulu par HQ lui-même (avis de Koffi sur une proposition), même si l'auteur est un agent."""
        if (author.kind != "human" and not force) or not self.enabled:
            return []
        targets = {m for m in mentioned if m in hub.agents}
        if channel.kind == "dm":
            async with SessionLocal() as s:
                ids = (await s.scalars(select(ChannelMember.member_id).where(ChannelMember.channel_id == channel.id))).all()
            targets |= {m for m in ids if m in hub.agents}
        targets.discard(author.id)
        # Un agent dont la discussion Claude est ouverte lit lui-même HQ : pas de copie lancée.
        targets -= {a.strip() for a in settings.agent_wake_skip.split(",") if a.strip()}
        for agent in targets:
            self.pending.setdefault(agent, []).append(msg.id)
            if agent not in self.busy:
                self.busy.add(agent)
                t = asyncio.create_task(self._work(agent))
                self.tasks.add(t)
                t.add_done_callback(self.tasks.discard)
        return sorted(targets)

    async def runs_today(self, agent: str) -> int:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        async with SessionLocal() as s:
            return await s.scalar(select(func.count()).select_from(AgentRun).where(
                AgentRun.agent_id == agent, AgentRun.created_at >= start, AgentRun.status.in_(["running", "done"]))) or 0

    async def _work(self, agent: str) -> None:
        try:
            while self.pending.get(agent):
                batch, self.pending[agent] = self.pending[agent], []
                await self._run_once(agent, batch)
        finally:
            self.busy.discard(agent)
            self.pending.pop(agent, None)

    async def _run_once(self, agent_id: str, batch: List[str]) -> None:
        async with SessionLocal() as s:
            agent = await s.get(Member, agent_id)
            trigger = await s.get(Message, batch[-1])
            channel = await s.get(Channel, trigger.channel_id)
            author = await s.get(Member, trigger.author_id)
            run = AgentRun(agent_id=agent_id, trigger_message_id=trigger.id, channel_id=channel.id,
                           triggered_by=author.id, model=AGENT_MODELS.get(agent_id, DEFAULT_MODEL), created_at=now())
            s.add(run)
            if await self.runs_today(agent_id) >= settings.agent_daily_cap:
                run.status = "capped"
                await s.commit()
                await self._cap_notice(agent, channel, trigger)
                return
            run.status = "running"
            await s.commit()
            run_id = run.id
        audience = None if channel.kind == "channel" else set((await self._members(channel.id)))
        hub.touch(agent_id)
        typing = asyncio.create_task(self._typing(agent_id, channel.id, trigger.parent_id, audience))
        started = time.monotonic()
        try:
            prompt = await build_prompt(agent, trigger, channel, author, len(batch) - 1)
            result = await self.runner(agent_id, run.model, prompt)
        except Exception as e:  # le réveil ne doit jamais faire tomber HQ
            result = {"cost": 0.0, "error": str(e)[:500]}
        finally:
            typing.cancel()
        async with SessionLocal() as s:
            run = await s.get(AgentRun, run_id)
            run.status = "failed" if result.get("error") else "done"
            run.cost_usd, run.error = result.get("cost", 0.0), result.get("error", "")
            run.duration_s = round(time.monotonic() - started, 1)
            await s.commit()
        await hub.broadcast({"type": "agent.run", "agent_id": agent_id, "status": run.status})

    async def _members(self, channel_id: str) -> List[str]:
        async with SessionLocal() as s:
            return list((await s.scalars(select(ChannelMember.member_id).where(ChannelMember.channel_id == channel_id))).all())

    async def _typing(self, agent_id: str, channel_id: str, parent_id: Optional[str], audience) -> None:
        while True:
            await hub.broadcast({"type": "typing", "channel_id": channel_id, "member_id": agent_id, "parent_id": parent_id},
                                to=audience, exclude=agent_id)
            await asyncio.sleep(3)

    async def _cap_notice(self, agent: Member, channel: Channel, trigger: Message) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        if self.capped_notice.get(agent.id) == today:
            return
        self.capped_notice[agent.id] = today
        from app.api.chat import emit_message, set_read

        async with SessionLocal() as s:
            msg = Message(channel_id=channel.id, author_id=agent.id, parent_id=trigger.parent_id, created_at=now(),
                          body=f"J'ai atteint ma limite de {settings.agent_daily_cap} réveils pour aujourd'hui. "
                               "Je lirai votre message demain, ou relancez-moi depuis ma discussion Claude si c'est urgent.")
            s.add(msg)
            await s.flush()
            await set_read(s, channel.id, agent.id, msg.created_at)
            await s.commit()
            await emit_message(s, channel, msg, "message.new")


waker = Waker()
