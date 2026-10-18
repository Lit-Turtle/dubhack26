from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_api_prefix():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/health").json() == {"status": "ok"}
    prefixed = client.post("/api/recipes", json={"ingredients": ["apple", "banana"]})
    assert prefixed.status_code == 200
    assert prefixed.json()["recipes"]


def test_missing_ingredients_and_servings():
    response = client.post("/recipes", json={"ingredients": [" RICE ", "egg", "carrot", "broccoli"], "servings": 4})
    assert response.status_code == 200
    recipes = response.json()["recipes"]
    assert len(recipes) == 3
    assert [len(r["missing_ingredients"]) for r in recipes] == sorted(len(r["missing_ingredients"]) for r in recipes)
    for recipe in recipes:
        assert set(recipe["ingredients_used"]).isdisjoint(recipe["missing_ingredients"])
        assert set(recipe["ingredients_used"] + recipe["missing_ingredients"]) == {i["name"] for i in recipe["ingredients"]}
        assert recipe["servings"] == 4
    fried_rice = next(r for r in recipes if r["name"] == "Vegetable Fried Rice")
    assert next(i["quantity"] for i in fried_rice["ingredients"] if i["name"] == "rice") == 4


def test_filters():
    recipes = client.post("/recipes", json={"ingredients": ["rice", "broccoli"], "exclusions": ["egg"], "max_minutes": 20, "vegetarian": True}).json()["recipes"]
    assert recipes
    for recipe in recipes:
        assert recipe["estimated_minutes"] <= 20
        assert "egg" not in {i["name"] for i in recipe["ingredients"]}


def test_empty_pantry():
    assert client.post("/recipes", json={"ingredients": [" "]}).status_code == 422


def test_egg_allergy_filters_sample_recipes():
    recipes = client.post("/recipes", json={
        "ingredients": ["rice", "egg", "carrot", "broccoli"],
        "allergies": ["eggs"],
    }).json()["recipes"]
    names = {recipe["name"] for recipe in recipes}
    assert "Vegetable Omelet" not in names
    assert "Vegetable Fried Rice" not in names
    assert "Broccoli Rice Bowl" in names


def test_unknown_preference_is_rejected():
    assert client.post("/recipes", json={"ingredients": ["rice"], "diet": "carnivore"}).status_code == 422


def test_apple_banana_has_sample_recipes():
    result = client.post("/recipes", json={"ingredients": ["apple", "banana"]}).json()
    names = {recipe["name"] for recipe in result["recipes"]}
    assert "Apple Banana Smoothie" in names
    assert len(result["recipes"]) == 3
    assert all({"apple", "banana"} & set(recipe["ingredients_used"]) for recipe in result["recipes"])


def test_custom_other_preference_is_accepted():
    response = client.post("/recipes", json={
        "ingredients": ["rice", "carrot", "broccoli"],
        "other_preferences": ["no spicy food", "dairy free"],
    })
    assert response.status_code == 200


