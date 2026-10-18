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
    pantry = {"rice", "egg", "carrot", "broccoli"}
    response = client.post("/recipes", json={"ingredients": [" RICE ", "egg", "carrot", "broccoli"], "servings": 4})
    assert response.status_code == 200
    recipes = response.json()["recipes"]
    assert 1 <= len(recipes) <= 3
    assert [len(r["missing_ingredients"]) for r in recipes] == sorted(len(r["missing_ingredients"]) for r in recipes)
    for recipe in recipes:
        assert set(recipe["ingredients_used"]).isdisjoint(recipe["missing_ingredients"])
        assert set(recipe["ingredients_used"] + recipe["missing_ingredients"]) == {i["name"] for i in recipe["ingredients"]}
        assert recipe["servings"] == 4
        assert set(recipe["ingredients_used"]) <= pantry
        assert recipe["ingredients_used"]


def test_filters():
    recipes = client.post("/recipes", json={"ingredients": ["rice", "broccoli"], "exclusions": ["egg"], "max_minutes": 20, "vegetarian": True}).json()["recipes"]
    assert recipes
    for recipe in recipes:
        assert recipe["estimated_minutes"] <= 20
        assert "egg" not in {i["name"] for i in recipe["ingredients"]}
        assert recipe["ingredients_used"]


def test_empty_pantry():
    assert client.post("/recipes", json={"ingredients": [" "]}).status_code == 422


def test_egg_allergy_skips_egg():
    recipes = client.post("/recipes", json={
        "ingredients": ["rice", "egg", "carrot", "broccoli"],
        "allergies": ["eggs"],
    }).json()["recipes"]
    assert recipes
    for recipe in recipes:
        assert "egg" not in {item["name"] for item in recipe["ingredients"]}
        assert "eggs" not in {item["name"] for item in recipe["ingredients"]}


def test_unknown_preference_is_rejected():
    assert client.post("/recipes", json={"ingredients": ["rice"], "diet": "carnivore"}).status_code == 422


def test_apple_banana_uses_those_ingredients():
    result = client.post("/recipes", json={"ingredients": ["apple", "banana"]}).json()
    assert 1 <= len(result["recipes"]) <= 3
    for recipe in result["recipes"]:
        used = set(recipe["ingredients_used"])
        assert used
        assert used <= {"apple", "banana"}


def test_does_not_require_every_ingredient():
    result = client.post("/recipes", json={"ingredients": ["chicken", "rice", "broccoli", "banana"]}).json()
    assert result["recipes"]
    assert any(len(recipe["ingredients_used"]) < 4 for recipe in result["recipes"])


def test_custom_other_preference_is_accepted():
    response = client.post("/recipes", json={
        "ingredients": ["rice", "carrot", "broccoli"],
        "other_preferences": ["no spicy food", "dairy free"],
    })
    assert response.status_code == 200


