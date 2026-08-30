# Taverna — The Living Rusted Tankard

A text-based RPG set in a single fantasy tavern. You stay in one room; the world arrives through the door. NPCs, bounties, news and items are driven by an LLM against a persisted game state.

## What's here

- `run_api.py` — FastAPI server for the web interface.
- `demo_3d_server.py` — a Three.js view of the tavern, served separately.
- `data/` — the world as JSON: `npcs.json`, `items.json`, `bounties.json`, `news.json`.
- `docs/` — `WEB_README.md` (interface guide), `OBSERVERS.md`, API documentation notes.
- `.github/workflows/quality.yml`, `.pre-commit-config.yaml` — lint and quality gates.

## Running it

```bash
python run_api.py                          # defaults to port 8001
python run_api.py --host 127.0.0.1 --port 8002 --reload
```

## Status

Playable. Note that the repository root also holds roughly thirty planning and analysis documents (roadmaps, sprint trackers, swarm analyses) that accumulated during development — they are historical notes, not current design docs. `TODO.md` is the one worth reading.
