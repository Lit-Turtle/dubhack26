import json
from pathlib import Path
from app.schemas import Ingredient, Recipe, RecipeRequest

CATALOG = json.loads((Path(__file__).resolve().parents[1] / "data" / "recipes.json").read_text())


def suggest_recipes(request: RecipeRequest) -> list[Recipe]:
    """Deterministic starter. Replace catalog lookup with validated LLM output later."""
    pantry = set(request.ingredients)
    excluded = set(request.exclusions)
    results = []
    for item in CATALOG:
        names = [ingredient["name"] for ingredient in item["ingredients"]]
        if item["estimated_minutes"] > request.max_minutes:
            continue
        if request.vegetarian and not item["vegetarian"]:
            continue
        if excluded.intersection(names):
            continue
        if not pantry.intersection(names):
            continue
        results.append(Recipe(
            name=item["name"], estimated_minutes=item["estimated_minutes"], servings=request.servings,
            ingredients=[Ingredient(**{**ingredient, "quantity": ingredient["quantity"] * request.servings / 2}) for ingredient in item["ingredients"]],
            ingredients_used=[name for name in names if name in pantry],
            missing_ingredients=[name for name in names if name not in pantry],
            steps=item["steps"],
        ))
    return sorted(results, key=lambda recipe: (len(recipe.missing_ingredients), -len(recipe.ingredients_used), recipe.estimated_minutes))[:3]
