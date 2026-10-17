# PantryPlay

DubHacks ’26 starter: confirm pantry ingredients and find meals with the least extra shopping.

## Structure

- `frontend/` — React + Vite; pantry editor, image upload, preferences, recipe cards and instructions.
- `backend/app/main.py` — FastAPI routes and CORS.
- `backend/app/schemas.py` — request and response contracts.
- `backend/app/services/detection.py` — YOLO inference for pantry photos.
- `backend/app/services/yolo_detector.py` — Ultralytics wrapper; loads official names or `backend/models/*.pt`.
- `backend/app/services/recipes.py` — sample recipe fallback.
- `backend/app/services/backboard.py` — Backboard REST calls, generated recipe validation, and graceful fallback.
- `backend/app/data/recipes.json` — starter recipes for two servings, scaled by the API.
- `backend/models/` — drop custom `.pt` weights here (gitignored).
- `backend/datasets/` — drop a dataset folder + YAML here when you want to train.
- `backend/run_yolo.py` — CLI detection.
- `backend/train_yolo.py` — fine-tune a local `.pt` on a dataset YAML.
- `backend/tests/` — API contract and recipe matching checks.

## Prerequisites

Install **Node.js 22** (includes npm) and **Git** on every machine. Python version depends on the CPU:

| Machine | Python for YOLO | Why |
|---|---|---|
| **Intel Mac** (`x86_64`) | **3.12 only** | PyPI has no current PyTorch wheels for 3.13+ on Intel Mac. |
| **Apple Silicon Mac** (M1/M2/M3/M4) | **3.11–3.13** | Current PyTorch wheels exist. Avoid 3.14. |
| **Windows** | **3.11 or 3.12** | Current PyTorch wheels exist. Avoid 3.14. |

Check which Mac you have:

```sh
uname -m
```

`x86_64` is Intel. `arm64` is Apple Silicon.

**Do not use Python 3.14** for YOLO. `ultralytics` needs `torch`, and 3.14 has no matching wheel.

## Run locally

### macOS — Intel

From the repository root, in one terminal:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python --version    # must print 3.12.x
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -r requirements-yolo.txt
cp -n .env.example .env
uvicorn app.main:app --reload --env-file .env
```

If `.venv` was created with 3.13 or 3.14, delete it first: `rm -rf .venv`.

### macOS — Apple Silicon (M-series)

From the repository root, in one terminal:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python --version    # 3.11, 3.12, or 3.13 — not 3.14
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -r requirements-yolo.txt
cp -n .env.example .env
uvicorn app.main:app --reload --env-file .env
```

`python3.13` is fine on Apple Silicon if that is what you have installed.

### Windows / PowerShell

