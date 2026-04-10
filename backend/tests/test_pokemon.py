"""
Tests for pokemon routes (backend/routes/pokemon.py).

All external HTTP calls are mocked via monkeypatch on pokeapi_get so
these tests are fully offline and self-contained.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_LIST = {
    "results": [
        {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
        {"name": "charmander", "url": "https://pokeapi.co/api/v2/pokemon/4/"},
        {"name": "squirtle", "url": "https://pokeapi.co/api/v2/pokemon/7/"},
    ],
}

FAKE_POKEMON_DETAIL = {
    "id": 1,
    "name": "bulbasaur",
    "sprites": {
        "front_default": "https://sprites/1.png",
        "front_shiny": "https://sprites/1s.png",
    },
    "types": [
        {"type": {"name": "grass"}},
        {"type": {"name": "poison"}},
    ],
    "stats": [
        {"stat": {"name": "hp"}, "base_stat": 45},
        {"stat": {"name": "attack"}, "base_stat": 49},
    ],
    "height": 7,
    "weight": 69,
    "abilities": [
        {"ability": {"name": "overgrow"}},
        {"ability": {"name": "chlorophyll"}},
    ],
}

FAKE_SPECIES = {
    "flavor_text_entries": [
        {
            "flavor_text": "A strange seed.",
            "language": {"name": "en"},
        },
    ],
}


def _mock_pokeapi_get(responses: dict | None = None):
    """Return an AsyncMock that resolves the given path→response mapping."""
    default_responses = {
        "pokemon?limit=1302&offset=0": FAKE_LIST,
        "pokemon/1": FAKE_POKEMON_DETAIL,
        "pokemon-species/1": FAKE_SPECIES,
    }
    if responses:
        default_responses.update(responses)

    async def side_effect(path: str):
        if path in default_responses:
            return default_responses[path]
        raise HTTPException(status_code=404, detail="Not found")

    return side_effect


# ---------------------------------------------------------------------------
# Tests: GET /api/pokemon (list)
# ---------------------------------------------------------------------------

class TestListPokemon:
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_list_returns_200_with_total_and_results(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon")
        assert response.status_code == 200
        body = response.json()
        assert "total" in body
        assert "results" in body
        assert body["total"] == 3
        assert len(body["results"]) == 3

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_search_filters_by_name(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon?search=bulba")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["results"][0]["name"] == "bulbasaur"

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_search_no_match_returns_empty(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon?search=zzz")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["results"] == []


# ---------------------------------------------------------------------------
# Tests: GET /api/pokemon/{id} (detail)
# ---------------------------------------------------------------------------

class TestGetPokemon:
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_get_pokemon_returns_expected_shape(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon/1")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == 1
        assert body["name"] == "bulbasaur"
        assert "grass" in body["types"]
        assert body["stats"]["hp"] == 45
        assert body["height"] == 7
        assert body["weight"] == 69
        assert "overgrow" in body["abilities"]
        assert body["flavor_text"] == "A strange seed."

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_get_pokemon_not_found_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon/99999")
        assert response.status_code == 404
