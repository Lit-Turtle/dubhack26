# PantryPlay

DubHacks ’26 starter: confirm pantry ingredients and find meals with the least extra shopping.

## Structure

- `frontend/` — React + Vite; pantry editor, image upload, preferences, recipe cards and instructions.
- `backend/app/main.py` — FastAPI routes and CORS.
- `backend/app/schemas.py` — request and response contracts.
- `backend/app/services/detection.py` — YOLO integration placeholder.
- `backend/app/services/recipes.py` — sample recipe fallback.
- `backend/app/services/backboard.py` — Backboard REST calls, generated recipe validation, and graceful fallback.
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
2. Configure Backboard as described below. Broaden ingredient aliases and dietary validation before relying on generated recipes for strict dietary needs.
3. Add ingredient aliases, richer dietary validation, pantry persistence, and favorites as needed.

No AI credentials or database are required for this starter. Recipe matching uses exact ingredient names and a small vegetarian catalog. Exclusions are not an allergy safety system. Cooking times assume cooked rice is already available; ingredient quantities are recipe requirements, not photo measurements. Photos are not persisted. This is a local-development skeleton, not a production deployment.


## Enable Backboard recipes

Create or rotate your key in the Backboard dashboard, then add it to `backend/.env` locally (never to the frontend or a committed file):

```dotenv
BACKBOARD_API_KEY=your_new_key_here
BACKBOARD_PROVIDER=openai
BACKBOARD_MODEL=gpt-4o
```

Restart the backend using `uvicorn app.main:app --reload --env-file .env`.
Install updated dependencies with `pip install -r requirements-dev.txt` first.
The provider/model defaults match Backboard's documented defaults. You can select a cheaper JSON-capable model from Backboard's model catalog and change both variables. Confirm its current price in Backboard before using it extensively.

Each Find recipes request makes one Backboard REST call to `POST /threads/messages`, with JSON output requested, memory and web search disabled, and a fresh conversation. Requests time out after 60 seconds of read inactivity and are not retried automatically. Backboard may still bill a timed-out request. Pantry data is sent to Backboard; photos still use the local detection placeholder.

The backend validates quantities, required fields, servings, cooking time, exact-name exclusions, and the model's vegetarian flag. It recomputes available/missing lists instead of trusting the model and sorts by missing count. Semantic dietary validation (including hidden allergens, synonyms, or ingredients mentioned only in steps) is not guaranteed. If the key is absent, the request fails, or the result fails validation, the UI explicitly labels the sample fallback. No raw upstream errors or credentials are returned to the browser.

Integration tests use mocked HTTP responses and spend no credits. A live call with your local key is still needed to verify your account/model access.

API reference: https://docs.backboard.io/concepts/messages