Install [Python 3.12](https://www.python.org/downloads/) (check **Add python.exe to PATH**), Node.js 22, and Git for Windows, then reopen PowerShell.

If you have not cloned the repository yet:

```powershell
git clone https://github.com/Lit-Turtle/dubhack26.git
Set-Location .\dubhack26
```

Confirm versions:

```powershell
py -3.12 --version
node --version
npm.cmd --version
```

Start the backend from the repository root. Always call the venv Python so packages do not install into system Python:

```powershell
Set-Location .\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-yolo.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env
```

If `py -3.12` is unavailable but `python --version` reports 3.11 or 3.12, use `python -m venv .venv` instead.

### Frontend (all platforms)

Keep the backend running. In a **second** terminal from the repository root:

**macOS**

```sh
cd frontend
npm install
cp -n .env.example .env
npm run dev -- --port 5173 --strictPort
```

**PowerShell**

```powershell
Set-Location .\frontend
npm.cmd install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm.cmd run dev -- --port 5173 --strictPort
```

`npm.cmd` avoids PowerShell blocking the `npm.ps1` wrapper.

Open http://localhost:5173. API documentation: http://localhost:8000/docs. Stop either server with `Ctrl+C`.

To enable Backboard, edit `backend/.env` and follow [Enable Backboard recipes](#enable-backboard-recipes). Restart the backend after saving.

## YOLO

Core API tests run without YOLO. Live photo detection needs `requirements-yolo.txt` in a venv that matches the table above.

Confirm the stack after install:

```sh
python -c "import torch, ultralytics; print(torch.__version__, ultralytics.__version__)"
```

### CLI smoke test

From `backend/` with the venv active (macOS) or using the venv Python (PowerShell):

```sh
python run_yolo.py --source https://ultralytics.com/images/bus.jpg --no-save
```

```powershell
.\.venv\Scripts\python.exe run_yolo.py --source https://ultralytics.com/images/bus.jpg --no-save
```

The first run may download official weights such as `yolo26n.pt`. You should get JSON detections.

### Use a custom `.pt`

A `.pt` file is **model weights**, not a dataset. Images and labels live in a separate dataset folder plus a YAML file.

1. Copy the file into `backend/models/` (that folder is in `.gitignore`, so weights stay local):

```sh
cp ~/Downloads/your-model.pt backend/models/food.pt
```

```powershell
Copy-Item $HOME\Downloads\your-model.pt .\backend\models\food.pt
```

2. Point the API at it in `backend/.env`:

```dotenv
YOLO_MODEL=food.pt
```

Restart uvicorn. Detection also accepts an official Ultralytics name (`yolo26n.pt`) or an absolute path.

### Share weights with the agent (so they can be inspected or used for training)

Cursor cannot see files only on your Desktop. Use one of these:

1. **Best:** copy the `.pt` into `backend/models/` as above, then tell the agent the filename.
2. **Chat:** drag the `.pt` from Finder/Explorer onto this Cursor chat. Large files may fail; then use option 1.
3. **Dataset (needed to train, not just to run):** copy the dataset folder (images, labels, and the `.yaml`) into `backend/datasets/` and say which YAML to use.

Weights are gitignored on purpose. Do not commit `.pt` files.

### Train / fine-tune

Training needs **starting weights** (your `.pt`) **and** a dataset YAML. `coco8.yaml` is Ultralytics’ tiny built-in set — use it only to prove the pipeline works.

From `backend/` with YOLO installed:

```sh
python train_yolo.py --model food.pt --data coco8.yaml --epochs 3
```

```powershell
.\.venv\Scripts\python.exe train_yolo.py --model food.pt --data coco8.yaml --epochs 3
```

For a real food model, pass your dataset YAML:

```sh
python train_yolo.py --model food.pt --data datasets/food.yaml --epochs 50
```

Best weights land at `backend/models/runs/food/weights/best.pt`. Set `YOLO_MODEL` to that path (or copy `best.pt` into `backend/models/`).

## Verify

### macOS

From the repository root, in separate terminals:

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
- `POST /detect` — multipart `image` upload (JPEG/PNG/WebP, max 10 MB); runs local YOLO inference and returns labels, confidence, and pixel bounding boxes.
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
BACKBOARD_PROVIDER=openai
BACKBOARD_MODEL=gpt-4o
```

Install API dependencies first (`pip install -r requirements-dev.txt`). Restart the backend with `uvicorn app.main:app --reload --env-file .env`.

The provider/model defaults match Backboard's documented defaults. You can select a cheaper JSON-capable model from Backboard's model catalog and change both variables. Confirm its current price in Backboard before using it extensively.

Each Find recipes request makes one Backboard REST call to `POST /threads/messages`, with JSON output requested, memory and web search disabled, and a fresh conversation. Requests time out after 60 seconds of read inactivity and are not retried automatically. Backboard may still bill a timed-out request. Pantry data is sent to Backboard; photos use the local YOLO detector.

The backend validates quantities, required fields, servings, cooking time, exact-name exclusions, and the model's vegetarian flag. It recomputes available/missing lists instead of trusting the model and sorts by missing count. Semantic dietary validation (including hidden allergens, synonyms, or ingredients mentioned only in steps) is not guaranteed. If the key is absent, the request fails, or the result fails validation, the UI explicitly labels the sample fallback. No raw upstream errors or credentials are returned to the browser.

Integration tests use mocked HTTP responses and spend no credits. A live call with your local key is still needed to verify your account/model access.

API reference: https://docs.backboard.io/concepts/messages
