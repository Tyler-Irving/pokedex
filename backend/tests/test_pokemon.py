"""
Tests for pokemon routes (backend/routes/pokemon.py).

All external HTTP calls are mocked via monkeypatch on pokeapi_get so
these tests are fully offline and self-contained.
"""

from unittest.mock import patch

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
    "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
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
        # URL extracted from species.url includes trailing slash
        "pokemon-species/1/": FAKE_SPECIES,
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


# ---------------------------------------------------------------------------
# Tests: GET /api/pokemon?type=<type> (type filter)
# ---------------------------------------------------------------------------

class TestListPokemonTypeFilter:
    @patch("backend.routes.pokemon._type_index", {"grass": ["bulbasaur"], "fire": ["charmander"]})
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_type_filter_returns_only_matching_pokemon(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon?type=grass")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["results"][0]["name"] == "bulbasaur"

    @patch("backend.routes.pokemon._type_index", {"grass": ["bulbasaur"], "fire": ["charmander"]})
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_type_filter_unknown_type_skips_filter(self, mock_get):
        # When the requested type is not in the index, the filter is a no-op
        # and all pokemon are returned (code: `if type and type in _type_index`).
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon?type=dragon")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 3  # all three FAKE_LIST entries returned

    @patch("backend.routes.pokemon._type_index", {"grass": ["bulbasaur", "squirtle"], "fire": ["charmander"]})
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_type_filter_combined_with_search(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        # squirtle is in _type_index["grass"] for this test, but search for "squirt" won't
        # match "bulbasaur" — only "squirtle" survives both filters
        response = client.get("/api/pokemon?type=grass&search=squirt")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["results"][0]["name"] == "squirtle"


# ---------------------------------------------------------------------------
# Tests: GET /api/pokemon/{id_or_name}/encounters
# ---------------------------------------------------------------------------

FAKE_ENCOUNTERS = [
    {
        "location_area": {"name": "pallet-town-area", "url": "https://pokeapi.co/api/v2/location-area/1/"},
        "version_details": [],
    }
]


class TestGetPokemonEncounters:
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_encounters_returns_list(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get({"pokemon/1/encounters": FAKE_ENCOUNTERS})
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon/1/encounters")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert body[0]["location_area"]["name"] == "pallet-town-area"

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_encounters_by_name(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get({"pokemon/bulbasaur/encounters": FAKE_ENCOUNTERS})
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon/bulbasaur/encounters")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_encounters_invalid_id_returns_400(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        # Special characters are not valid
        response = client.get("/api/pokemon/!!invalid!!/encounters")
        assert response.status_code in (400, 422)

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_encounters_unknown_pokemon_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/pokemon/99999/encounters")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests: GET /api/types
# ---------------------------------------------------------------------------

class TestListTypes:
    @patch("backend.routes.pokemon._type_index", {"fire": [], "grass": [], "water": []})
    def test_types_returns_sorted_list(self):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/types")
        assert response.status_code == 200
        body = response.json()
        assert "types" in body
        assert isinstance(body["types"], list)
        assert body["types"] == sorted(body["types"])

    @patch("backend.routes.pokemon._type_index", {"fire": [], "grass": [], "water": []})
    def test_types_returns_all_indexed_types(self):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/types")
        body = response.json()
        assert set(body["types"]) == {"fire", "grass", "water"}

    @patch("backend.routes.pokemon._type_index", {})
    def test_types_empty_index_returns_empty_list(self):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/types")
        assert response.status_code == 200
        assert response.json() == {"types": []}


# ---------------------------------------------------------------------------
# Tests: GET /api/compare
# ---------------------------------------------------------------------------

def _make_pokemon_data(pokemon_id: int, name: str, hp: int, attack: int) -> dict:
    return {
        "id": pokemon_id,
        "name": name,
        "sprites": {"front_default": f"https://sprites/{pokemon_id}.png", "front_shiny": None},
        "types": [{"type": {"name": "normal"}}],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": hp},
            {"stat": {"name": "attack"}, "base_stat": attack},
            {"stat": {"name": "defense"}, "base_stat": 50},
            {"stat": {"name": "special-attack"}, "base_stat": 50},
            {"stat": {"name": "special-defense"}, "base_stat": 50},
            {"stat": {"name": "speed"}, "base_stat": 50},
        ],
        "abilities": [],
    }


FAKE_BULBASAUR = _make_pokemon_data(1, "bulbasaur", hp=45, attack=49)
FAKE_CHARMANDER = _make_pokemon_data(4, "charmander", hp=39, attack=52)


class TestComparePokemon:
    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_two_pokemon_returns_correct_shape(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get({"pokemon/1": FAKE_BULBASAUR, "pokemon/4": FAKE_CHARMANDER})
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare?ids=1,4")
        assert response.status_code == 200
        body = response.json()
        assert "pokemon" in body
        assert "best_in_stat" in body
        assert len(body["pokemon"]) == 2

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_best_in_stat_correct(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get({"pokemon/1": FAKE_BULBASAUR, "pokemon/4": FAKE_CHARMANDER})
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare?ids=1,4")
        body = response.json()
        # bulbasaur hp=45 > charmander hp=39
        assert body["best_in_stat"]["hp"] == "bulbasaur"
        # charmander attack=52 > bulbasaur attack=49
        assert body["best_in_stat"]["attack"] == "charmander"

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_one_pokemon_returns_400(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare?ids=1")
        assert response.status_code == 400

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_seven_pokemon_returns_400(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare?ids=1,2,3,4,5,6,7")
        assert response.status_code == 400

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_invalid_id_format_returns_400(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare?ids=1,@@@")
        assert response.status_code == 400

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_unknown_pokemon_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get({"pokemon/1": FAKE_BULBASAUR})
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare?ids=1,99999")
        assert response.status_code == 404

    @patch("backend.routes.pokemon.pokeapi_get")
    def test_compare_missing_ids_param_returns_422(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/compare")
        assert response.status_code == 422
