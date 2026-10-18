import os
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import DetectionResponse, RecipeRequest, RecipeResponse
from app.services.detection import detect_food
from app.services.backboard import generate_recipes

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/detect", response_model=DetectionResponse)
async def detect(image: UploadFile = File(...)):
    try:
        if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(415, "Upload a JPEG, PNG, or WebP image")
        content = await image.read(10 * 1024 * 1024 + 1)
        if not content:
            raise HTTPException(400, "Image is empty")
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "Image must be 10 MB or smaller")
        return await detect_food(content)
    finally:
        await image.close()


@router.post("/recipes", response_model=RecipeResponse)
def recipes(request: RecipeRequest):
    if not request.ingredients:
        raise HTTPException(422, "Enter at least one ingredient")
    return generate_recipes(request)


def _cors_origins() -> list[str]:
    origins = {os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")}
    if os.getenv("VERCEL_URL"):
        origins.add(f"https://{os.getenv('VERCEL_URL')}")
    if os.getenv("VERCEL_PROJECT_PRODUCTION_URL"):
        origins.add(f"https://{os.getenv('VERCEL_PROJECT_PRODUCTION_URL')}")
    return sorted(origins)


app = FastAPI(title="PantryPlay API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
app.include_router(router, prefix="/api")
