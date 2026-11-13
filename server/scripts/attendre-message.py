#!/usr/bin/env python3
"""Attend un nouveau message HQ pour un agent, puis s'arrête en l'affichant.

Sert aux agents dont la discussion Claude est ouverte (HQ_AGENT_WAKE_SKIP) : la discussion
lance ce guetteur en fond, et l'app la prévient dès qu'il s'arrête. Elle répond alors
elle-même dans HQ, avec tout le contexte de son travail en cours.

    python3 scripts/attendre-message.py kwame [minutes]
"""
import os
import subprocess
import sys
import time

AGENT = sys.argv[1] if len(sys.argv) > 1 else "kwame"
MINUTES = float(sys.argv[2]) if len(sys.argv) > 2 else 240
DB = os.environ.get("HQ_DB_NAME", "nyuman_hq")
EVERY_S = 15

# Messages d'un humain, adressés à l'agent : dans une discussion privée dont il fait partie,
# ou dans un canal où il est mentionné.
SQL = """
select m.created_at, mem.name, c.kind, coalesce(c.name, 'message privé'), left(m.body, 600)
from messages m
  join members mem on mem.id = m.author_id
  join channels c on c.id = m.channel_id
where m.created_at > %(since)s
  and m.deleted = false
  and mem.kind = 'human'
  and (
    exists (select 1 from channel_members cm
            where cm.channel_id = m.channel_id and cm.member_id = %(agent)s and c.kind = 'dm')
    or exists (select 1 from mentions x where x.message_id = m.id and x.member_id = %(agent)s)
  )
order by m.created_at
limit 5
"""


def query(since: str) -> str:
    sql = SQL.replace("%(since)s", f"'{since}'").replace("%(agent)s", f"'{AGENT}'")
    out = subprocess.run(["psql", "-d", DB, "-At", "-F", " · ", "-c", sql],
                         capture_output=True, text=True, timeout=20)
    if out.returncode != 0:
        print("guetteur : la base ne répond pas —", out.stderr.strip()[:200], flush=True)
        return ""
    return out.stdout.strip()


def main() -> int:
    since = subprocess.run(["psql", "-d", DB, "-Atc", "select now()"], capture_output=True, text=True).stdout.strip()
    if not since:
        print("guetteur : impossible de lire l'heure de la base.", flush=True)
        return 2
    print(f"Guetteur HQ pour {AGENT} : j'attends un message depuis {since}.", flush=True)
    stop = time.time() + MINUTES * 60
    while time.time() < stop:
        time.sleep(EVERY_S)
        found = query(since)
        if found:
            print("\nNouveau message dans HQ :\n" + found, flush=True)
            return 0
    print("Guetteur arrêté : rien reçu dans le temps imparti.", flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
