"""
GW2 Squad Builder — initial single-file Streamlit prototype.

Run with:
    streamlit run gw2_squad_builder.py
"""

import streamlit as st

# ==================== DATA ====================

# Player preferences. Keyed by player.
# Each value maps class -> priority (1 = strong main, 2 = secondary, higher = flex).
# Within the same priority, players with fewer total classes ("one-tricks") sort first.
PLAYERS: dict[str, dict[str, int]] = {
    "Lullu": {"Druid": 1},
    "NappoLeo": {"Paragon": 1},
    "kfc": {"HFB / Firebrand": 1, "Paragon": 1},
    # "Any DPS, Sup Trouba on Lead"
    "Semtäx": {
        "Troubadour": 1,
        "Reaper": 2,
        "Ritualist": 2,
        "Amalgam": 2,
        "Holosmith": 2,
        "Untamed": 2,
        "DPS Ele": 2,
        "Virtuoso": 2,
        "Spellbreaker": 2,
        "Dragonhunter": 2,
        "Willbender": 2,
        "Soulbeast": 2,
        "Daredevil": 2,
        "DPS Scrapper": 2,
    },
    # "FB/DH/Lumi Guardian, Mesmer (Virtuoso and chrono), Druid, support scrapper"
    "Colmyllo Blanco": {
        "HFB / Firebrand": 1,
        "Dragonhunter": 1,
        "Lumi": 1,
        "Willbender": 1,
        "Virtuoso": 2,
        "Heal Chrono": 2,
        "Druid": 3,
        "Heal Scrapper": 3,
    },
    # Heal: Scrapper/Druid; Boon: Harb/Para; DPS: Amalgam/Holo; DPS+strip: Reaper/Core
    "Suushi": {
        "Heal Scrapper": 1,
        "Druid": 1,
        "Support Harbinger": 1,
        "Paragon": 1,
        "Amalgam": 1,
        "Holosmith": 1,
        "Reaper": 1,
        "Core Necro": 1,
        "Scourge": 2,
        "DPS Scrapper": 2,
    },
    # "Amalgam/Scrapper + Support para + Druid"
    "Melow": {
        "Amalgam": 1,
        "Heal Scrapper": 1,
        "Paragon": 1,
        "Druid": 1,
    },
    # "Druid, Troubadour, Scrapper (heal), Specter [Mostly all heal, can also play tertiary - Para, Harbi, trouba]"
    "Esskape": {
        "Druid": 1,
        "Troubadour": 1,
        "Heal Scrapper": 1,
        "Specter": 1,
        "Paragon": 2,
        "Support Harbinger": 2,
        "Heal Chrono": 3,
        "Support Catalyst": 3,
        "Support Tempest": 3,
    },
    # "SPB/paragon, untamed/druid/SB"
    "daRetzaa": {
        "Spellbreaker": 1,
        "Paragon": 1,
        "Untamed": 2,
        "Druid": 2,
        "Soulbeast": 2,
    },
    # "Anything Ele (DPS or Support) / Supp Para"
    "Punsi": {
        "DPS Ele": 1,
        "Support Tempest": 1,
        "Support Catalyst": 1,
        "Paragon": 2,
    },
    # "Stab HFB/Lumi, Support Para, Support Druid/Tempest, with some work dps untamed/Lumi"
    "Viv": {
        "HFB / Firebrand": 1,
        "Lumi": 1,
        "Paragon": 2,
        "Druid": 3,
        "Support Tempest": 3,
        "Untamed": 4,
    },
    # "Any Heal"
    "Disturbed": {
        "Druid": 2,
        "Heal Scrapper": 2,
        "Specter": 2,
        "Troubadour": 2,
        "Heal Chrono": 2,
        "Support Tempest": 2,
        "Support Catalyst": 2,
    },
    # "Want to try hard lumi dps, main is necro, can play everything but no HFB"
    "Sif": {
        "Lumi": 1,
        "Reaper": 2,
        "Scourge": 2,
        "Core Necro": 2,
        "Support Harbinger": 2,
        "Ritualist": 2,
        "Druid": 3,
        "Paragon": 3,
        "Troubadour": 3,
        "Amalgam": 3,
        "Holosmith": 3,
        "DPS Scrapper": 3,
        "Heal Scrapper": 3,
        "Untamed": 3,
        "Soulbeast": 3,
        "DPS Ele": 3,
        "Support Tempest": 3,
        "Support Catalyst": 3,
        "Virtuoso": 3,
        "Heal Chrono": 3,
        "Revenant": 3,
        "Spellbreaker": 3,
        "Dragonhunter": 3,
        "Willbender": 3,
        "Daredevil": 3,
        "Specter": 3,
    },
    # "Mainly DPS most exp on Ele, Engineer & Necro"
    "Tim": {
        "DPS Ele": 1,
        "Amalgam": 1,
        "Holosmith": 1,
        "DPS Scrapper": 1,
        "Reaper": 1,
        "Core Necro": 1,
        "Scourge": 1,
        "Ritualist": 1,
        "Untamed": 2,
        "Virtuoso": 2,
        "Spellbreaker": 2,
        "Dragonhunter": 2,
        "Willbender": 2,
        "Soulbeast": 2,
        "Daredevil": 2,
    },
    # "Druid most exp, paragon, supp spelly, Tempest, scrapper, trouba; no HFB GvG"
    "Krataxx": {
        "Druid": 1,
        "Paragon": 2,
        "Spellbreaker": 2,
        "Support Tempest": 2,
        "Heal Scrapper": 2,
        "Troubadour": 2,
    },
    # Main necro line, Scrapper/Holo/Amalgam, then secondary, then learning
    "Alex": {
        "Core Necro": 1,
        "Reaper": 1,
        "Scourge": 1,
        "Support Harbinger": 1,
        "DPS Scrapper": 1,
        "Heal Scrapper": 1,
        "Holosmith": 1,
        "Amalgam": 1,
        "Revenant": 2,
        "Virtuoso": 2,
        "Daredevil": 2,
        "Ritualist": 3,
        "Untamed": 3,
        "Spellbreaker": 3,
        "Druid": 4,
    },
    # "Vindicator/Conduit/Renegade/Herald for any role (preferred); DPS: Untamed/WB/Holo/Virt/any Necro; Support: Chrono/Lumi/Druid/Scourge"
    "Caradea": {
        "Revenant": 1,
        "Untamed": 2,
        "Willbender": 2,
        "Holosmith": 2,
        "Virtuoso": 2,
        "Reaper": 2,
        "Core Necro": 2,
        "Scourge": 2,
        "Heal Chrono": 2,
        "Lumi": 2,
        "Druid": 2,
    },
    # "all, im the god xd" — full flex, all classes at low priority
    "MonkeyDLuis": {
        c: 5
        for c in [
            "Druid",
            "Paragon",
            "Troubadour",
            "Lumi",
            "HFB / Firebrand",
            "Support Harbinger",
            "Reaper",
            "Scourge",
            "Core Necro",
            "Ritualist",
            "Amalgam",
            "Holosmith",
            "Untamed",
            "DPS Ele",
            "Support Tempest",
            "Support Catalyst",
            "Virtuoso",
            "Heal Chrono",
            "Heal Scrapper",
            "DPS Scrapper",
            "Revenant",
            "Spellbreaker",
            "Dragonhunter",
            "Willbender",
            "Soulbeast",
            "Daredevil",
            "Specter",
        ]
    },
}


