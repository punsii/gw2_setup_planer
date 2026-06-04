# gw2_setup_planer

A small Streamlit app for planning Guild Wars 2 GvG squad compositions. Pick
a role and a tag-filter for each spot, see which players can fill the role,
assign them, and copy the result as a `:profession_spec:`-emoji block
straight into Discord.

## Features

- **Setup tab** — grid of `N × 5` slots (1–10 groups). Per-spot role picker
  is a modal dialog with a left tag list (`Heal`, `DPS`, `Stability`, …) and
  a right role list filtered by the active tag. The player dropdown shows
  candidates sorted by their role-priority position, then by total number of
  roles they play (one-tricks first). At the bottom, a code block formats
  the whole squad for direct Discord paste.
- **Roles tab** — define roles. Each role has a name, a profession, a
  specialization (constrained to its profession's specs), and a list of
  tags. 27 default roles ship with the app (HFB, Druid, Heal Scrapper, …).
- **Players tab** — define players. Each player has a name and an ordered
  list of role names (index = priority). Reorder via ↑/↓ inside the edit
  modal. Custom / orphan role strings are allowed: a player can list a role
  that doesn't exist in the Roles tab.
- **Persistence** — roles and players are stored in a local SQLite database.
  Setup state is session-local (does not persist).
- **Profession icons** — bundled `assets/icons/` set sourced from the
  GW2 wiki (`icon_small` PNGs upscaled to 80×80 for visual uniformity).

## Running locally

The repo is a Nix flake. The dev shell + python env come from
`nixpkgs/nixos-unstable`.

```bash
direnv allow              # picks up .envrc → use flake .
nix run .#dev             # streamlit run app.py (uses cwd source)
```

Or without direnv:

```bash
nix develop
streamlit run app.py
```

For a fully-pinned production-style run from the flake source:

```bash
nix run .#prod
```

## Configuration

| Variable              | Default                                                                                               | Effect                   |
| --------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------ |
| `GW2_SETUP_PLANER_DB` | `/var/lib/gw2-setup-planer/db.sqlite3` if writable, else `~/.local/share/gw2-setup-planer/db.sqlite3` | SQLite database location |

The DB is created on first launch and seeded with the hardcoded defaults
from `app.py` (`DEFAULT_ROLES`, `DEFAULT_PLAYERS`, `DEFAULT_SETUP`). To wipe
state back to defaults, delete the DB file and restart.

## Deployment (NixOS)

The flake exposes a `nixosModule` (`gw2-setup-planer`). Import it from your
host config and enable:

```nix
{ config, pkgs, ... }:
{
  imports = [
    (builtins.getFlake "github:punsii/gw2_setup_planer/main").nixosModules.default
  ];

  gw2-setup-planer = {
    enable = true;
    caddy = {
      enable = true;
      domainName = "setup-planer.example.com";
    };
  };
}
```

What the module does:

- Runs the streamlit app as a `systemd` service on port `14444`, under a
  transient `DynamicUser`.
- Allocates `/var/lib/gw2-setup-planer/` (working dir + DB) and
  `/var/cache/gw2-setup-planer/` (Nix eval cache) automatically.
- Optionally fronts the service with `caddy` on the supplied `domainName`
  (ACME cert auto-fetched; set `services.caddy.email` somewhere globally).
- Restarts the service nightly at 03:30 (randomized ±30 min) via a timer.

The service pulls its sources via `nix run "github:punsii/gw2_setup_planer/main"`,
so a `git push` is the deploy step — no separate publish flow.

## Repo layout

```
app.py                  — streamlit UI (Setup / Roles / Players tabs, dialogs)
models.py               — pydantic domain models (Profession, Specialization,
                          Tag, Role, Player, Spot, Setup)
storage.py              — SQLite layer (path resolution, schema, CRUD)
assets/icons/           — 45 80×80 profession + spec icons
.streamlit/config.toml  — local-dev theme + port
flake.nix               — devShell, prod/dev apps, nixosModule wiring
nix/nixosModules/
  gw2-setup-planer.nix  — systemd service + caddy reverse proxy
```

## Discord output format

Each cell in the bottom "Copy/paste for Discord" block looks like:

```
:guardian_firebrand:`Xeonix              `
```

The `:profession_spec:` token renders as the corresponding profession icon
on a server that has those emojis (e.g. matching uploads from
`assets/icons/`). The backticks wrap the padded player name as inline
monospace so columns line up despite Discord's default proportional font.
Cells are separated by `|`; rows by newlines.

## License

ArenaNet content (profession icons) is © ArenaNet. The rest of the code is
for personal use.
