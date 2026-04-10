"""Pydantic response models for the Pokédex API."""

from pydantic import BaseModel


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


# --- Favorites ---

class FavoriteItem(BaseModel):
    pokemon_id: int
    name: str
    sprite: str | None = None


class FavoritesListResponse(BaseModel):
    favorites: list[FavoriteItem]


class OkResponse(BaseModel):
    ok: bool
