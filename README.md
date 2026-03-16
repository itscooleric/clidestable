# clidestable 🐴

> The stable where your dales live — VPS-side session server for [clidesdale](https://github.com/itscooleric/clidesdale).

A lightweight server that manages **stalls** (observable shell sessions) on a VPS. Each stall gets a web terminal (ttyd) and an activity log. One port, multiple sessions, zero complexity.

## Quick Start

```bash
pip install -e .
clidestable serve                    # start on port 7690
clidestable serve --port 7690 --bind 100.x.x.x  # Tailscale only
```

Then open `http://your-vps:7690` to see the dashboard.

## What it does

- Manages named **stalls** (shell sessions on the VPS)
- Each stall gets a web terminal via ttyd (subpath routed)
- Activity logs from clidesdale agents are visible in the UI
- REST API for stall management

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
│  ┌────────┐  ┌────────┐  ┌────────┐     │
│  │ edge   │  │ edge2  │  │ edge3  │     │
│  │ :7701  │  │ :7702  │  │ :7703  │     │
│  │ (ttyd) │  │ (ttyd) │  │ (ttyd) │     │
│  └────────┘  └────────┘  └────────┘     │
└──────────────────────────────────────────┘
```

## Requirements

- Python 3.10+
- `ttyd` installed on the VPS
- That's it
