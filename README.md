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

Install Python 3.11–3.13 (YOLO/PyTorch wheels are not available on 3.14 yet), Node.js 22 (includes npm), and Git. Clone this repository or open your existing checkout.

### macOS / Linux

Starting from the repository root, run in one terminal:

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -r requirements-yolo.txt
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

### Windows / PowerShell

Install Python 3.11+, Node.js 22, and Git for Windows, then reopen PowerShell so the commands are available. If you have not cloned the repository yet:

```powershell
git clone https://github.com/Lit-Turtle/dubhack26.git
Set-Location .\dubhack26
```

If you already have the repository, open PowerShell in its root folder instead. Check your installations:

```powershell
py --version
node --version
npm.cmd --version
```

Start the backend from the repository root:

```powershell
Set-Location .\backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
pip install -r requirements-yolo.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env
```

If `py` is unavailable but `python --version` reports Python 3.11 or newer, use `python -m venv .venv` instead. These commands call the virtual environment's Python directly, so activation and execution-policy changes are unnecessary.

Keep the backend running. Open a **second PowerShell terminal in the repository root** and start the frontend:

```powershell
Set-Location .\frontend
npm.cmd install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm.cmd run dev -- --port 5173 --strictPort
```

Using `npm.cmd` avoids PowerShell blocking the `npm.ps1` wrapper. The environment-file commands preserve any existing API key or configuration.

Open http://localhost:5173. API documentation: http://localhost:8000/docs. Stop either server with `Ctrl+C` in its terminal.

To enable Backboard, edit `backend\.env` and follow [Enable Backboard recipes](#enable-backboard-recipes) below. After saving, stop and restart the backend with the same `python.exe -m uvicorn` command above.

## Verify

### macOS / Linux

Run each block from the repository root in a separate terminal:

```sh
cd backend
source .venv/bin/activate
python -m pytest
```

```sh
cd frontend
npm run build
```

### Windows / PowerShell

Run each block from the repository root in a separate terminal:

```powershell
Set-Location .\backend
.\.venv\Scripts\python.exe -m pytest
```

```powershell
Set-Location .\frontend
npm.cmd run build
```

## API

- `GET /health` — readiness check.
- `POST /detect` — multipart `image` upload (JPEG/PNG/WebP, max 10 MB); runs local YOLO26 inference and returns labels, confidence, and pixel bounding boxes. MIME type and size are checked before decode.
- `POST /recipes` — JSON with `ingredients`, `max_minutes`, `servings`, `vegetarian`, and `exclusions`. Returns up to three recipes, required quantities, pantry matches, missing ingredients, and steps.

Example request:

```json
{"ingredients":["rice","egg","carrot","broccoli"],"max_minutes":30,"servings":2,"vegetarian":true,"exclusions":[]}
```

## Next integration steps

1. Add an image preview and box overlay to the UI. Tune `YOLO_MODEL`, `YOLO_CONF`, and `YOLO_IMGSZ` in `backend/.env` if needed. Do not infer weight or freshness.
2. Configure Backboard as described below. Broaden ingredient aliases and dietary validation before relying on generated recipes for strict dietary needs.
3. Add ingredient aliases, richer dietary validation, pantry persistence, and favorites as needed.

No AI credentials or database are required for this starter. Recipe matching uses exact ingredient names and a small vegetarian catalog. Exclusions are not an allergy safety system. Cooking times assume cooked rice is already available; ingredient quantities are recipe requirements, not photo measurements. Photos are not persisted. This is a local-development skeleton, not a production deployment.


## Enable Backboard recipes

Create or rotate your key in the Backboard dashboard, then add it to `backend/.env` locally (never to the frontend or a committed file):

```dotenv
BACKBOARD_API_KEY=your_new_key_here
BACKBOARD_PROVIDER=openrouter
BACKBOARD_MODEL=openai/gpt-4o-mini
```

Restart the backend using `uvicorn app.main:app --reload --env-file .env`.
Install updated dependencies with `pip install -r requirements-dev.txt
pip install -r requirements-yolo.txt` first.
The provider/model defaults follow Backboard's OpenRouter quickstart. You can change both variables to another JSON-capable model from Backboard's catalog. Confirm its current price in Backboard before using it extensively.

Each Find recipes request calls `POST /threads/messages` with the pantry and preferences, JSON output requested, memory and web search disabled, and a fresh conversation. If JSON mode fails, the backend tries once without it. Requests time out after 60 seconds of read inactivity and are not retried automatically. Backboard may still bill a timed-out request. Pantry data is sent to Backboard; photos still use the local detection placeholder.

The backend validates quantities, required fields, servings, cooking time, exact-name exclusions, and the model's vegetarian flag. It recomputes available/missing lists instead of trusting the model and sorts by missing count. Semantic dietary validation (including hidden allergens, synonyms, or ingredients mentioned only in steps) is not guaranteed. If the key is absent, the request fails, or the result fails validation, the UI explicitly labels the sample fallback. No raw upstream errors or credentials are returned to the browser.

Integration tests use mocked HTTP responses and spend no credits. A live call with your local key is still needed to verify your account/model access.

API reference: https://docs.backboard.io/concepts/messages
