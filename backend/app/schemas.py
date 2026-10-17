from pydantic import BaseModel, Field, field_validator


class RecipeRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1, max_length=50)
    max_minutes: int = Field(default=30, ge=5, le=180)
    servings: int = Field(default=2, ge=1, le=12)
    vegetarian: bool = False
    exclusions: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("ingredients", "exclusions")
    @classmethod
    def normalize(cls, values):
        cleaned = list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))
        if any(len(value) > 80 for value in cleaned):
            raise ValueError("Ingredient names must be at most 80 characters")
        return cleaned


class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str


class Recipe(BaseModel):
    name: str
    estimated_minutes: int
    servings: int
    ingredients: list[Ingredient]
    ingredients_used: list[str]
    missing_ingredients: list[str]
    steps: list[str]


class RecipeResponse(BaseModel):
    recipes: list[Recipe]
    message: str


class Detection(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    box: tuple[float, float, float, float]  # pixel coordinates: x1, y1, x2, y2


class DetectionResponse(BaseModel):
    detections: list[Detection]
    message: str
