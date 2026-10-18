from pydantic import BaseModel, Field, field_validator

DIETS = ("vegetarian", "vegan", "pescatarian", "halal", "kosher")
ALLERGIES = ("peanuts", "tree nuts", "dairy", "lactose", "gluten", "eggs", "soy", "fish", "shellfish", "sesame")
NUTRITION_GOALS = ("high-protein", "low-carb", "keto", "low-sodium", "low-sugar", "low-fat", "calorie-conscious")
OTHER_PREFERENCES = ("dairy free", "gluten free", "paleo")


class RecipeRequest(BaseModel):
    ingredients: list[str] = Field(min_length=1, max_length=50)
    max_minutes: int = Field(default=30, ge=5, le=180)
    servings: int = Field(default=2, ge=1, le=12)
    vegetarian: bool = False
    diet: str = ""
    allergies: list[str] = Field(default_factory=list, max_length=20)
    nutrition_goals: list[str] = Field(default_factory=list, max_length=20)
    other_preferences: list[str] = Field(default_factory=list, max_length=20)
    exclusions: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("ingredients", "exclusions")
    @classmethod
    def normalize(cls, values):
        cleaned = list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))
        if any(len(value) > 80 for value in cleaned):
            raise ValueError("Ingredient names must be at most 80 characters")
        return cleaned

    @field_validator("diet")
    @classmethod
    def normalize_diet(cls, value):
        cleaned = value.strip().lower()
        if cleaned and cleaned not in DIETS:
            raise ValueError("Unknown diet type")
        return cleaned

    @field_validator("allergies")
    @classmethod
    def normalize_allergies(cls, values):
        return _normalize_choices(values, ALLERGIES, "allergy")

    @field_validator("nutrition_goals")
    @classmethod
    def normalize_goals(cls, values):
        return _normalize_choices(values, NUTRITION_GOALS, "nutrition goal")

    @field_validator("other_preferences")
    @classmethod
    def normalize_other(cls, values):
        cleaned = list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))
        if any(len(value) > 80 for value in cleaned):
            raise ValueError("Preferences must be at most 80 characters")
        return cleaned


def _normalize_choices(values, allowed, label):
    cleaned = list(dict.fromkeys(value.strip().lower() for value in values if value.strip()))
    unknown = [value for value in cleaned if value not in allowed]
    if unknown:
        raise ValueError(f"Unknown {label}: {unknown[0]}")
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
    uncertain: bool = False


class DetectionResponse(BaseModel):
    detections: list[Detection]
    message: str
