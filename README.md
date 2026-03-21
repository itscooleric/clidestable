# clidestable

```text
   ██████╗██╗     ██╗██████╗ ███████╗
  ██╔════╝██║     ██║██╔══██╗██╔════╝
  ██║     ██║     ██║██║  ██║█████╗        ───
  ██║     ██║     ██║██║  ██║██╔══╝          \
  ╚██████╗███████╗██║██████╔╝███████╗         \    ╱▔▔▔╲
   ╚═════╝╚══════╝╚═╝╚═════╝ ╚══════╝         ╲__╱ ● ● ╲
  ███████╗████████╗ █████╗ ██████╗ ██╗     ███████╗│  ▽  │
  ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║     ██╔════╝ ╲───╱
  ███████╗   ██║   ███████║██████╔╝██║     █████╗   ╱   ╲
  ╚════██║   ██║   ██╔══██║██╔══██╗██║     ██╔══╝  ╱ ┃ ┃ ╲
  ███████║   ██║   ██║  ██║██████╔╝███████╗███████╗╱  ┃ ┃  ╲
  ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝

  the stable where your dales live               v0.1
  ────────────────────────────────────────────────────
  dashboard · stalls · split view · activity logs
  ────────────────────────────────────────────────────
```

> VPS-side session server for [clidesdale](https://github.com/itscooleric/clidesdale).

A lightweight server that manages **stalls** (observable shell sessions) on a VPS. Each stall gets a web terminal (ttyd) and an activity log. One port, multiple sessions, zero complexity.

## Quick Start

```bash
pip install -e .
clidestable serve                    # start on port 7690
clidestable serve --port 7690 --bind 100.x.x.x  # Tailscale only
```

Then open `http://your-vps:7690` to see the dashboard.

## What it does

- Manages named **stalls** (observable agent sessions on the VPS)
- Each stall gets a web terminal via [ttyd](https://github.com/tsl0922/ttyd) that streams the activity log in real time
- Activity logs from [clidesdale](https://github.com/itscooleric/clidesdale) agents are visible in the dashboard
- Split view for watching multiple agents side-by-side
- REST API for stall management

## How it works

1. **clidesdale** agents run commands on the VPS via `sdale exec` / `sdale run`
2. Every command + output is appended to `/opt/stacks/.sdale-<name>.log`
3. **clidestable** creates stalls — each stall spawns a ttyd instance that `tail -f`'s the corresponding log file
4. You see agent activity streaming in your browser in real time

```
  clidesdale (client)              clidestable (server)
  ─────────────────              ───────────────────────
  sdale exec edge "cmd"   ──>   .sdale-edge.log   ──>  ttyd (tail -f)  ──>  browser
  sdale exec edge2 "cmd"  ──>   .sdale-edge2.log  ──>  ttyd (tail -f)  ──>  browser
```

No tmux nesting, no SSH tunnels — just log files and ttyd.

## Concepts

| Term | What |
|------|------|
| **clidesdale** | The CLI client (sends commands to dales) |
| **clidestable** | This server (where the dales live) |
| **stall** | One session/shell (where one dale works) |

## API

```
GET    /api/stalls              # list stalls
POST   /api/stalls              # create stall {"name": "edge"}
DELETE /api/stalls/{name}       # destroy stall
GET    /api/stalls/{name}/log   # get activity log
```

## Architecture

```
┌──────────────────────────────────────────┐
│  clidestable server (port 7690)          │
│                                          │
│  /              → dashboard (stall list) │
│  /stall/edge    → ttyd terminal          │
│  /stall/edge2   → ttyd terminal          │
│  /log/edge      → activity log viewer    │
│                                          │
│  ┌────────┐  ┌────────┐  ┌────────┐      │
│  │ edge   │  │ edge2  │  │ edge3  │      │
│  │ :7701  │  │ :7702  │  │ :7703  │      │
│  │ (ttyd) │  │ (ttyd) │  │ (ttyd) │      │
│  └────────┘  └────────┘  └────────┘      │
└──────────────────────────────────────────┘
```

## Docker

```bash
docker compose up -d --build
```

Configure in `.env`:
```bash
STABLE_BIND=100.x.x.x   # Tailscale IP (default: 0.0.0.0)
STABLE_PORT=7690         # Dashboard port
STABLE_DATA_DIR=/opt/stacks  # Shared with clidesdale agent logs
```

## Web UI

| Page | What |
|------|------|
| `/` | Dashboard — create/destroy stalls, quick links |
| `/view` | Split view — side-by-side terminals for all stalls |
| `/stall/<name>/` | Single stall terminal (live agent activity stream) |
| `/log/<name>` | Activity log viewer (auto-refreshes every 3s) |

## Requirements

- Python 3.10+
- `ttyd` (included in Docker image)

## Ecosystem

| Project | What |
|---------|------|
| [clide](https://github.com/itscooleric/clide) | CLI Development Environment — sandboxed terminal for AI agents |
| [clidesdale](https://github.com/itscooleric/clidesdale) | CLI client — SSH access to remote VPSes for agents |
| **clidestable** | This server — dashboard, stall management, split terminal view |

## License

MIT
