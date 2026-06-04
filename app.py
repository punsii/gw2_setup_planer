"""
GW2 Squad Builder — Streamlit prototype with Setup/Roles/Players tabs.

Run with:
    streamlit run app.py
"""

import base64
from copy import deepcopy
from pathlib import Path

import streamlit as st

import storage
from models import PROFESSION_TO_SPECS as _MODELS_PROFESSION_TO_SPECS
from models import Player, Role

# ==================== DATA ====================

TAG_OPTIONS: list[str] = [
    "Stability",
    "Heal",
    "Boons",
    "Cleanse",
    "DPS",
    "Strips",
    "Smoke",
]

# String-typed view onto models.PROFESSION_TO_SPECS so the UI code keeps using
# raw strings everywhere (selectbox options, dict lookups, session_state)
# while models.py stays the enum-typed source of truth.
PROFESSION_TO_SPECS: dict[str, list[str]] = {
    prof.value: [spec.value for spec in specs]
    for prof, specs in _MODELS_PROFESSION_TO_SPECS.items()
}

PROFESSIONS: list[str] = list(PROFESSION_TO_SPECS.keys())


# Default roles. User edits/adds/removes these at runtime via the Roles tab.
DEFAULT_ROLES: dict[str, dict] = {
    "HFB": {
        "profession": "Guardian",
        "specialization": "Firebrand",
        "tags": ["Stability", "Boons", "Cleanse"],
    },
    "Dragonhunter": {
        "profession": "Guardian",
        "specialization": "Dragonhunter",
        "tags": ["DPS"],
    },
    "Willbender": {
        "profession": "Guardian",
        "specialization": "Willbender",
        "tags": ["DPS"],
    },
    "Support Luminary": {
        "profession": "Guardian",
        "specialization": "Luminary",
        "tags": ["Stability", "Cleanse"],
    },
    "DPS Luminary": {
        "profession": "Guardian",
        "specialization": "Luminary",
        "tags": ["DPS"],
    },
    "Druid": {
        "profession": "Ranger",
        "specialization": "Druid",
        "tags": ["Heal", "Cleanse", "Smoke"],
    },
    "Soulbeast": {
        "profession": "Ranger",
        "specialization": "Soulbeast",
        "tags": ["DPS", "Smoke"],
    },
    "Untamed": {
        "profession": "Ranger",
        "specialization": "Untamed",
        "tags": ["DPS", "Strips", "Smoke"],
    },
    "Heal Scrapper": {
        "profession": "Engineer",
        "specialization": "Scrapper",
        "tags": ["Heal", "Cleanse", "Smoke"],
    },
    "DPS Scrapper": {
        "profession": "Engineer",
        "specialization": "Scrapper",
        "tags": ["DPS", "Smoke"],
    },
    "Holosmith": {
        "profession": "Engineer",
        "specialization": "Holosmith",
        "tags": ["DPS", "Smoke"],
    },
    "Amalgam": {
        "profession": "Engineer",
        "specialization": "Amalgam",
        "tags": ["DPS", "Smoke"],
    },
    "Core Necro": {
        "profession": "Necromancer",
        "specialization": "Necromancer",
        "tags": ["DPS", "Strips"],
    },
    "Reaper": {
        "profession": "Necromancer",
        "specialization": "Reaper",
        "tags": ["DPS", "Strips"],
    },
    "Support Scourge": {
        "profession": "Necromancer",
        "specialization": "Scourge",
        "tags": ["Heal", "Strips"],
    },
    "Support Harbinger": {
        "profession": "Necromancer",
        "specialization": "Harbinger",
        "tags": ["Boons", "Strips"],
    },
    "Ritualist": {
        "profession": "Necromancer",
        "specialization": "Ritualist",
        "tags": ["DPS", "Strips"],
    },
    "Spellbreaker": {
        "profession": "Warrior",
        "specialization": "Spellbreaker",
        "tags": ["DPS", "Strips"],
    },
    "Paragon": {
        "profession": "Warrior",
        "specialization": "Paragon",
        "tags": ["Heal", "Boons"],
    },
    "Troubadour": {
        "profession": "Mesmer",
        "specialization": "Troubadour",
        "tags": ["Stability", "Heal", "Boons"],
    },
    "Virtuoso": {"profession": "Mesmer", "specialization": "Virtuoso", "tags": ["DPS"]},
    "Support Chrono": {
        "profession": "Mesmer",
        "specialization": "Chronomancer",
        "tags": ["Stability", "Heal", "Boons", "Strips"],
    },
    "DPS Ele": {
        "profession": "Elementalist",
        "specialization": "Elementalist",
        "tags": ["DPS"],
    },
    "Support Tempest": {
        "profession": "Elementalist",
        "specialization": "Tempest",
        "tags": ["Heal", "Cleanse"],
    },
    "Support Catalyst": {
        "profession": "Elementalist",
        "specialization": "Catalyst",
        "tags": ["Cleanse", "Boons"],
    },
    "Revenant": {
        "profession": "Revenant",
        "specialization": "Revenant",
        "tags": ["DPS"],
    },
    "Daredevil": {
        "profession": "Thief",
        "specialization": "Daredevil",
        "tags": ["DPS", "Smoke"],
    },
    "Specter": {
        "profession": "Thief",
        "specialization": "Specter",
        "tags": ["Heal", "Boons", "Smoke"],
    },
}


