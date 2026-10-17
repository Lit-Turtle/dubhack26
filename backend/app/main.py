import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import DetectionResponse, RecipeRequest, RecipeResponse
from app.services.detection import detect_food
from app.services.backboard import generate_recipes

app = FastAPI(title="PantryPlay API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")],
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/detect", response_model=DetectionResponse)
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


@app.post("/recipes", response_model=RecipeResponse)
def recipes(request: RecipeRequest):
    if not request.ingredients:
        raise HTTPException(422, "Enter at least one ingredient")
    return generate_recipes(request)