# Classes grouped roughly by profession for the dropdown.
CLASSES: list[str] = [
    # Guardian
    "HFB / Firebrand",
    "Dragonhunter",
    "Willbender",
    "Lumi",
    # Ranger
    "Druid",
    "Soulbeast",
    "Untamed",
    # Engineer
    "Heal Scrapper",
    "DPS Scrapper",
    "Holosmith",
    "Amalgam",
    # Necromancer
    "Core Necro",
    "Reaper",
    "Scourge",
    "Support Harbinger",
    "Ritualist",
    # Warrior
    "Spellbreaker",
    "Paragon",
    # Mesmer
    "Troubadour",
    "Virtuoso",
    "Heal Chrono",
    # Elementalist
    "DPS Ele",
    "Support Tempest",
    "Support Catalyst",
    # Revenant
    "Revenant",
    # Thief
    "Daredevil",
    "Specter",
]


# ==================== STATE / LOGIC ====================

NUM_ROWS = 3
NUM_COLS = 3


def _class_key(r: int, c: int) -> str:
    return f"class_{r}_{c}"


def _player_key(r: int, c: int) -> str:
    return f"player_{r}_{c}"


def _picked_players_except(my_spot: tuple[int, int]) -> set[str]:
    """All players currently assigned to spots OTHER than `my_spot`."""
    picked: set[str] = set()
    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            if (r, c) == my_spot:
                continue
            v = st.session_state.get(_player_key(r, c))
            if v:
                picked.add(v)
    return picked


