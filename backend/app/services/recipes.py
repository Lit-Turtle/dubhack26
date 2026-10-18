import json
from pathlib import Path

from app.schemas import Ingredient, Recipe, RecipeRequest

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "recipes.json"

FRUITS = {
    "apple", "banana", "orange", "blueberry", "strawberry", "lemon", "lime",
    "mango", "grape", "watermelon", "peach", "pear", "avocado", "berry",
}
PROTEINS = {
    "chicken", "beef", "pork", "egg", "eggs", "tofu", "fish", "salmon", "tuna",
    "shrimp", "turkey", "lamb", "ham", "bean", "beans",
}
MEATS = {
    "chicken", "beef", "pork", "bacon", "ham", "turkey", "lamb", "fish",
    "salmon", "tuna", "shrimp",
}
CARBS = {"rice", "pasta", "bread", "noodle", "noodles", "tortilla", "oat", "oats", "potato"}
VEGGIES = {
    "carrot", "broccoli", "tomato", "spinach", "onion", "garlic", "pepper",
    "cucumber", "lettuce", "cabbage", "corn", "pea", "peas", "asparagus",
}


def _scale(quantity: float, servings: int) -> float:
    return quantity * servings / 2


def _to_recipe(name: str, minutes: int, ingredients: list[dict], steps: list[str], request: RecipeRequest) -> Recipe:
    pantry = set(request.ingredients)
    names = [item["name"] for item in ingredients]
    return Recipe(
        name=name,
        estimated_minutes=min(minutes, request.max_minutes),
        servings=request.servings,
        ingredients=[
            Ingredient(name=item["name"], quantity=_scale(item["quantity"], request.servings), unit=item["unit"])
            for item in ingredients
        ],
        ingredients_used=[name for name in names if name in pantry],
        missing_ingredients=[name for name in names if name not in pantry],
        steps=steps,
    )


def _usable_pantry(request: RecipeRequest) -> list[str]:
    excluded = set(request.exclusions)
    usable = [name for name in request.ingredients if name not in excluded]
    if request.vegetarian:
        usable = [name for name in usable if name not in MEATS]
    return usable


def _join_names(names: list[str]) -> str:
    pretty = [name.replace("_", " ") for name in names]
    if len(pretty) == 1:
        return pretty[0].title()
    if len(pretty) == 2:
        return f"{pretty[0].title()} {pretty[1].title()}"
    return f"{pretty[0].title()} {pretty[1].title()} {pretty[2].title()}"


def _cook_method(items: list[str]) -> tuple[str, int, list[dict], list[str]]:
    fruits = [name for name in items if name in FRUITS]
    proteins = [name for name in items if name in PROTEINS]
    carbs = [name for name in items if name in CARBS]
    veggies = [name for name in items if name in VEGGIES]
    extras = [name for name in items if name not in fruits + proteins + carbs + veggies]

    if fruits and len(fruits) >= len(items) - 1 and not proteins:
        used = fruits[:3]
        ingredients = [{"name": name, "quantity": 1, "unit": ""} for name in used]
        return (
            f"{_join_names(used)} Smoothie",
            8,
            ingredients,
            [
                f"Prep {', '.join(used)} and add them to a blender.",
                "Blend with a splash of cold water until smooth.",
                "Pour and serve immediately.",
            ],
        )

    if proteins:
        used = (proteins[:1] + veggies[:1] + carbs[:1] + extras[:1])[:3]
        ingredients = [{"name": name, "quantity": 1, "unit": ""} for name in used]
        if "oil" not in {item["name"] for item in ingredients}:
            ingredients.append({"name": "oil", "quantity": 1, "unit": "tbsp"})
        return (
            f"{_join_names(used)} Skillet",
            20,
            ingredients,
            [
                f"Cut {', '.join(used)} into bite-size pieces.",
                "Heat a little oil in a skillet over medium heat.",
                f"Cook {used[0]} first, then add the remaining ingredients and cook until done.",
                "Season to taste and serve hot.",
            ],
        )

    if carbs:
        used = (carbs[:1] + veggies[:2] + extras[:1] + fruits[:1])[:3]
        ingredients = [{"name": name, "quantity": 1, "unit": ""} for name in used]
        return (
            f"{_join_names(used)} Bowl",
            18,
            ingredients,
            [
                f"Cook or warm the {used[0]}.",
                f"Prepare {', '.join(used[1:]) or used[0]} while that finishes.",
                "Combine in a bowl, season, and serve.",
            ],
        )

    used = items[:3]
    ingredients = [{"name": name, "quantity": 1, "unit": ""} for name in used]
    return (
        f"Simple {_join_names(used)}",
        15,
        ingredients,
        [
            f"Prep {', '.join(used)}.",
            "Cook in a pan or serve fresh, depending on the ingredients.",
            "Season lightly and serve.",
        ],
    )


