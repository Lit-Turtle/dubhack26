import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import RecipeRequest
from app.services import backboard

client = TestClient(app)
REAL_CLIENT = httpx.Client


def recipe(**changes):
    return {
        'name': 'Rice bowl', 'estimated_minutes': 20, 'servings': 2, 'vegetarian': True,
        'ingredients': [{'name': 'rice', 'quantity': 1, 'unit': 'cup'}, {'name': 'salt', 'quantity': 0.25, 'unit': 'tsp'}],
        'steps': ['Cook the rice in water until tender and season with salt.'], **changes,
    }


def mock_api(monkeypatch, handler):
    monkeypatch.setenv('BACKBOARD_API_KEY', 'fake-test-key')
    monkeypatch.setenv('BACKBOARD_PROVIDER', 'test-provider')
    monkeypatch.setenv('BACKBOARD_MODEL', 'test-model')
    monkeypatch.setattr(backboard.httpx, 'Client', lambda **kwargs: REAL_CLIENT(transport=httpx.MockTransport(handler), **kwargs))


def test_api_uses_backboard_and_recomputes_missing(monkeypatch):
    calls = []
    def handler(request):
        calls.append(request)
        assert str(request.url) == backboard.API_URL
        assert request.headers['X-API-Key'] == 'fake-test-key'
        data = json.loads(request.content)
        assert data['llm_provider'] == 'test-provider'
        assert data['model_name'] == 'test-model'
        assert data['memory'] == data['web_search'] == 'off'
        assert data['send_to_llm'] == 'true'
        assert data['json_output'] is True
        assert 'thread_id' not in data
        return httpx.Response(200, json={'status': 'completed', 'content': {'recipes': [recipe(missing_ingredients=[])]}})
    mock_api(monkeypatch, handler)
    response = client.post('/recipes', json={'ingredients': ['rice']})
    assert response.status_code == 200
    result = response.json()
    assert 'generated with Backboard' in result['message']
    assert result['recipes'][0]['missing_ingredients'] == ['salt']
    assert result['recipes'][0]['ingredients_used'] == ['rice']
    assert len(calls) == 1


@pytest.mark.parametrize('changes', [
    {'estimated_minutes': 45}, {'vegetarian': False},
    {'steps': []}, {'ingredients': [{'name': 'rice', 'quantity': -1, 'unit': 'cup'}]},
])
def test_rejects_invalid_or_nonmatching_recipes(changes):
    with pytest.raises(ValueError):
        backboard.validate_recipes(json.dumps({'recipes': [recipe(**changes)]}), RecipeRequest(ingredients=['rice'], vegetarian=True))


def test_generated_servings_are_normalized():
    recipes = backboard.validate_recipes(
        json.dumps({'recipes': [recipe(servings=4)]}),
        RecipeRequest(ingredients=['rice'], servings=2, vegetarian=True),
    )
    assert recipes[0].servings == 2


def test_extracts_list_or_fenced_json():
    request = RecipeRequest(ingredients=['rice'], vegetarian=True)
    fenced = '```json\n' + json.dumps({'recipes': [recipe()]}) + '\n```'
    assert backboard.validate_recipes([recipe()], request)[0].name == 'Rice bowl'
    assert backboard.validate_recipes(fenced, request)[0].name == 'Rice bowl'


def test_keeps_valid_recipes_when_one_fails():
    recipes = backboard.validate_recipes(
        json.dumps({'recipes': [recipe(estimated_minutes=45), recipe(name='Good rice')]}),
        RecipeRequest(ingredients=['rice'], vegetarian=True),
    )
    assert [item.name for item in recipes] == ['Good rice']


def test_exclusions_are_checked():
    with pytest.raises(ValueError):
        backboard.validate_recipes(json.dumps({'recipes': [recipe()]}), RecipeRequest(ingredients=['rice'], exclusions=['salt']))


@pytest.mark.parametrize('status', [401, 402, 403, 429, 500])
def test_http_failure_is_safe_and_falls_back(monkeypatch, status):
    mock_api(monkeypatch, lambda request: httpx.Response(status, text='sensitive-upstream-detail'))
    result = client.post('/recipes', json={'ingredients': ['rice']}).json()
    assert 'sample recipe' in result['message']
    assert result['recipes']
    assert 'sensitive-upstream-detail' not in json.dumps(result)
    assert 'fake-test-key' not in json.dumps(result)


@pytest.mark.parametrize('payload', [
    {'status': 'COMPLETED', 'content': 'not json'},
    {'status': 'FAILED', 'content': '{}'},
    {'status': 'IN_PROGRESS'},
    {'status': 'COMPLETED', 'content': {'recipes': []}},
    {'status': 'COMPLETED', 'content': '{"recipes":[]}'},
    [],
])
def test_bad_upstream_response_falls_back(monkeypatch, payload):
    mock_api(monkeypatch, lambda request: httpx.Response(200, json=payload))
    result = client.post('/recipes', json={'ingredients': ['rice']}).json()
    assert 'sample recipe' in result['message']


def test_timeout_is_not_retried(monkeypatch):
    calls = []
    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout('sensitive-detail', request=request)
    mock_api(monkeypatch, handler)
    result = client.post('/recipes', json={'ingredients': ['rice']}).json()
    assert 'timed out' in result['message']
    assert len(calls) == 1


def test_missing_key_never_calls_backboard(monkeypatch):
    monkeypatch.delenv('BACKBOARD_API_KEY', raising=False)
    def unexpected_call(**kwargs):
        pytest.fail('Network should not be used without a key')
    monkeypatch.setattr(backboard.httpx, 'Client', unexpected_call)
    result = client.post('/recipes', json={'ingredients': ['rice']}).json()
    assert 'not configured' in result['message']