# Default players. Ordered list of role names; index = priority (0 = primary).
DEFAULT_PLAYERS: dict[str, list[str]] = {
    "Alex": [
        "Core Necro",
        "Reaper",
        "Support Scourge",
        "Support Harbinger",
        "DPS Scrapper",
        "Heal Scrapper",
        "Holosmith",
        "Amalgam",
        "Revenant",
        "Virtuoso",
        "Daredevil",
        "Ritualist",
        "Untamed",
        "Spellbreaker",
        "Druid",
    ],
    "Caradea": [
        "Revenant",
        "Untamed",
        "Willbender",
        "Holosmith",
        "Virtuoso",
        "Reaper",
        "Core Necro",
        "Support Scourge",
        "Support Chrono",
        "Support Luminary",
        "Druid",
    ],
    "Colmyllo Blanco": [
        "HFB",
        "Dragonhunter",
        "Support Luminary",
        "Virtuoso",
        "Support Chrono",
        "Druid",
        "Heal Scrapper",
    ],
    "daRetzaa": ["Spellbreaker", "Paragon", "Untamed", "Druid", "Soulbeast"],
    "Disturbed": [
        "Druid",
        "Heal Scrapper",
        "Specter",
        "Troubadour",
        "Support Chrono",
        "Support Tempest",
        "Support Catalyst",
        "Daredevil",
        "Paragon",
        "Support Scourge",
    ],
    "Esskape": [
        "Druid",
        "Troubadour",
        "Heal Scrapper",
        "Specter",
        "Paragon",
        "Support Harbinger",
        "Support Chrono",
        "Support Catalyst",
        "Support Tempest",
    ],
    "kfc": ["HFB", "Spellbreaker"],
    "Krataxx": [
        "Druid",
        "Paragon",
        "Spellbreaker",
        "Support Tempest",
        "Heal Scrapper",
        "Troubadour",
    ],
    "Lullu": ["Druid"],
    "Melow": ["Amalgam", "Heal Scrapper", "Paragon", "Druid"],
    "MonkeyDLuis": [
        "Amalgam",
        "Core Necro",
        "DPS Ele",
        "DPS Luminary",
        "DPS Scrapper",
        "Daredevil",
        "Dragonhunter",
        "Druid",
        "HFB",
        "Heal Scrapper",
        "Holosmith",
        "Paragon",
        "Reaper",
        "Revenant",
        "Ritualist",
        "Soulbeast",
        "Specter",
        "Spellbreaker",
        "Support Catalyst",
        "Support Chrono",
        "Support Harbinger",
        "Support Luminary",
        "Support Scourge",
        "Support Tempest",
        "Troubadour",
        "Untamed",
        "Virtuoso",
        "Willbender",
    ],
    "NappoLeo": ["Paragon"],
    "Punsi": ["DPS Ele", "Support Tempest", "Support Catalyst", "Paragon"],
    "Semtäx": [
        "Troubadour",
        "Reaper",
        "Ritualist",
        "Amalgam",
        "Holosmith",
        "Untamed",
        "DPS Ele",
        "Virtuoso",
        "Spellbreaker",
        "Dragonhunter",
        "Willbender",
        "DPS Luminary",
        "Soulbeast",
        "Daredevil",
        "DPS Scrapper",
        "Core Necro",
        "Revenant",
    ],
    "Fabz": ["Willbender"],
    "Xeonix": [
        "HFB",
        "Support Luminary",
        "DPS Luminary",
        "Reaper",
        "Support Scourge",
        "Core Necro",
        "Support Harbinger",
        "Ritualist",
        "Druid",
        "Paragon",
        "Troubadour",
        "Amalgam",
        "Holosmith",
        "DPS Scrapper",
        "Heal Scrapper",
        "Untamed",
        "Soulbeast",
        "DPS Ele",
        "Support Tempest",
        "Support Catalyst",
        "Virtuoso",
        "Support Chrono",
        "Revenant",
        "Spellbreaker",
        "Dragonhunter",
        "Willbender",
        "Daredevil",
        "Specter",
    ],
    "Sif": [
        "DPS Luminary",
        "Reaper",
        "Support Scourge",
        "Core Necro",
        "Support Harbinger",
        "Ritualist",
        "Druid",
        "Paragon",
        "Troubadour",
        "Amalgam",
        "Holosmith",
        "DPS Scrapper",
        "Heal Scrapper",
        "Untamed",
        "Soulbeast",
        "DPS Ele",
        "Support Tempest",
        "Support Catalyst",
        "Virtuoso",
        "Support Chrono",
        "Revenant",
        "Spellbreaker",
        "Dragonhunter",
        "Willbender",
        "Daredevil",
        "Specter",
    ],
    "Suushi": [
        "Heal Scrapper",
        "Druid",
        "Support Harbinger",
        "Paragon",
        "Amalgam",
        "Holosmith",
        "Reaper",
        "Core Necro",
        "Support Scourge",
        "DPS Scrapper",
    ],
    "Tim": [
        "DPS Ele",
        "Amalgam",
        "Holosmith",
        "DPS Scrapper",
        "Reaper",
        "Core Necro",
        "Ritualist",
        "Untamed",
        "Virtuoso",
        "Spellbreaker",
        "Dragonhunter",
        "Willbender",
        "Soulbeast",
        "Daredevil",
    ],
    "Viv": [
        "HFB",
        "Support Luminary",
        "Paragon",
        "Druid",
        "Support Tempest",
        "Untamed",
        "DPS Luminary",
    ],
}


