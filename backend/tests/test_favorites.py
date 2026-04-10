"""
Tests for favorites routes (backend/routes/favorites.py).

Uses a temporary aiosqlite database and mocks pokeapi_get so no real
HTTP calls or persistent DB writes occur.
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.database import init_db
from backend.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_POKEMON = {
    "name": "bulbasaur",
    "sprites": {"front_default": "https://sprites/1.png"},
}


def _mock_pokeapi_get():
    async def side_effect(path: str):
        if path.startswith("pokemon/"):
            return FAKE_POKEMON
        return {}

    return side_effect


@pytest.fixture(autouse=True)
def _use_tmp_db(tmp_path, monkeypatch):
    """Point the database at a temporary file and initialise the schema."""
    import asyncio

    db_path = str(tmp_path / "test_favorites.db")
    monkeypatch.setattr("backend.database.DB_PATH", db_path)
    asyncio.get_event_loop().run_until_complete(init_db())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestListFavorites:
    @patch("backend.routes.favorites.pokeapi_get")
    def test_empty_list_initially(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/favorites")
        assert response.status_code == 200
        assert response.json()["favorites"] == []


class TestAddFavorite:
    @patch("backend.routes.favorites.pokeapi_get")
    def test_add_then_list_returns_favorite(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/favorites/1")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        favorites = client.get("/api/favorites").json()["favorites"]
        assert len(favorites) == 1
        assert favorites[0]["pokemon_id"] == 1
        assert favorites[0]["name"] == "bulbasaur"

    @patch("backend.routes.favorites.pokeapi_get")
    def test_add_duplicate_returns_409(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        client.post("/api/favorites/1")
        resp = client.post("/api/favorites/1")
        assert resp.status_code == 409


class TestRemoveFavorite:
    @patch("backend.routes.favorites.pokeapi_get")
    def test_remove_existing_returns_200(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        client.post("/api/favorites/1")
        resp = client.delete("/api/favorites/1")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        favorites = client.get("/api/favorites").json()["favorites"]
        assert len(favorites) == 0

    @patch("backend.routes.favorites.pokeapi_get")
    def test_remove_nonexistent_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/favorites/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auth enforcement tests
# ---------------------------------------------------------------------------

class TestAuthEnforcement:
    """Verify that when POKEDEX_API_KEY is set the key header is enforced."""

    @patch("backend.routes.favorites.pokeapi_get")
    def test_missing_key_returns_401(self, mock_get, monkeypatch):
        monkeypatch.setenv("POKEDEX_API_KEY", "secret-test-key")
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/favorites")
        assert resp.status_code == 401

    @patch("backend.routes.favorites.pokeapi_get")
    def test_wrong_key_returns_401(self, mock_get, monkeypatch):
        monkeypatch.setenv("POKEDEX_API_KEY", "secret-test-key")
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/favorites", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    @patch("backend.routes.favorites.pokeapi_get")
    def test_correct_key_succeeds(self, mock_get, monkeypatch):
        monkeypatch.setenv("POKEDEX_API_KEY", "secret-test-key")
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/favorites", headers={"X-API-Key": "secret-test-key"})
        assert resp.status_code == 200

    @patch("backend.routes.favorites.pokeapi_get")
    def test_correct_key_allows_add(self, mock_get, monkeypatch):
        monkeypatch.setenv("POKEDEX_API_KEY", "secret-test-key")
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/favorites/1", headers={"X-API-Key": "secret-test-key"})
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