def compose_recipes(request: RecipeRequest) -> list[Recipe]:
    """Build up to three recipes from a subset of the user's pantry."""
    usable = _usable_pantry(request)
    if not usable:
        return []

    recipes = []
    seen = set()

    def add(name: str, minutes: int, ingredients: list[dict], steps: list[str]) -> None:
        if name in seen or minutes > request.max_minutes:
            return
        cleaned = [item for item in ingredients if item["name"] not in request.exclusions]
        if not cleaned:
            return
        seen.add(name)
        recipes.append(_to_recipe(name, minutes, cleaned, steps, request))

    fruits = [name for name in usable if name in FRUITS]
    if len(fruits) >= 2:
        pair = fruits[:2]
        add(
            f"{_join_names(pair)} Smoothie",
            8,
            [{"name": name, "quantity": 1, "unit": ""} for name in pair],
            [
                f"Prep {', '.join(pair)} and add them to a blender.",
                "Blend with a splash of cold water until smooth.",
                "Pour and serve immediately.",
            ],
        )
        add(
            f"Fresh {_join_names(pair)} Bowl",
            10,
            [{"name": name, "quantity": 1, "unit": ""} for name in pair],
            [
                f"Slice {', '.join(pair)} into a bowl.",
                "Toss gently and serve.",
            ],
        )
        add(
            f"Warm {_join_names(pair[:1])}",
            12,
            [{"name": pair[0], "quantity": 1, "unit": ""}],
            [
                f"Slice the {pair[0]} and warm it in a pan for a few minutes.",
                "Serve on its own or over the remaining fruit.",
            ],
        )

    subsets = [usable[:4]]
    if len(usable) >= 3:
        subsets.append(usable[1:4])
    subsets.append(usable[:2] if len(usable) > 1 else usable[:1])
    for items in subsets:
        if len(recipes) == 3:
            break
        add(*_cook_method(items))
    return recipes[:3]


def catalog_recipes(request: RecipeRequest) -> list[Recipe]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    pantry = set(request.ingredients)
    excluded = set(request.exclusions)
    results = []
    for item in catalog:
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
            name=item["name"],
            estimated_minutes=item["estimated_minutes"],
            servings=request.servings,
            ingredients=[
                Ingredient(**{**ingredient, "quantity": _scale(ingredient["quantity"], request.servings)})
                for ingredient in item["ingredients"]
            ],
            ingredients_used=[name for name in names if name in pantry],
            missing_ingredients=[name for name in names if name not in pantry],
            steps=item["steps"],
        ))
    return results


def suggest_recipes(request: RecipeRequest) -> list[Recipe]:
    """Prefer recipes built from the pantry; catalog items are extras."""
    combined = {recipe.name: recipe for recipe in catalog_recipes(request)}
    for recipe in compose_recipes(request):
        combined[recipe.name] = recipe
    return sorted(
        combined.values(),
        key=lambda recipe: (len(recipe.missing_ingredients), -len(recipe.ingredients_used), recipe.estimated_minutes),
    )[:3]
