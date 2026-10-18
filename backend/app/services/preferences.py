from app.schemas import RecipeRequest

ALLERGY_INGREDIENTS = {
    "peanuts": ("peanut", "peanuts"),
    "tree nuts": ("almond", "walnut", "cashew", "pecan", "hazelnut", "pistachio", "tree nut"),
    "dairy": ("milk", "cheese", "butter", "yogurt", "cream", "dairy"),
    "lactose": ("milk", "cheese", "butter", "yogurt", "cream", "lactose"),
    "gluten": ("gluten", "wheat", "flour", "bread", "pasta"),
    "eggs": ("egg", "eggs"),
    "soy": ("soy", "soy sauce", "tofu"),
    "fish": ("fish", "salmon", "tuna", "cod"),
    "shellfish": ("shrimp", "crab", "lobster", "shellfish"),
    "sesame": ("sesame",),
}

DIET_EXCLUSIONS = {
    "vegan": ("egg", "eggs", "milk", "cheese", "butter", "yogurt", "cream", "honey"),
    "pescatarian": ("beef", "pork", "chicken", "lamb", "turkey", "bacon"),
    "halal": ("pork", "bacon", "alcohol", "wine", "beer"),
    "kosher": ("pork", "bacon", "shellfish", "shrimp", "crab", "lobster"),
}

OTHER_EXCLUSIONS = {
    "dairy free": ("milk", "cheese", "butter", "yogurt", "cream", "dairy"),
    "gluten free": ("gluten", "wheat", "flour", "bread", "pasta"),
    "paleo": ("rice", "bread", "pasta", "soy", "soy sauce", "tofu", "beans"),
}


def apply_preferences(request: RecipeRequest) -> RecipeRequest:
    exclusions = set(request.exclusions)
    for allergy in request.allergies:
        exclusions.update(ALLERGY_INGREDIENTS.get(allergy, ()))
    exclusions.update(DIET_EXCLUSIONS.get(request.diet, ()))
    for preference in request.other_preferences:
        exclusions.update(OTHER_EXCLUSIONS.get(preference, ()))
    vegetarian = request.vegetarian or request.diet in {"vegetarian", "vegan"}
    return request.model_copy(update={"exclusions": sorted(exclusions), "vegetarian": vegetarian})
