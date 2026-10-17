import pytest


@pytest.fixture(autouse=True)
def isolate_credentials(monkeypatch):
    # Tests never use a developer's real credentials, even if exported in the shell.
    monkeypatch.delenv('BACKBOARD_API_KEY', raising=False)
