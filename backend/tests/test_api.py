from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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


def test_detection_is_explicit_stub():
    response = client.post("/detect", files={"image": ("photo.jpg", b"placeholder", "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["detections"] == []
    assert "not connected" in response.json()["message"]
    assert client.post("/detect", files={"image": ("x.txt", b"text", "text/plain")}).status_code == 415