def candidates_for(cls: str, my_spot: tuple[int, int]) -> list[str]:
    """Available players for `cls`, sorted by (priority asc, total classes asc, name asc).

    Players already assigned to a different spot are excluded.
    """
    taken = _picked_players_except(my_spot)
    rows: list[tuple[int, int, str]] = []
    for player, class_map in PLAYERS.items():
        if cls not in class_map or player in taken:
            continue
        priority = class_map[cls]
        total = len(class_map)
        rows.append((priority, total, player))
    rows.sort()
    return [name for _, _, name in rows]


def _on_class_changed(r: int, c: int) -> None:
    """When the class for a spot changes, clear that spot's player."""
    st.session_state[_player_key(r, c)] = ""


# ==================== UI ====================

st.set_page_config(page_title="GW2 Squad Builder", layout="wide")
st.title("GW2 Squad Builder")
st.caption(
    "Pick a class for each spot. The number next to the class is how many players "
    "can still fill that role given current picks. Click it to assign a player."
)

# --- Reset button -------------------------------------------------------------
if st.button("Reset all spots"):
    for r in range(NUM_ROWS):
        for c in range(NUM_COLS):
            st.session_state[_class_key(r, c)] = ""
            st.session_state[_player_key(r, c)] = ""
    st.rerun()

# --- Spot grid ----------------------------------------------------------------
for r in range(NUM_ROWS):
    cols = st.columns(NUM_COLS)
    for c, col in enumerate(cols):
        with col:
            with st.container(border=True):
                ck = _class_key(r, c)
                pk = _player_key(r, c)

                st.markdown(f"**Spot {r + 1}.{c + 1}**")

                cls = st.selectbox(
                    "Class",
                    options=[""] + CLASSES,
                    key=ck,
                    on_change=_on_class_changed,
                    args=(r, c),
                    label_visibility="collapsed",
                    placeholder="Choose a class…",
                )

                if not cls:
                    st.caption("— no class picked —")
                    continue

                available = candidates_for(cls, (r, c))

                # If the player previously assigned here is no longer in the
                # candidate list (e.g. assigned to another spot in the meantime),
                # clear before rendering the picker.
                current_player = st.session_state.get(pk, "")
                if current_player and current_player not in available:
                    st.session_state[pk] = ""
                    current_player = ""

                name_col, badge_col = st.columns([3, 1])
                with name_col:
                    st.markdown(f"### {cls}")
                    if current_player:
                        st.markdown(f"👤 **{current_player}**")
                    else:
                        st.caption("no player assigned")
                with badge_col:
                    # The "click the number → dropdown opens" interaction.
                    with st.popover(
                        f"{len(available)}",
                        use_container_width=True,
                        help=f"{len(available)} player(s) can run {cls}",
                    ):
                        st.caption(f"Players who can run **{cls}**")
                        st.selectbox(
                            "Pick player",
                            options=[""] + available,
                            key=pk,
                            label_visibility="collapsed",
                        )

# --- Summary ------------------------------------------------------------------
st.divider()
st.subheader("Current setup")

summary_lines: list[str] = []
for r in range(NUM_ROWS):
    row_items: list[str] = []
    for c in range(NUM_COLS):
        cls = st.session_state.get(_class_key(r, c), "")
        ply = st.session_state.get(_player_key(r, c), "")
        if cls and ply:
            row_items.append(f"{ply:<16} {cls}")
        elif cls:
            row_items.append(f"{'(empty)':<16} {cls}")
        else:
            row_items.append(f"{'—':<16} {'—'}")
    summary_lines.append("   |   ".join(row_items))

st.code("\n".join(summary_lines), language="text")
