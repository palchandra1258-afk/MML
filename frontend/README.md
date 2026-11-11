# MCP-RI Frontend

MCP-RI (Multimodal Cognitive Perception and Representation Intelligence) is a research prototype for persistent, evidence-linked learner-state estimation, explainable representation planning, and learning-trajectory orchestration. The frontend is planned as two experiences: a focused learner workspace and a research console for inspecting evidence and system decisions. Research artifacts are not equivalent to a production tutoring service: current cognitive categories are provisional behavioral rules, delivery capabilities are unavailable, the default concept-dependency registry is empty, and Phase 13 history is in-memory in the Python implementation.

## Project status

This directory currently contains the Next.js starter application and this product/architecture plan. The documents in [`docs/`](docs/) define the intended information architecture, user journeys, screen requirements, data boundaries, and milestones. F0 planning is complete when reviewed; F1 implementation must wait for review and approval of these documents. No authentication is planned for this stage.

## Stack and setup

The installed project uses Next.js 16.4.6 App Router, React 19.3.0, TypeScript 5, Tailwind CSS 4.3.3, and ESLint 9. The package currently has no charting, icon, query-cache, form, or component-library dependency. Keep the dependency surface small and add a package only when a defined interaction requires it.

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Available scripts are `dev`, `build`, `start`, and `lint`. No backend is currently configured for this frontend.

## Planned architecture

Use App Router route groups/layouts for a shared shell, domain feature modules for learner state, cognitive estimates, representations, trajectories, diversions, and evidence, and a typed API client boundary in `src/lib/api/`. Keep route components focused on composing feature components. Keep presentation labels separate from raw research codes. See [`FRONTEND_TECHNICAL_ARCHITECTURE.md`](docs/FRONTEND_TECHNICAL_ARCHITECTURE.md) and [`COMPONENT_INVENTORY.md`](docs/COMPONENT_INVENTORY.md).

## Backend integration

A separate workstream owns Phase 14 (FastAPI, endpoints, persistence, and OpenAPI). Do not infer or publish an API contract from Python schemas. Once the backend OpenAPI document is available, generate or hand-maintain transport types from that authoritative contract, configure `NEXT_PUBLIC_API_BASE_URL` by environment, and map transport data to frontend view models in the API layer. Until then, any demo data must be explicitly marked synthetic and isolated from API-backed records. Details: [`API_INTEGRATION_STRATEGY.md`](docs/API_INTEGRATION_STRATEGY.md), [`MOCK_DATA_STRATEGY.md`](docs/MOCK_DATA_STRATEGY.md).

## Scientific boundary

EdNet-derived records describe submitted response correctness, interaction history, and dataset skill tags, not understanding, mastery, confusion, or learner intent. Cognitive-state records are provisional estimates without ground truth. Representation plans are recommendations only; all eight delivery capabilities are unavailable in the current registry. Dataset skill tags do not establish validated concepts or prerequisites. Synthetic journey examples must never be represented as actual learners or observations. Refer to [`FRONTEND_LIMITATIONS_AND_ASSUMPTIONS.md`](docs/FRONTEND_LIMITATIONS_AND_ASSUMPTIONS.md).