# Initial setup loaded on first session start: ordered grid of (role, player)
# tuples. Outer list = groups (rows); inner list = spots within a group.
DEFAULT_SETUP: list[list[tuple[str, str]]] = [
    [
        ("HFB", "Xeonix"),
        ("Troubadour", "Esskape"),
        ("Paragon", "Melow"),
        ("Virtuoso", "Alex"),
        ("Virtuoso", "Semtäx"),
    ],
    [
        ("HFB", "Colmyllo Blanco"),
        ("Specter", "Disturbed"),
        ("Support Catalyst", "Punsi"),
        ("Spellbreaker", "Sif"),
        ("Willbender", "Fabz"),
    ],
    [
        ("HFB", "Viv"),
        ("Druid", "Lullu"),
        ("Support Harbinger", "Suushi"),
        ("Spellbreaker", "MonkeyDLuis"),
        ("Untamed", "Caradea"),
    ],
]


ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"


# ==================== HELPERS ====================

NUM_COLS = 5
MAX_GROUPS = 10

# Default tag preselected in the role-picker dialog, per spot column.
# Index = column 0..NUM_COLS-1. Falls back to "All" if out of range.
COL_DEFAULT_TAGS: list[str] = ["Stability", "Heal", "Boons", "DPS", "DPS"]


def _icon_path_for_spec(spec: str) -> Path | None:
    if not spec:
        return None
    return ICON_DIR / f"{spec.capitalize()}_icon_small.png"


def _icon_path_for_role(role_name: str) -> Path | None:
    role = st.session_state.roles.get(role_name)
    if not role:
        return None
    return _icon_path_for_spec(role["specialization"])


@st.cache_data
def _spec_data_url(spec: str) -> str:
    """Base64 data URL for inline-HTML rendering."""
    p = _icon_path_for_spec(spec)
    if p is None or not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


def _role_data_url(role_name: str) -> str:
    role = st.session_state.roles.get(role_name)
    if not role:
        return ""
    return _spec_data_url(role["specialization"])


def _discord_emoji_for_role(role_name: str) -> str:
    role = st.session_state.roles.get(role_name)
    if not role:
        return ""
    prof = role["profession"].lower()
    spec = role["specialization"].lower()
    if prof == spec:
        return f":{prof}_core:"
    return f":{prof}_{spec}:"


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _num_groups() -> int:
    return st.session_state.get("num_groups", 3)


def _role_key(r: int, c: int) -> str:
    return f"role_{r}_{c}"


def _player_key(r: int, c: int) -> str:
    return f"player_{r}_{c}"


def _picked_players_except(my_spot: tuple[int, int]) -> set[str]:
    picked: set[str] = set()
    for r in range(_num_groups()):
        for c in range(NUM_COLS):
            if (r, c) == my_spot:
                continue
            v = st.session_state.get(_player_key(r, c))
            if v:
                picked.add(v)
    return picked


def candidates_for(role_name: str, my_spot: tuple[int, int]) -> list[str]:
    """Players who have role_name, sorted by (position in their list, total roles, name)."""
    taken = _picked_players_except(my_spot)
    rows: list[tuple[int, int, str]] = []
    for player, roles in st.session_state.players.items():
        if role_name not in roles or player in taken:
            continue
        rows.append((roles.index(role_name), len(roles), player))
    rows.sort()
    return [name for _, _, name in rows]


def _role_sort_key(role_name: str) -> tuple[int, int, str]:
    """Sort roles by (profession order, spec order, role name)."""
    role = st.session_state.roles.get(role_name, {})
    prof = role.get("profession", "")
    spec = role.get("specialization", "")
    prof_idx = PROFESSIONS.index(prof) if prof in PROFESSIONS else len(PROFESSIONS)
    specs = PROFESSION_TO_SPECS.get(prof, [])
    spec_idx = specs.index(spec) if spec in specs else len(specs)
    return (prof_idx, spec_idx, role_name)


def _rename_role_everywhere(old: str, new: str) -> None:
    """Rename role key in roles dict, all player lists, all setup spot state,
    and persist the rename atomically in the DB."""
    if old == new:
        return
    st.session_state.roles[new] = st.session_state.roles.pop(old)
    for player_roles in st.session_state.players.values():
        for i, r in enumerate(player_roles):
            if r == old:
                player_roles[i] = new
    for r in range(MAX_GROUPS):
        for c in range(NUM_COLS):
            if st.session_state.get(_role_key(r, c)) == old:
                st.session_state[_role_key(r, c)] = new
    try:
        storage.rename_role(old, new)
    except Exception as e:
        st.toast(f"Role rename failed to persist: {e}", icon="⚠️")


def _rename_player_everywhere(old: str, new: str) -> None:
    """Rename player key in players dict, all setup spot state, and the DB."""
    if old == new:
        return
    st.session_state.players[new] = st.session_state.players.pop(old)
    for r in range(MAX_GROUPS):
        for c in range(NUM_COLS):
            if st.session_state.get(_player_key(r, c)) == old:
                st.session_state[_player_key(r, c)] = new
    try:
        storage.rename_player(old, new)
    except Exception as e:
        st.toast(f"Player rename failed to persist: {e}", icon="⚠️")


