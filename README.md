# PantryPlay

DubHacks ’26 starter: confirm pantry ingredients and find meals with the least extra shopping.

## Structure

- `frontend/` — React + Vite; pantry editor, image upload, preferences, recipe cards and instructions.
- `backend/app/main.py` — FastAPI routes and CORS.
- `backend/app/schemas.py` — request and response contracts.
- `backend/app/services/detection.py` — YOLO integration placeholder.
- `backend/app/services/recipes.py` — working sample recipe matching; future LLM integration point.
- `backend/app/data/recipes.json` — starter recipes for two servings, scaled by the API.
- `backend/tests/` — API contract and recipe matching checks.

## Run locally

Use Python 3.11+ and Node.js 22. In one terminal:

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --env-file .env
```

In another terminal:

```sh
cd frontend
npm install
cp .env.example .env
npm run dev -- --port 5173 --strictPort
```

Open http://localhost:5173. API documentation: http://localhost:8000/docs.

## Verify

```sh
cd backend
source .venv/bin/activate
python -m pytest
```

```sh
cd frontend
npm run build
```

## API

- `GET /health` — readiness check.
- `POST /detect` — multipart `image` upload (JPEG/PNG/WebP, max 10 MB); currently returns no detections and an explicit placeholder message. MIME type and size are checked; decoding will belong in the detector.
- `POST /recipes` — JSON with `ingredients`, `max_minutes`, `servings`, `vegetarian`, and `exclusions`. Returns up to three recipes, required quantities, pantry matches, missing ingredients, and steps.

Example request:

```json
{"ingredients":["rice","egg","carrot","broccoli"],"max_minutes":30,"servings":2,"vegetarian":true,"exclusions":[]}
```

## Next integration steps

1. Add YOLO inference to `detect_food`; return labels, confidence, and pixel bounding boxes. Add an image preview and box overlay to the UI. Do not infer weight or freshness.
2. Replace catalog matching with an LLM call in `suggest_recipes`. Validate generated data with the response schemas and recompute pantry/missing lists in code. Keep API keys on the backend.
3. Add ingredient aliases, richer dietary validation, pantry persistence, and favorites as needed.

No AI credentials or database are required for this starter. Recipe matching uses exact ingredient names and a small vegetarian catalog. Exclusions are not an allergy safety system. Cooking times assume cooked rice is already available; ingredient quantities are recipe requirements, not photo measurements. Photos are not persisted. This is a local-development skeleton, not a production deployment.
