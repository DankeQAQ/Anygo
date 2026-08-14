# Anygo Project Structure

Anygo is split into a Vue mobile-first frontend and a FastAPI multi-agent backend.

## Main Areas

```text
Anygo-main/
├── frontend/                 # Vue 3 app, mobile UI, API client
│   ├── src/views/            # Main screens: Landing and Result
│   ├── src/services/         # API calls and runtime settings
│   ├── src/types/            # Shared TypeScript interfaces
│   ├── src/i18n/             # zh / en / ja text
│   └── src/styles/           # Global app styling
├── backend/                  # FastAPI service and agent orchestration
│   ├── app/agents/           # anygo_agent.py multi-agent planner
│   ├── app/api/routes/       # API routes for trip, settings, POI, chat, maps
│   ├── app/services/         # LLM, maps, XHS, graph, chat services
│   └── app/models/           # Pydantic schemas
├── docs/                     # Project documentation
├── .vscode/                  # VS Code tasks, launch config, recommendations
├── docker-compose.yaml       # Container deployment entry
└── README.md                 # User-facing project guide
```

## Files You Usually Edit

- `frontend/src/views/Landing.vue`: home form, mobile glass UI, generation progress.
- `frontend/src/views/Result.vue`: itinerary result screen.
- `frontend/src/services/api.ts`: frontend API base URL, settings API, trip generation.
- `backend/app/agents/anygo_agent.py`: multi-agent planning flow.
- `backend/app/services/xhs_service.py`: Xiaohongshu search, note extraction, photo lookup.
- `backend/app/config.py`: runtime settings and environment variable handling.

## Files You Should Not Commit

- `frontend/node_modules/`
- `frontend/dist/`
- `backend/runtime_settings.json`
- `backend/data/`
- `__pycache__/`
- `.DS_Store`
- local `.zip` archives

These are hidden or ignored by the VS Code and Git settings.

## VS Code Tasks

Open the command palette and run `Tasks: Run Task`:

- `Backend: install`
- `Backend: dev`
- `Frontend: dev`
- `Frontend: build`

For debugging, use the `Anygo Backend` launch configuration.