def _persist_role(name: str) -> None:
    """Write the in-memory state of role `name` to the DB. If the role no
    longer exists in session state, delete it from the DB instead."""
    raw = st.session_state.roles.get(name)
    try:
        if raw is None:
            storage.delete_role(name)
            return
        storage.upsert_role(
            Role(
                name=name,
                profession=raw["profession"],
                specialization=raw["specialization"],
                tags=list(raw["tags"]),
            )
        )
    except Exception as e:
        st.toast(f"Role save failed: {e}", icon="⚠️")


def _persist_player(name: str) -> None:
    raw = st.session_state.players.get(name)
    try:
        if raw is None:
            storage.delete_player(name)
            return
        storage.upsert_player(Player(name=name, role_priorities=list(raw)))
    except Exception as e:
        st.toast(f"Player save failed: {e}", icon="⚠️")


# ---- Edit dialogs ----

_ROLE_DRAFT_KEYS = (
    "_role_draft",
    "_role_draft_for",
    "_role_dlg_name",
    "_role_dlg_prof",
    "_role_dlg_spec",
    "_role_dlg_tags",
)
_PLAYER_DRAFT_KEYS = (
    "_player_draft",
    "_player_draft_for",
    "_player_dlg_name",
    "_player_add_pick",
    "_player_add_custom",
)


def _close_role_dialog() -> None:
    for k in _ROLE_DRAFT_KEYS:
        if k in st.session_state:
            del st.session_state[k]


def _close_player_dialog() -> None:
    for k in _PLAYER_DRAFT_KEYS:
        if k in st.session_state:
            del st.session_state[k]


def _next_new_player_name() -> str:
    n = 1
    while f"New player {n}" in st.session_state.players:
        n += 1
    return f"New player {n}"


def _next_new_role_name() -> str:
    n = 1
    while f"New role {n}" in st.session_state.roles:
        n += 1
    return f"New role {n}"


@st.dialog("Edit role", width="large")
def edit_role_dialog(role_name: str) -> None:
    # Lazy-init draft tied to this specific role; reset if user switched roles.
    if st.session_state.get("_role_draft_for") != role_name:
        st.session_state["_role_draft_for"] = role_name
        st.session_state["_role_draft"] = {
            "profession": st.session_state.roles[role_name]["profession"],
            "specialization": st.session_state.roles[role_name]["specialization"],
        }
        for k in (
            "_role_dlg_name",
            "_role_dlg_prof",
            "_role_dlg_spec",
            "_role_dlg_tags",
        ):
            if k in st.session_state:
                del st.session_state[k]

    role = st.session_state.roles[role_name]
    draft = st.session_state["_role_draft"]

    new_name = st.text_input("Name", value=role_name, key="_role_dlg_name").strip()

    cols = st.columns(2)
    with cols[0]:
        prof_index = (
            PROFESSIONS.index(draft["profession"])
            if draft["profession"] in PROFESSIONS
            else 0
        )
        new_prof = st.selectbox(
            "Profession",
            options=PROFESSIONS,
            index=prof_index,
            key="_role_dlg_prof",
        )
        # On prof change snap spec to first of new profession; no explicit rerun
        # — st.rerun() inside a dialog closes it.
        if new_prof != draft["profession"]:
            draft["profession"] = new_prof
            draft["specialization"] = PROFESSION_TO_SPECS[new_prof][0]
            if "_role_dlg_spec" in st.session_state:
                del st.session_state["_role_dlg_spec"]
    with cols[1]:
        specs = PROFESSION_TO_SPECS[new_prof]
        spec_index = (
            specs.index(draft["specialization"])
            if draft["specialization"] in specs
            else 0
        )
        new_spec = st.selectbox(
            "Specialization",
            options=specs,
            index=spec_index,
            key="_role_dlg_spec",
        )
        draft["specialization"] = new_spec

    new_tags = st.multiselect(
        "Tags",
        options=TAG_OPTIONS,
        default=role["tags"],
        key="_role_dlg_tags",
    )

    icon_path = _icon_path_for_spec(new_spec)
    if icon_path and icon_path.exists():
        st.image(str(icon_path), width=72)

    st.divider()
    btn_cols = st.columns(3)
    with btn_cols[0]:
        if st.button(
            "Save", type="primary", use_container_width=True, key="_role_save"
        ):
            if not new_name:
                st.error("Name is required.")
            elif new_name != role_name and new_name in st.session_state.roles:
                st.error(f"Role '{new_name}' already exists.")
            else:
                st.session_state.roles[role_name] = {
                    "profession": new_prof,
                    "specialization": new_spec,
                    "tags": list(new_tags),
                }
                _rename_role_everywhere(role_name, new_name)
                _persist_role(new_name)
                # Saved: clear any pending-create marker (this role is now
                # legitimately persisted).
                st.session_state.pop("_pending_create_role", None)
                _close_role_dialog()
                st.rerun()
    with btn_cols[1]:
        if st.button("Delete", use_container_width=True, key="_role_delete"):
            del st.session_state.roles[role_name]
            _persist_role(role_name)
            st.session_state.pop("_pending_create_role", None)
            _close_role_dialog()
            st.rerun()
    with btn_cols[2]:
        if st.button("Cancel", use_container_width=True, key="_role_cancel"):
            # If this dialog was opened by "+ Add role", the in-memory entry
            # was never persisted; roll it back so we don't leave a phantom.
            pending = st.session_state.pop("_pending_create_role", None)
            if pending == role_name:
                st.session_state.roles.pop(role_name, None)
            _close_role_dialog()
            st.rerun()


