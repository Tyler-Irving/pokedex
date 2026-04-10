"""Pydantic response models for the Pokédex API."""

from pydantic import BaseModel, Field


# --- PokeAPI common patterns ---

class NamedAPIResource(BaseModel):
    name: str
    url: str


class NamedAPIResourceList(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[NamedAPIResource]


# --- Pokemon ---

class PokemonSummary(BaseModel):
    id: int
    name: str
    sprite: str


class PokemonListResponse(BaseModel):
    total: int
    results: list[PokemonSummary]


class PokemonDetail(BaseModel):
    id: int
    name: str
    sprite: str | None = None
    sprite_shiny: str | None = None
    types: list[str]
    stats: dict[str, int]
    height: int
    weight: int
    abilities: list[str]
    flavor_text: str


# --- Types ---

class TypesListResponse(BaseModel):
    types: list[str]


# --- Compare ---

class PokemonCompareItem(BaseModel):
    id: int
    name: str
    sprite: str | None
    types: list[str]
    stats: dict[str, int]


class CompareResponse(BaseModel):
    pokemon: list[PokemonCompareItem]
    best_in_stat: dict[str, str]


# --- Favorites ---

class FavoriteItem(BaseModel):
    pokemon_id: int
    name: str
    sprite: str | None = None


class FavoritesListResponse(BaseModel):
    favorites: list[FavoriteItem]


class OkResponse(BaseModel):
    ok: bool


# --- Teams ---

class TeamMemberItem(BaseModel):
    pokemon_id: int
    name: str
    sprite: str | None = None


class TeamSummary(BaseModel):
    id: int
    name: str
    member_count: int


class TeamDetail(BaseModel):
    id: int
    name: str
    members: list[TeamMemberItem]


class TeamsListResponse(BaseModel):
    teams: list[TeamSummary]


class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)


class TeamRenameRequest(BaseModel):
    name: str = Field(..., min_length=1)


class CoverageResponse(BaseModel):
    strong: list[str]
    weak: list[str]
    no_coverage: list[str]
