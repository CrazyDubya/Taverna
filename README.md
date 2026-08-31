# Taverna — The Living Rusted Tankard

A text-based RPG set in a fantasy tavern, with LLM-driven interaction over a persisted game state.

## What's here

- `living_rusted_tankard/` — the game package. `START_GAME.py` is the entry point; `api/routers/game.py` serves it; `core/async_llm_optimization.py` handles model calls.
- `run_api.py` — FastAPI server for the web interface.
- `demo_3d_server.py` — a Three.js view, served separately.
- `data/` — world content as JSON: `npcs.json`, `items.json`, `bounties.json`, `news.json`.
- `docs/WEB_README.md` — how to run and use the web interface.
- `.github/workflows/quality.yml`, `.pre-commit-config.yaml` — lint and quality gates.

## Running it

From `docs/WEB_README.md`:

```bash
python run_api.py                                        # port 8001
python run_api.py --host 127.0.0.1 --port 8002 --reload
```

## A note on the repository root

Roughly thirty planning and analysis documents sit at the root — roadmaps, sprint trackers, swarm analyses, phase summaries. They accumulated during development and were not pruned. `TODO.md` and `docs/` are the current material; the rest is history.