@st.fragment
def _player_roles_fragment() -> None:
    """Rendered inside edit_player_dialog. Lives in a fragment so list
    reorder/add/remove buttons rerun ONLY the fragment (st.rerun closes
    dialogs unless scoped to the fragment)."""
    draft_roles: list[str] = st.session_state["_player_draft"]

    st.markdown("**Roles** — top to bottom = highest to lowest priority")

    for i, rn in enumerate(draft_roles):
        line_cols = st.columns([1, 1, 1, 2, 9])
        with line_cols[0]:
            if st.button(
                "↑",
                key=f"_p_up_{i}",
                disabled=(i == 0),
                use_container_width=True,
            ):
                draft_roles[i - 1], draft_roles[i] = (
                    draft_roles[i],
                    draft_roles[i - 1],
                )
                st.rerun(scope="fragment")
        with line_cols[1]:
            if st.button(
                "↓",
                key=f"_p_down_{i}",
                disabled=(i == len(draft_roles) - 1),
                use_container_width=True,
            ):
                draft_roles[i + 1], draft_roles[i] = (
                    draft_roles[i],
                    draft_roles[i + 1],
                )
                st.rerun(scope="fragment")
        with line_cols[2]:
            if st.button(
                "✗",
                key=f"_p_del_{i}",
                use_container_width=True,
            ):
                draft_roles.pop(i)
                st.rerun(scope="fragment")
        with line_cols[3]:
            icon_path = _icon_path_for_role(rn)
            if icon_path and icon_path.exists():
                st.image(str(icon_path), width=54)
        with line_cols[4]:
            st.markdown(f"**{i + 1}.** {rn}")

    known_roles = sorted(st.session_state.roles.keys(), key=_role_sort_key)
    unused = [rn for rn in known_roles if rn not in draft_roles]
    add_cols = st.columns([5, 5, 1])
    with add_cols[0]:
        pick = st.selectbox(
            "Add known role",
            options=[""] + unused,
            key="_player_add_pick",
            label_visibility="collapsed",
            placeholder="Pick from known roles…",
        )
    with add_cols[1]:
        custom = st.text_input(
            "Custom role",
            key="_player_add_custom",
            label_visibility="collapsed",
            placeholder="Or type a custom role…",
        )
    with add_cols[2]:
        custom_trim = custom.strip()
        to_add = custom_trim or pick
        if st.button(
            "+",
            key="_player_add_btn",
            disabled=not to_add or to_add in draft_roles,
            use_container_width=True,
        ):
            draft_roles.append(to_add)
            for k in ("_player_add_pick", "_player_add_custom"):
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun(scope="fragment")


@st.dialog("Edit player", width="large")
def edit_player_dialog(player_name: str) -> None:
    # Lazy-init draft tied to this specific player.
    if st.session_state.get("_player_draft_for") != player_name:
        st.session_state["_player_draft_for"] = player_name
        st.session_state["_player_draft"] = list(st.session_state.players[player_name])
        for k in ("_player_dlg_name", "_player_add_pick", "_player_add_custom"):
            if k in st.session_state:
                del st.session_state[k]

    new_name = st.text_input("Name", value=player_name, key="_player_dlg_name").strip()

    _player_roles_fragment()

    st.divider()
    btn_cols = st.columns(3)
    with btn_cols[0]:
        if st.button(
            "Save", type="primary", use_container_width=True, key="_player_save"
        ):
            if not new_name:
                st.error("Name is required.")
            elif new_name != player_name and new_name in st.session_state.players:
                st.error(f"Player '{new_name}' already exists.")
            else:
                st.session_state.players[player_name] = list(
                    st.session_state["_player_draft"]
                )
                _rename_player_everywhere(player_name, new_name)
                _persist_player(new_name)
                st.session_state.pop("_pending_create_player", None)
                _close_player_dialog()
                st.rerun()
    with btn_cols[1]:
        if st.button("Delete", use_container_width=True, key="_player_delete"):
            del st.session_state.players[player_name]
            _persist_player(player_name)
            st.session_state.pop("_pending_create_player", None)
            _close_player_dialog()
            st.rerun()
    with btn_cols[2]:
        if st.button("Cancel", use_container_width=True, key="_player_cancel"):
            pending = st.session_state.pop("_pending_create_player", None)
            if pending == player_name:
                st.session_state.players.pop(player_name, None)
            _close_player_dialog()
            st.rerun()


