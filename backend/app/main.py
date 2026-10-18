import os
from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import DetectionResponse, RecipeRequest, RecipeResponse
from app.services.detection import detect_food
from app.services.backboard import generate_recipes

router = APIRouter()
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/pjpeg", "image/png", "image/webp", "application/octet-stream", ""}


def _image_kind(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    if len(content) > 12 and content[4:8] == b"ftyp" and content[8:12] in {b"heic", b"heif", b"mif1", b"msf1"}:
        return "heic"
    return None


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/detect", response_model=DetectionResponse)
async def detect(image: UploadFile = File(...)):
    try:
        content = await image.read(10 * 1024 * 1024 + 1)
        if not content:
            raise HTTPException(400, "Image is empty")
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, "Image must be 10 MB or smaller")
        kind = _image_kind(content)
        declared = (image.content_type or "").split(";")[0].strip().lower()
        if kind == "heic":
            raise HTTPException(415, "HEIC photos are not supported. Save or export the picture as JPEG or PNG, then upload it.")
        if kind is None and declared not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(415, "Upload a JPEG, PNG, or WebP image")
        return await detect_food(content)
    finally:
        await image.close()


@router.post("/recipes", response_model=RecipeResponse)
def recipes(request: RecipeRequest):
    if not request.ingredients:
        raise HTTPException(422, "Enter at least one ingredient")
    return generate_recipes(request)


def _cors_origins() -> list[str]:
    origins = {
        os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    }
    if os.getenv("VERCEL_URL"):
        origins.add(f"https://{os.getenv('VERCEL_URL')}")
    if os.getenv("VERCEL_PROJECT_PRODUCTION_URL"):
        origins.add(f"https://{os.getenv('VERCEL_PROJECT_PRODUCTION_URL')}")
    return sorted(origin for origin in origins if origin)


app = FastAPI(title="PantryPlay API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(router, prefix="/api")
