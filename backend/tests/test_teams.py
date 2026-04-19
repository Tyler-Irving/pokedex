"""
Tests for teams routes (backend/routes/teams.py).

Uses a temporary aiosqlite database and mocks pokeapi_get / _type_chart so no
real HTTP calls or persistent DB writes occur.
"""

import asyncio
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.database import init_db
from backend.main import app


FAKE_POKEMON = {
    "name": "bulbasaur",
    "sprites": {"front_default": "https://sprites/1.png"},
    "types": [{"type": {"name": "grass"}}, {"type": {"name": "poison"}}],
}

MOCK_TYPE_CHART = {
    "grass": {
        "double_damage_to": [{"name": "water"}, {"name": "ground"}, {"name": "rock"}],
        "double_damage_from": [{"name": "fire"}, {"name": "ice"}, {"name": "poison"}, {"name": "flying"}, {"name": "bug"}],
        "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": [],
    },
    "poison": {
        "double_damage_to": [{"name": "grass"}, {"name": "fairy"}],
        "double_damage_from": [{"name": "ground"}, {"name": "psychic"}],
        "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": [],
    },
    "fire": {
        "double_damage_to": [{"name": "grass"}, {"name": "ice"}, {"name": "bug"}, {"name": "steel"}],
        "double_damage_from": [{"name": "water"}, {"name": "ground"}, {"name": "rock"}],
        "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": [],
    },
    "water": {
        "double_damage_to": [{"name": "fire"}, {"name": "ground"}, {"name": "rock"}],
        "double_damage_from": [{"name": "electric"}, {"name": "grass"}],
        "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": [],
    },
    "normal": {"double_damage_to": [], "double_damage_from": [{"name": "fighting"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "electric": {"double_damage_to": [{"name": "water"}, {"name": "flying"}], "double_damage_from": [{"name": "ground"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "ice": {"double_damage_to": [{"name": "grass"}, {"name": "ground"}, {"name": "flying"}, {"name": "dragon"}], "double_damage_from": [{"name": "fire"}, {"name": "fighting"}, {"name": "rock"}, {"name": "steel"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "fighting": {"double_damage_to": [{"name": "normal"}, {"name": "ice"}, {"name": "rock"}, {"name": "dark"}, {"name": "steel"}], "double_damage_from": [{"name": "flying"}, {"name": "psychic"}, {"name": "fairy"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "ground": {"double_damage_to": [{"name": "fire"}, {"name": "electric"}, {"name": "poison"}, {"name": "rock"}, {"name": "steel"}], "double_damage_from": [{"name": "water"}, {"name": "grass"}, {"name": "ice"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "flying": {"double_damage_to": [{"name": "grass"}, {"name": "fighting"}, {"name": "bug"}], "double_damage_from": [{"name": "electric"}, {"name": "ice"}, {"name": "rock"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "psychic": {"double_damage_to": [{"name": "fighting"}, {"name": "poison"}], "double_damage_from": [{"name": "bug"}, {"name": "ghost"}, {"name": "dark"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "bug": {"double_damage_to": [{"name": "grass"}, {"name": "psychic"}, {"name": "dark"}], "double_damage_from": [{"name": "fire"}, {"name": "flying"}, {"name": "rock"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "rock": {"double_damage_to": [{"name": "fire"}, {"name": "ice"}, {"name": "flying"}, {"name": "bug"}], "double_damage_from": [{"name": "water"}, {"name": "grass"}, {"name": "fighting"}, {"name": "ground"}, {"name": "steel"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "ghost": {"double_damage_to": [{"name": "psychic"}, {"name": "ghost"}], "double_damage_from": [{"name": "ghost"}, {"name": "dark"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "dragon": {"double_damage_to": [{"name": "dragon"}], "double_damage_from": [{"name": "ice"}, {"name": "dragon"}, {"name": "fairy"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "dark": {"double_damage_to": [{"name": "psychic"}, {"name": "ghost"}], "double_damage_from": [{"name": "fighting"}, {"name": "bug"}, {"name": "fairy"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "steel": {"double_damage_to": [{"name": "ice"}, {"name": "rock"}, {"name": "fairy"}], "double_damage_from": [{"name": "fire"}, {"name": "fighting"}, {"name": "ground"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
    "fairy": {"double_damage_to": [{"name": "fighting"}, {"name": "dragon"}, {"name": "dark"}], "double_damage_from": [{"name": "poison"}, {"name": "steel"}], "half_damage_to": [], "half_damage_from": [], "no_damage_to": [], "no_damage_from": []},
}


def _mock_pokeapi_get(pokemon_data=None):
    """Return an async side_effect function that returns *pokemon_data* for any
    pokemon/ path, or FAKE_POKEMON if none is supplied."""
    data = pokemon_data if pokemon_data is not None else FAKE_POKEMON

    async def side_effect(path: str):
        if path.startswith("pokemon/"):
            return data
        return {}

    return side_effect


@pytest.fixture(autouse=True)
def _use_tmp_db(tmp_path, monkeypatch):
    """Point the database at a temporary file and initialise the schema."""
    db_path = str(tmp_path / "test_teams.db")
    monkeypatch.setattr("backend.database.DB_PATH", db_path)
    asyncio.get_event_loop().run_until_complete(init_db())


def _create_team(client: TestClient, name: str = "My Team") -> dict[str, Any]:
    resp = client.post("/api/teams", json={"name": name})
    assert resp.status_code == 201
    return resp.json()


class TestListTeams:
    def test_list_empty_returns_empty_list(self):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/teams")
        assert response.status_code == 200
        assert response.json()["teams"] == []

    def test_list_after_creating_teams(self):
        client = TestClient(app, raise_server_exceptions=False)
        _create_team(client, "Team Alpha")
        _create_team(client, "Team Beta")

        response = client.get("/api/teams")
        assert response.status_code == 200
        teams = response.json()["teams"]
        assert len(teams) == 2
        names = {t["name"] for t in teams}
        assert "Team Alpha" in names
        assert "Team Beta" in names
        for team in teams:
            assert "id" in team
            assert "member_count" in team
            assert team["member_count"] == 0


class TestCreateTeam:
    def test_create_team_returns_201_with_data(self):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/teams", json={"name": "Rocket Team"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Rocket Team"
        assert data["member_count"] == 0
        assert "id" in data

    def test_create_requires_name(self):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/teams", json={})
        assert resp.status_code == 422

    def test_create_max_5_returns_409(self):
        client = TestClient(app, raise_server_exceptions=False)
        for i in range(5):
            _create_team(client, f"Team {i}")
        resp = client.post("/api/teams", json={"name": "Sixth Team"})
        assert resp.status_code == 409


class TestGetTeam:
    @patch("backend.routes.teams.pokeapi_get")
    def test_get_team_with_members(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client, "Grass Squad")
        team_id = team["id"]

        client.post(f"/api/teams/{team_id}/members/1")

        resp = client.get(f"/api/teams/{team_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == team_id
        assert data["name"] == "Grass Squad"
        assert len(data["members"]) == 1
        member = data["members"][0]
        assert member["pokemon_id"] == 1
        assert member["name"] == "bulbasaur"
        assert member["sprite"] == "https://sprites/1.png"

    def test_get_nonexistent_returns_404(self):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/teams/99999")
        assert resp.status_code == 404


class TestRenameTeam:
    def test_rename_returns_200_with_updated_name(self):
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client, "Old Name")
        team_id = team["id"]

        resp = client.patch(f"/api/teams/{team_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == team_id
        assert data["name"] == "New Name"
        assert "member_count" in data

    def test_rename_nonexistent_returns_404(self):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.patch("/api/teams/99999", json={"name": "Ghost Team"})
        assert resp.status_code == 404


class TestDeleteTeam:
    def test_delete_returns_ok(self):
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client, "Doomed Team")
        team_id = team["id"]

        resp = client.delete(f"/api/teams/{team_id}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        get_resp = client.get(f"/api/teams/{team_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self):
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/teams/99999")
        assert resp.status_code == 404

    @patch("backend.routes.teams.pokeapi_get")
    def test_delete_cascades_to_members(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client, "Cascade Team")
        team_id = team["id"]

        add_resp = client.post(f"/api/teams/{team_id}/members/1")
        assert add_resp.status_code == 201

        del_resp = client.delete(f"/api/teams/{team_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["ok"] is True

        assert client.get(f"/api/teams/{team_id}").status_code == 404

        # Re-adding the same pokemon on a new team must succeed: the old
        # team_members row was cascade-deleted so the UNIQUE constraint is free.
        new_team = _create_team(client, "New Team")
        new_id = new_team["id"]
        add_again = client.post(f"/api/teams/{new_id}/members/1")
        assert add_again.status_code == 201


class TestTeamMembers:
    @patch("backend.routes.teams.pokeapi_get")
    def test_add_member_returns_201(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client)
        resp = client.post(f"/api/teams/{team['id']}/members/1")
        assert resp.status_code == 201
        assert resp.json()["ok"] is True

    @patch("backend.routes.teams.pokeapi_get")
    def test_add_duplicate_returns_409(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client)
        tid = team["id"]
        client.post(f"/api/teams/{tid}/members/1")
        resp = client.post(f"/api/teams/{tid}/members/1")
        assert resp.status_code == 409

    @patch("backend.routes.teams.pokeapi_get")
    def test_add_to_nonexistent_team_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/teams/99999/members/1")
        assert resp.status_code == 404

    @patch("backend.routes.teams.pokeapi_get")
    def test_add_max_6_members_returns_409(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client)
        tid = team["id"]

        for pokemon_id in range(1, 7):
            resp = client.post(f"/api/teams/{tid}/members/{pokemon_id}")
            assert resp.status_code == 201, f"Expected 201 adding pokemon {pokemon_id}, got {resp.status_code}"

        resp = client.post(f"/api/teams/{tid}/members/7")
        assert resp.status_code == 409

    @patch("backend.routes.teams.pokeapi_get")
    def test_remove_member_returns_ok(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client)
        tid = team["id"]
        client.post(f"/api/teams/{tid}/members/1")

        resp = client.delete(f"/api/teams/{tid}/members/1")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        detail = client.get(f"/api/teams/{tid}").json()
        assert detail["members"] == []

    @patch("backend.routes.teams.pokeapi_get")
    def test_remove_nonexistent_member_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client)
        resp = client.delete(f"/api/teams/{team['id']}/members/99999")
        assert resp.status_code == 404


class TestCoverage:
    def test_coverage_empty_team_returns_all_no_coverage(self):
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client, "Empty Team")
        resp = client.get(f"/api/teams/{team['id']}/coverage")
        assert resp.status_code == 200
        data = resp.json()
        assert data["strong"] == []
        assert data["weak"] == []
        assert len(data["no_coverage"]) == 18

    @patch("backend.routes.teams.pokeapi_get")
    @patch("backend.routes.teams._type_chart", MOCK_TYPE_CHART)
    def test_coverage_returns_correct_shape(self, mock_get):
        """Bulbasaur is grass/poison. Grass hits water/ground/rock; poison hits
        grass/fairy. Together strong = water, ground, rock, grass, fairy."""
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        team = _create_team(client, "Bulbasaur Only")
        tid = team["id"]
        client.post(f"/api/teams/{tid}/members/1")

        resp = client.get(f"/api/teams/{tid}/coverage")
        assert resp.status_code == 200
        data = resp.json()

        assert "strong" in data
        assert "weak" in data
        assert "no_coverage" in data

        strong_set = set(data["strong"])
        # grass -> double_damage_to: water, ground, rock
        # poison -> double_damage_to: grass, fairy
        for expected in ("water", "ground", "rock", "grass", "fairy"):
            assert expected in strong_set, f"Expected '{expected}' in strong, got {strong_set}"

        # Every type in strong+weak+no_coverage must appear exactly once
        all_types = set(data["strong"] + data["weak"] + data["no_coverage"])
        assert len(all_types) == 18

    @patch("backend.routes.teams.pokeapi_get")
    @patch("backend.routes.teams._type_chart", MOCK_TYPE_CHART)
    def test_coverage_nonexistent_team_returns_404(self, mock_get):
        mock_get.side_effect = _mock_pokeapi_get()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/teams/99999/coverage")
        assert resp.status_code == 404