@st.fragment
def _pick_role_fragment(r: int, c: int) -> None:
    """Body of the pick_role_dialog. Wrapped in a fragment so tag clicks
    rerun ONLY this fragment (highlight catches up immediately without
    closing the surrounding dialog)."""
    rk = _role_key(r, c)
    pk = _player_key(r, c)
    active_tag_key = f"_active_role_tag_{r}_{c}"
    if active_tag_key not in st.session_state:
        st.session_state[active_tag_key] = (
            COL_DEFAULT_TAGS[c] if c < len(COL_DEFAULT_TAGS) else "All"
        )

    active_tag = st.session_state[active_tag_key]

    cols = st.columns([1, 3], gap="small")
    with cols[0]:
        st.markdown("**Tags**")
        for t in ["All"] + TAG_OPTIONS:
            btn_type = "primary" if t == active_tag else "secondary"
            if st.button(
                t,
                key=f"_pr_tag_{r}_{c}_{t}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state[active_tag_key] = t
                # Fragment-scoped rerun: dialog stays open, highlight refreshes.
                st.rerun(scope="fragment")

    role_names_all = sorted(st.session_state.roles.keys(), key=_role_sort_key)
    if active_tag == "All":
        filtered = role_names_all
    else:
        filtered = [
            rn
            for rn in role_names_all
            if active_tag in st.session_state.roles[rn]["tags"]
        ]

    with cols[1]:
        st.markdown(f"**Roles — {active_tag}**")
        if not filtered:
            st.caption("No roles match this tag.")
        for rn in filtered:
            sub = st.columns([1, 9], gap="small")
            with sub[0]:
                p = _icon_path_for_role(rn)
                if p and p.exists():
                    st.image(str(p), width=28)
            with sub[1]:
                if st.button(
                    rn,
                    key=f"_pr_role_{r}_{c}_{rn}",
                    use_container_width=True,
                ):
                    if st.session_state.get(rk) != rn:
                        st.session_state[rk] = rn
                        st.session_state[pk] = ""
                    if active_tag_key in st.session_state:
                        del st.session_state[active_tag_key]
                    # Full rerun closes the dialog.
                    st.rerun()

    st.divider()
    bcols = st.columns(2)
    with bcols[0]:
        if st.session_state.get(rk):
            if st.button(
                "✗ Clear role",
                key=f"_pr_clear_{r}_{c}",
                use_container_width=True,
            ):
                st.session_state[rk] = ""
                st.session_state[pk] = ""
                if active_tag_key in st.session_state:
                    del st.session_state[active_tag_key]
                st.rerun()
    with bcols[1]:
        if st.button(
            "Cancel",
            key=f"_pr_cancel_{r}_{c}",
            use_container_width=True,
        ):
            if active_tag_key in st.session_state:
                del st.session_state[active_tag_key]
            st.rerun()


@st.dialog("Pick a role", width="small")
def pick_role_dialog(r: int, c: int) -> None:
    _pick_role_fragment(r, c)


# ==================== UI ====================

st.set_page_config(
    page_title="GW2 Squad Builder",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize mutable state once per session, sourced from the DB.
if "_db_initialised" not in st.session_state:
    # Seed the DB with hardcoded defaults on first ever app launch.
    seed_roles = {
        name: Role(
            name=name,
            profession=raw["profession"],
            specialization=raw["specialization"],
            tags=list(raw["tags"]),
        )
        for name, raw in DEFAULT_ROLES.items()
    }
    seed_players = {
        name: Player(name=name, role_priorities=list(raw))
        for name, raw in DEFAULT_PLAYERS.items()
    }
    try:
        storage.init_db(default_roles=seed_roles, default_players=seed_players)
    except Exception as e:
        st.error(f"Could not initialise database at {storage.db_path()}: {e}")
    st.session_state["_db_initialised"] = True

if "roles" not in st.session_state or "players" not in st.session_state:
    try:
        db_roles, db_players = storage.load_all()
    except Exception as e:
        st.error(f"Could not load from database: {e}; falling back to defaults.")
        db_roles, db_players = {}, {}
    if db_roles:
        st.session_state.roles = {
            name: {
                "profession": role.profession.value,
                "specialization": role.specialization.value,
                "tags": [t.value for t in role.tags],
            }
            for name, role in db_roles.items()
        }
    else:
        st.session_state.roles = deepcopy(DEFAULT_ROLES)
    if db_players:
        st.session_state.players = {
            name: list(player.role_priorities) for name, player in db_players.items()
        }
    else:
        st.session_state.players = deepcopy(DEFAULT_PLAYERS)

if "num_groups" not in st.session_state:
    st.session_state.num_groups = max(len(DEFAULT_SETUP), 1)
    for _r, _row in enumerate(DEFAULT_SETUP):
        for _c, (_role, _player) in enumerate(_row[:NUM_COLS]):
            st.session_state[_role_key(_r, _c)] = _role
            st.session_state[_player_key(_r, _c)] = _player

st.title("GW2 Squad Builder")

# Process any pending group mutation BEFORE widgets render this run.
# (Direct st.session_state writes to widget keys after widget instantiation
# raise StreamlitAPIException — so delete/add buttons defer the shift to the
# next run via this pending-action pattern.)
_pending = st.session_state.pop("_grp_pending", None)
if _pending:
    _action, _idx = _pending
    _n = st.session_state["num_groups"]
    if _action == "delete":
        for _rr in range(_idx, _n - 1):
            for _cc in range(NUM_COLS):
                st.session_state[_role_key(_rr, _cc)] = st.session_state.get(
                    _role_key(_rr + 1, _cc), ""
                )
                st.session_state[_player_key(_rr, _cc)] = st.session_state.get(
                    _player_key(_rr + 1, _cc), ""
                )
        for _cc in range(NUM_COLS):
            st.session_state.pop(_role_key(_n - 1, _cc), None)
            st.session_state.pop(_player_key(_n - 1, _cc), None)
        st.session_state["num_groups"] = _n - 1
    elif _action == "add":
        for _rr in range(_n, _idx + 1, -1):
            for _cc in range(NUM_COLS):
                st.session_state[_role_key(_rr, _cc)] = st.session_state.get(
                    _role_key(_rr - 1, _cc), ""
                )
                st.session_state[_player_key(_rr, _cc)] = st.session_state.get(
                    _player_key(_rr - 1, _cc), ""
                )
        for _cc in range(NUM_COLS):
            st.session_state[_role_key(_idx + 1, _cc)] = ""
            st.session_state[_player_key(_idx + 1, _cc)] = ""
        st.session_state["num_groups"] = _n + 1

num_groups = _num_groups()

tab_setup, tab_roles, tab_players = st.tabs(["Setup", "Roles", "Players"])


# ---------- Setup tab ----------
with tab_setup:
    role_names_sorted = sorted(st.session_state.roles.keys(), key=_role_sort_key)

    GROUP_LABEL_WEIGHT = 1
    SPOT_WEIGHT = 4
    for r in range(num_groups):
        row_cols = st.columns([SPOT_WEIGHT] * NUM_COLS + [GROUP_LABEL_WEIGHT])
        for c in range(NUM_COLS):
            with row_cols[c]:
                with st.container(border=True):
                    rk = _role_key(r, c)
                    pk = _player_key(r, c)

                    # Drop stale role reference (role may have been deleted).
                    stale_role = st.session_state.get(rk, "")
                    if stale_role and stale_role not in st.session_state.roles:
                        st.session_state[rk] = ""

                    role = st.session_state.get(rk, "")
                    available = candidates_for(role, (r, c)) if role else []

                    current_player = st.session_state.get(pk, "")
                    if current_player and current_player not in available:
                        st.session_state[pk] = ""
                        current_player = ""

                    # Row 1: clickable opener for the role-picker dialog.
                    # When a role is set: HTML strip [icon + name + count] plus
                    # a small Material edit icon button on the right. When no
                    # role: a single borderless ("tertiary") button styled like
                    # the previous "No role" placeholder.
                    if role:
                        url = _role_data_url(role)
                        # Count of OTHER options: total candidates minus self
                        # if a player is currently assigned to this spot.
                        other_count = len(available) - (1 if current_player else 0)
                        count_html = (
                            "<span style='margin-left:auto;color:#888;"
                            f"font-size:0.85em;'>{other_count} avail</span>"
                        )
                        if url:
                            row_html = (
                                "<div style='display:flex;align-items:center;"
                                "height:40px;'>"
                                f"<img src='{url}' style='width:36px;height:36px;"
                                "margin-right:8px;'>"
                                "<span style='font-weight:600;font-size:1.05em;'>"
                                f"{_truncate(role, 18)}</span>"
                                f"{count_html}"
                                "</div>"
                            )
                        else:
                            row_html = (
                                "<div style='display:flex;align-items:center;"
                                "height:40px;'>"
                                "<span style='font-weight:600;font-size:1.05em;'>"
                                f"{_truncate(role, 18)}</span>"
                                f"{count_html}"
                                "</div>"
                            )
                        head_cols = st.columns([8, 1], gap="small")
                        with head_cols[0]:
                            st.markdown(row_html, unsafe_allow_html=True)
                        with head_cols[1]:
                            if st.button(
                                "",
                                icon=":material/edit:",
                                key=f"_open_role_dlg_{r}_{c}",
                                help="Change role",
                                type="tertiary",
                                use_container_width=True,
                            ):
                                pick_role_dialog(r, c)
                    else:
                        if st.button(
                            "Pick a role…",
                            key=f"_open_role_dlg_{r}_{c}",
                            type="secondary",
                        ):
                            pick_role_dialog(r, c)

                    # Row 2: player selectbox (single-line dropdown).
                    st.selectbox(
                        "Player",
                        options=[""] + available,
                        key=pk,
                        label_visibility="collapsed",
                        placeholder=(
                            f"Pick from {len(available)} player(s)"
                            if role
                            else "(no role yet)"
                        ),
                        disabled=not role,
                        format_func=lambda x: _truncate(x, 20) if x else "—",
                    )
        with row_cols[NUM_COLS]:
            st.markdown(f"**Group {r + 1}**")
            grp_btns = st.columns(2, gap="small")
            with grp_btns[0]:
                if st.button(
                    "",
                    icon=":material/delete:",
                    type="tertiary",
                    help="Delete this group",
                    key=f"_del_grp_{r}",
                    disabled=num_groups <= 1,
                ):
                    st.session_state["_grp_pending"] = ("delete", r)
                    st.rerun()
            with grp_btns[1]:
                if st.button(
                    "",
                    icon=":material/add:",
                    type="tertiary",
                    help="Add a new group below this one",
                    key=f"_add_grp_{r}",
                    disabled=num_groups >= MAX_GROUPS,
                ):
                    st.session_state["_grp_pending"] = ("add", r)
                    st.rerun()

    st.divider()
    st.subheader("Copy/paste for Discord")

    # Per-column padding: longest visible string in each column. Spec emoji
    # (`:profession_spec:`) renders as 1 char in Discord by definition, so we
    # don't include its length in the padding calculation.
    col_widths = [0] * NUM_COLS
    cell_data: list[list[tuple[str, str]]] = []
    for r in range(num_groups):
        row_cells: list[tuple[str, str]] = []
        for c in range(NUM_COLS):
            role_str_val = st.session_state.get(_role_key(r, c), "")
            ply = st.session_state.get(_player_key(r, c), "")
            cls_str = _discord_emoji_for_role(role_str_val) if role_str_val else "—"
            if ply:
                ply_str = _truncate(ply, 20)
            else:
                ply_str = "-unassigned-" if role_str_val else "—"
            row_cells.append((ply_str, cls_str))
            col_widths[c] = max(col_widths[c], len(ply_str))
        cell_data.append(row_cells)

    summary_lines: list[str] = []
    for row_cells in cell_data:
        row_items: list[str] = []
        for c, (ply_str, cls_str) in enumerate(row_cells):
            # Wrap padded player names in backticks so Discord renders them
            # as monospaced inline code (its default font is proportional).
            row_items.append(f"{cls_str}`{ply_str.ljust(col_widths[c])}`")
        summary_lines.append(" | ".join(row_items))

    # Leading zero-width space + newline so Discord pastes start on a fresh
    # line. Streamlit's st.code strips plain leading whitespace, but ZWSP
    # (U+200B) is not whitespace and survives, anchoring the newline.
    st.code("​\n" + "\n".join(summary_lines), language="text")


# ---------- Roles tab ----------
with tab_roles:
    _, _roles_mid, _ = st.columns([1, 3, 1])

with _roles_mid:
    st.caption(
        "Click Edit to change a role in a popup. "
        "Profession determines which specializations are available. "
        "Tags describe what a role can contribute to a group."
    )

    for role_name in sorted(st.session_state.roles.keys(), key=_role_sort_key):
        role = st.session_state.roles[role_name]
        icon_path = _icon_path_for_spec(role["specialization"])

        outer_cols = st.columns([1, 6, 8, 1, 1])
        with outer_cols[0]:
            if icon_path and icon_path.exists():
                st.image(str(icon_path), width=40)
        with outer_cols[1]:
            st.markdown(f"**{role_name}**")
        with outer_cols[2]:
            st.caption(", ".join(role["tags"]) if role["tags"] else "—")
        with outer_cols[3]:
            if st.button(
                "",
                icon=":material/edit:",
                key=f"edit_role_btn_{role_name}",
                type="tertiary",
                help="Edit role",
                use_container_width=True,
            ):
                edit_role_dialog(role_name)
        with outer_cols[4]:
            if st.button(
                "",
                icon=":material/delete:",
                key=f"del_role_inline_{role_name}",
                type="tertiary",
                help="Delete role",
                use_container_width=True,
            ):
                del st.session_state.roles[role_name]
                _persist_role(role_name)
                st.rerun()

    st.divider()
    if st.button("➕ Add role", key="add_role_btn"):
        new_name = _next_new_role_name()
        st.session_state.roles[new_name] = {
            "profession": PROFESSIONS[0],
            "specialization": PROFESSION_TO_SPECS[PROFESSIONS[0]][0],
            "tags": [],
        }
        # Mark as pending: not yet persisted to DB. Save will commit,
        # Cancel will roll back the in-memory entry.
        st.session_state["_pending_create_role"] = new_name
        edit_role_dialog(new_name)


# ---------- Players tab ----------
with tab_players:
    _, _players_mid, _ = st.columns([1, 3, 1])

with _players_mid:
    st.caption(
        "Click Edit to change a player in a popup: rename, reorder roles, add/remove roles."
    )

    PREVIEW_LIMIT = 8

    for player_name in sorted(st.session_state.players.keys()):
        player_roles = st.session_state.players[player_name]

        outer_cols = st.columns([3, 12, 1, 1])
        with outer_cols[0]:
            st.markdown(f"**{player_name}**")
        with outer_cols[1]:
            preview = player_roles[:PREVIEW_LIMIT]
            overflow = len(player_roles) - len(preview)
            if preview or overflow > 0:
                parts: list[str] = []
                for rn in preview:
                    url = _role_data_url(rn)
                    if url:
                        parts.append(
                            f'<img src="{url}" '
                            f'style="width:36px;height:36px;margin-right:2px;'
                            f'vertical-align:middle;" alt="{rn}">'
                        )
                    else:
                        parts.append(
                            f'<span style="display:inline-block;width:36px;'
                            f"height:36px;line-height:36px;text-align:center;"
                            f"color:#888;font-size:10px;margin-right:2px;"
                            f'vertical-align:middle;">{rn[:4]}</span>'
                        )
                if overflow > 0:
                    parts.append(
                        f'<span style="color:#888;vertical-align:middle;'
                        f'margin-left:6px;">+{overflow} more</span>'
                    )
                st.markdown(
                    "<div style='display:flex;align-items:center;'>"
                    + "".join(parts)
                    + "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption("(no roles)")
        with outer_cols[2]:
            if st.button(
                "",
                icon=":material/edit:",
                key=f"edit_player_btn_{player_name}",
                type="tertiary",
                help="Edit player",
                use_container_width=True,
            ):
                edit_player_dialog(player_name)
        with outer_cols[3]:
            if st.button(
                "",
                icon=":material/delete:",
                key=f"del_player_inline_{player_name}",
                type="tertiary",
                help="Delete player",
                use_container_width=True,
            ):
                del st.session_state.players[player_name]
                _persist_player(player_name)
                st.rerun()

    st.divider()
    if st.button("➕ Add player", key="add_player_btn"):
        new_name = _next_new_player_name()
        st.session_state.players[new_name] = []
        st.session_state["_pending_create_player"] = new_name
        edit_player_dialog(new_name)
