"""
SQLite persistence layer for the GW2 Squad Builder.

Single-purpose module — owns the DB path resolution, schema, and CRUD. The
streamlit app talks to this module via load_all / upsert / delete and never
touches sqlite3 directly.

DB path:
- $GW2_SETUP_PLANER_DB env var if set
- /var/lib/gw2-setup-planer/db.sqlite3 if /var/lib is writable (e.g. systemd
  service deployment)
- otherwise ~/.local/share/gw2-setup-planer/db.sqlite3
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from models import Player, Profession, Role, Specialization, Tag

_ENV_VAR = "GW2_SETUP_PLANER_DB"


def _default_db_path() -> Path:
    sysd = Path("/var/lib/gw2-setup-planer")
    try:
        sysd.mkdir(parents=True, exist_ok=True)
        if os.access(sysd, os.W_OK):
            return sysd / "db.sqlite3"
    except OSError:
        pass
    userd = Path.home() / ".local/share/gw2-setup-planer"
    userd.mkdir(parents=True, exist_ok=True)
    return userd / "db.sqlite3"


def db_path() -> Path:
    env = os.environ.get(_ENV_VAR)
    return Path(env).expanduser() if env else _default_db_path()


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
    try:
        c.execute("PRAGMA foreign_keys = ON;")
        yield c
        c.commit()
    finally:
        c.close()


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS roles (
    name           TEXT PRIMARY KEY,
    profession     TEXT NOT NULL,
    specialization TEXT NOT NULL,
    tags_json      TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS players (
    name                 TEXT PRIMARY KEY,
    role_priorities_json TEXT NOT NULL DEFAULT '[]'
);
"""


def init_db(
    default_roles: dict[str, Role] | None = None,
    default_players: dict[str, Player] | None = None,
) -> None:
    """Create schema if missing. Seed default roles/players only if the
    respective table is empty (so a wipe-the-DB reset path stays usable)."""
    with _conn() as c:
        c.executescript(_SCHEMA_SQL)
        if default_roles is not None:
            (n_roles,) = c.execute("SELECT COUNT(*) FROM roles").fetchone()
            if n_roles == 0:
                for role in default_roles.values():
                    _write_role(c, role)
        if default_players is not None:
            (n_players,) = c.execute("SELECT COUNT(*) FROM players").fetchone()
            if n_players == 0:
                for player in default_players.values():
                    _write_player(c, player)


def _row_to_role(row: tuple) -> Role:
    name, prof, spec, tags_json = row
    return Role(
        name=name,
        profession=Profession(prof),
        specialization=Specialization(spec),
        tags=[Tag(t) for t in json.loads(tags_json)],
    )


def _row_to_player(row: tuple) -> Player:
    name, prio_json = row
    return Player(name=name, role_priorities=list(json.loads(prio_json)))


def load_all() -> tuple[dict[str, Role], dict[str, Player]]:
    """Snapshot of everything in the DB. Called once at app start."""
    with _conn() as c:
        roles = {}
        for row in c.execute(
            "SELECT name, profession, specialization, tags_json FROM roles"
        ):
            try:
                role = _row_to_role(row)
            except (ValueError, KeyError):
                # Skip rows with bad/renamed enums rather than crashing.
                continue
            roles[role.name] = role
        players = {}
        for row in c.execute("SELECT name, role_priorities_json FROM players"):
            try:
                player = _row_to_player(row)
            except (ValueError, KeyError):
                continue
            players[player.name] = player
    return roles, players


def _write_role(c: sqlite3.Connection, role: Role) -> None:
    c.execute(
        "INSERT INTO roles (name, profession, specialization, tags_json) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(name) DO UPDATE SET "
        "profession=excluded.profession, "
        "specialization=excluded.specialization, "
        "tags_json=excluded.tags_json",
        (
            role.name,
            role.profession.value,
            role.specialization.value,
            json.dumps([t.value for t in role.tags]),
        ),
    )


def _write_player(c: sqlite3.Connection, player: Player) -> None:
    c.execute(
        "INSERT INTO players (name, role_priorities_json) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET "
        "role_priorities_json=excluded.role_priorities_json",
        (player.name, json.dumps(list(player.role_priorities))),
    )


def upsert_role(role: Role) -> None:
    with _conn() as c:
        _write_role(c, role)


def delete_role(name: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM roles WHERE name = ?", (name,))


def rename_role(old: str, new: str) -> None:
    """Atomic rename: update the role row's primary key AND rewrite the
    role_priorities_json blob of every player that references `old`."""
    if old == new:
        return
    with _conn() as c:
        # Pull every player that references the old role name (string match).
        rows = c.execute(
            "SELECT name, role_priorities_json FROM players "
            "WHERE role_priorities_json LIKE ?",
            (f'%"{old}"%',),
        ).fetchall()
        c.execute("UPDATE roles SET name = ? WHERE name = ?", (new, old))
        for pname, prio_json in rows:
            prios = json.loads(prio_json)
            updated = [new if p == old else p for p in prios]
            if updated != prios:
                c.execute(
                    "UPDATE players SET role_priorities_json = ? WHERE name = ?",
                    (json.dumps(updated), pname),
                )


def upsert_player(player: Player) -> None:
    with _conn() as c:
        _write_player(c, player)


def delete_player(name: str) -> None:
    with _conn() as c:
        c.execute("DELETE FROM players WHERE name = ?", (name,))


def rename_player(old: str, new: str) -> None:
    if old == new:
        return
    with _conn() as c:
        c.execute("UPDATE players SET name = ? WHERE name = ?", (new, old))
