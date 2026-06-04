"""
Domain models for the GW2 Squad Builder.

Pydantic v2. Pure data — no streamlit, no DB. Used by the storage layer for
serialisation and by the future setup-import / URL-share feature.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class Profession(str, Enum):
    ELEMENTALIST = "Elementalist"
    ENGINEER = "Engineer"
    GUARDIAN = "Guardian"
    MESMER = "Mesmer"
    NECROMANCER = "Necromancer"
    RANGER = "Ranger"
    REVENANT = "Revenant"
    THIEF = "Thief"
    WARRIOR = "Warrior"


class Specialization(str, Enum):
    # Elementalist
    ELEMENTALIST = "Elementalist"
    CATALYST = "Catalyst"
    EVOKER = "Evoker"
    TEMPEST = "Tempest"
    WEAVER = "Weaver"
    # Engineer
    ENGINEER = "Engineer"
    AMALGAM = "Amalgam"
    HOLOSMITH = "Holosmith"
    MECHANIST = "Mechanist"
    SCRAPPER = "Scrapper"
    # Guardian
    GUARDIAN = "Guardian"
    DRAGONHUNTER = "Dragonhunter"
    FIREBRAND = "Firebrand"
    LUMINARY = "Luminary"
    WILLBENDER = "Willbender"
    # Mesmer
    MESMER = "Mesmer"
    CHRONOMANCER = "Chronomancer"
    MIRAGE = "Mirage"
    TROUBADOUR = "Troubadour"
    VIRTUOSO = "Virtuoso"
    # Necromancer
    NECROMANCER = "Necromancer"
    HARBINGER = "Harbinger"
    REAPER = "Reaper"
    RITUALIST = "Ritualist"
    SCOURGE = "Scourge"
    # Ranger
    RANGER = "Ranger"
    DRUID = "Druid"
    GALESHOT = "Galeshot"
    SOULBEAST = "Soulbeast"
    UNTAMED = "Untamed"
    # Revenant
    REVENANT = "Revenant"
    CONDUIT = "Conduit"
    HERALD = "Herald"
    RENEGADE = "Renegade"
    VINDICATOR = "Vindicator"
    # Thief
    THIEF = "Thief"
    ANTIQUARY = "Antiquary"
    DAREDEVIL = "Daredevil"
    DEADEYE = "Deadeye"
    SPECTER = "Specter"
    # Warrior
    WARRIOR = "Warrior"
    BERSERKER = "Berserker"
    BLADESWORN = "Bladesworn"
    PARAGON = "Paragon"
    SPELLBREAKER = "Spellbreaker"


class Tag(str, Enum):
    STABILITY = "Stability"
    HEAL = "Heal"
    BOONS = "Boons"
    CLEANSE = "Cleanse"
    DPS = "DPS"
    STRIPS = "Strips"
    SMOKE = "Smoke"


# Authoritative map: profession -> list of valid specs.
# Core profession spec comes first per the convention used in the UI dropdowns.
PROFESSION_TO_SPECS: dict[Profession, list[Specialization]] = {
    Profession.ELEMENTALIST: [
        Specialization.ELEMENTALIST,
        Specialization.CATALYST,
        Specialization.EVOKER,
        Specialization.TEMPEST,
        Specialization.WEAVER,
    ],
    Profession.ENGINEER: [
        Specialization.ENGINEER,
        Specialization.AMALGAM,
        Specialization.HOLOSMITH,
        Specialization.MECHANIST,
        Specialization.SCRAPPER,
    ],
    Profession.GUARDIAN: [
        Specialization.GUARDIAN,
        Specialization.DRAGONHUNTER,
        Specialization.FIREBRAND,
        Specialization.LUMINARY,
        Specialization.WILLBENDER,
    ],
    Profession.MESMER: [
        Specialization.MESMER,
        Specialization.CHRONOMANCER,
        Specialization.MIRAGE,
        Specialization.TROUBADOUR,
        Specialization.VIRTUOSO,
    ],
    Profession.NECROMANCER: [
        Specialization.NECROMANCER,
        Specialization.HARBINGER,
        Specialization.REAPER,
        Specialization.RITUALIST,
        Specialization.SCOURGE,
    ],
    Profession.RANGER: [
        Specialization.RANGER,
        Specialization.DRUID,
        Specialization.GALESHOT,
        Specialization.SOULBEAST,
        Specialization.UNTAMED,
    ],
    Profession.REVENANT: [
        Specialization.REVENANT,
        Specialization.CONDUIT,
        Specialization.HERALD,
        Specialization.RENEGADE,
        Specialization.VINDICATOR,
    ],
    Profession.THIEF: [
        Specialization.THIEF,
        Specialization.ANTIQUARY,
        Specialization.DAREDEVIL,
        Specialization.DEADEYE,
        Specialization.SPECTER,
    ],
    Profession.WARRIOR: [
        Specialization.WARRIOR,
        Specialization.BERSERKER,
        Specialization.BLADESWORN,
        Specialization.PARAGON,
        Specialization.SPELLBREAKER,
    ],
}


class Role(BaseModel):
    """A named build assignment: profession + specialization + tags."""

    name: str
    profession: Profession
    specialization: Specialization
    tags: list[Tag] = Field(default_factory=list)

    @model_validator(mode="after")
    def _spec_belongs_to_profession(self) -> "Role":
        valid_specs = PROFESSION_TO_SPECS[self.profession]
        if self.specialization not in valid_specs:
            raise ValueError(
                f"Specialization {self.specialization.value!r} does not belong "
                f"to profession {self.profession.value!r}. "
                f"Valid: {[s.value for s in valid_specs]}"
            )
        return self


class Player(BaseModel):
    """A named player and their ordered role priority list.

    role_priorities holds role NAMES as strings (not Role objects) so a player
    list can keep orphan/custom role references that are not in the Role table.
    """

    name: str
    role_priorities: list[str] = Field(default_factory=list)


class Spot(BaseModel):
    """One slot in a setup grid.

    Both fields are optional: a spot can have no role chosen and no player
    assigned. Not persisted to the DB on its own; used as a serialisation
    shape for the future setup import / URL-share feature.
    """

    role: str | None = None
    player: str | None = None


class Setup(BaseModel):
    """A full setup grid: list of groups, each group a list of Spots."""

    groups: list[list[Spot]] = Field(default_factory=list)

    # Matches the format emitted by tab_setup's "Copy/paste for Discord" code
    # block:  :profession_spec:`player name (padded)`
    _DISCORD_CELL = re.compile(
        r":(?P<prof>[a-z]+)_(?P<spec>[a-z]+):`(?P<player>[^`]*)`" r"|—\s*—|(?P<empty>—)"
    )

    @classmethod
    def from_discord_text(cls, text: str) -> "Setup":
        """Parse the discord-emoji block that tab_setup outputs back into a
        Setup. Best-effort: unknown tokens become None.

        Lines are groups, " | " separates cells, each cell is either
        `:profession_spec:` plus a backtick-wrapped (possibly padded) player
        name, or a single em-dash for fully empty spots.
        """
        # Specialisation lookup keyed by lowercase value.
        spec_by_lower = {s.value.lower(): s for s in Specialization}

        groups: list[list[Spot]] = []
        for raw_line in text.strip("​\n").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            cells: list[Spot] = []
            for raw_cell in line.split(" | "):
                cell = raw_cell.strip()
                if not cell or cell == "—":
                    cells.append(Spot())
                    continue
                m = re.match(
                    r":(?P<prof>[a-z]+)_(?P<spec>[a-z]+):`(?P<player>[^`]*)`",
                    cell,
                )
                if not m:
                    cells.append(Spot())
                    continue
                spec_key = m.group("spec")
                spec = spec_by_lower.get(spec_key)
                # We can't recover the role name from the discord emoji alone
                # (one spec can map to multiple roles, e.g. "Heal Scrapper" /
                # "DPS Scrapper" both render as :engineer_scrapper:). Return
                # the spec name as the role placeholder; caller can resolve.
                role_placeholder = spec.value if spec else None
                player_padded = m.group("player").strip() or None
                cells.append(Spot(role=role_placeholder, player=player_padded))
            groups.append(cells)
        return cls(groups=groups)
