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

## Deploy on Vercel

The repo root `vercel.json` deploys the Vite frontend and FastAPI backend as one project. Public URLs:

- `/` — frontend
- `/api/health`, `/api/recipes`, `/api/detect` — backend

1. Import [this GitHub repo](https://github.com/Lit-Turtle/dubhack26) into [Vercel](https://vercel.com/new). Keep the project root at the repository root.
2. In the Vercel project, add these environment variables (Production and Preview):

```dotenv
BACKBOARD_API_KEY=your_new_key_here
BACKBOARD_PROVIDER=openrouter
BACKBOARD_MODEL=openai/gpt-4o-mini
FRONTEND_ORIGIN=https://your-app.vercel.app
```

3. Deploy. After the first deploy, set `FRONTEND_ORIGIN` to the real `*.vercel.app` URL (or your custom domain) and redeploy.
4. Optional custom domain: Project → Settings → Domains.

Do not add `requirements-yolo.txt` or PyTorch on Vercel. Those packages are too large for a serverless function, so photo detection will fall back to manual ingredients. Recipe generation uses Backboard plus the sample catalog.

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


## Focused 30-ingredient training

The retained full dataset is `backend/datasets/pantry-evaluation-77h3_knk/` (172 classes).
The completed quick-trial candidate and results remain in
`backend/models/experiments/quick-food-20261017-215150/`.
Older source datasets and abandoned trials were moved outside the repository to
`/Users/canbo/dubhack26-recovery-20261017-221124/`; its `manifest.json` records their original paths.
This archive is local to the original Mac, not included in Git.

The focused dataset includes onion, tomato, potato, carrot, broccoli, spinach,
lettuce, cabbage, cucumber, pepper, garlic, mushroom, eggplant, corn, peas, eggs,
chicken, beef, pork, flour, oil, cheese, milk, butter, rice, bread, apple, banana,
lemon, and beans. These are a practical cooking list, not a statistical usage ranking.

From `backend`, with the virtual environment active:

```sh
python train_food30.py --prepare-only
python train_food30.py --prepared --hours 2 --target 0.8
```

Preparation refuses to overwrite an existing dataset. It preserves the original
172-class dataset, filters invalid boxes, maps labels by class name, and removes
exact duplicate image files across splits, giving test and validation priority.
Near-duplicate photographs and prior exposure during the teammate's original
training have not been ruled out. Every target class must have examples in each split.
Training samples up to 150 images per class, keeping all selected ingredient boxes
in each chosen image; shared images can increase individual class counts.

The target is **AP50 >= 0.80 for every ingredient**, not an 80% average or a
prediction-confidence threshold. Training stops on the validation target or the
budget; the final selected checkpoint is then evaluated once on the test split.
The two-hour limit includes final evaluation, with time reserved for it.
An interrupted or timed-out run may have checkpoints but no final test results.
No score is guaranteed, and the application model is never automatically replaced.
Sparse test classes (especially oil) need additional independently labeled examples
before their scores should be treated as reliable. The script reports classes with
fewer than 20 test images; 20 is only a support warning threshold, not a guarantee.

Find progress, per-class history, selected weights, and final results under
`backend/models/food30-runs/<run>/`. Read `status.json` for the run state and
`test_AP50` after completion. Dataset manifests and support counts are under
`backend/datasets/food30/`. Generated data and checkpoints are ignored by Git;
share weights separately if teammates need them.


## Active detector and manual photo test

The API now defaults to the completed **30-ingredient model**, bundled as
`backend/models/food30/best.onnx`. The CPU inference runtime is included in
`backend/requirements.txt`; production inference does not need PyTorch or
Ultralytics. The matching `best.pt` is retained for further training. The original
172-class checkpoint remains in `backend/models/runs/food/weights/best.pt`.
The 30-class list does **not** include grapes. Empty detections are possible and
manual ingredient entry remains necessary. Measured test results and class names
are in `backend/models/food30/model-info.json`; this model did not reach 80% for all classes.

From the repository root on macOS:

```sh
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --env-file .env --port 8000
```

Set `YOLO_MODEL=food30/best.onnx` in `backend/.env`. Stop any old server with
Ctrl+C before restarting so it reloads the environment and model.
Open `http://localhost:8000/docs`, expand **POST /api/detect**, click **Try it out**,
choose a JPEG/PNG/WebP, then **Execute**. A successful response includes a
`detections` list with `label`, `confidence`, and `box`. An empty list with a
no-detections message means inference ran but found nothing above the threshold.
HTTP 503 means the model/runtime is unavailable.

Alternatively, from another terminal:

```sh
curl http://localhost:8000/api/health
curl -F 'image=@/absolute/path/to/photo.jpg' http://localhost:8000/api/detect
```

For the deployed website, use the same endpoints at
`https://www.picadish.photo/api/health` and `https://www.picadish.photo/api/detect`.
Use photos below 4 MB to fit the platform upload limit. Production Vite builds use
`VITE_API_URL=/api`, and Vercel routes those requests to FastAPI. If a Vercel
`YOLO_MODEL` environment override is configured, change it to
`food30/best.onnx` and redeploy. Backend keys belong only in backend environment
variables, never in `VITE_*` variables. Training data and experiment folders are
excluded from deployment; the ONNX runtime model is included.
