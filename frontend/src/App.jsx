import { useState, useEffect, useCallback } from "react";

const PAGE_SIZE = 20;

export default function App() {
  const [view, setView] = useState("list"); // list | favorites
  const [pokemon, setPokemon] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [types, setTypes] = useState([]);
  const [favorites, setFavorites] = useState(new Set());
  const [favList, setFavList] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch types on mount
  useEffect(() => {
    fetch("/api/types")
      .then((r) => r.json())
      .then((d) => setTypes(d.types))
      .catch(() => {});
  }, []);

  // Fetch favorites set
  const loadFavorites = useCallback(() => {
    fetch("/api/favorites")
      .then((r) => r.json())
      .then((d) => {
        setFavList(d.favorites);
        setFavorites(new Set(d.favorites.map((f) => f.pokemon_id)));
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  // Fetch pokemon list
  useEffect(() => {
    if (view !== "list") return;
    setLoading(true);
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(PAGE_SIZE),
    });
    if (search) params.set("search", search);
    if (typeFilter) params.set("type", typeFilter);

    fetch(`/api/pokemon?${params}`)
      .then((r) => r.json())
      .then((d) => {
        setPokemon(d.results);
        setTotal(d.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [offset, search, typeFilter, view]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [search, typeFilter]);

  // Fetch detail
  useEffect(() => {
    if (selected == null) {
      setDetail(null);
      return;
    }
    setDetail(null);
    fetch(`/api/pokemon/${selected}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(() => setSelected(null));
  }, [selected]);

  const toggleFav = async (id, e) => {
    if (e) e.stopPropagation();
    if (favorites.has(id)) {
      await fetch(`/api/favorites/${id}`, { method: "DELETE" });
    } else {
      await fetch(`/api/favorites/${id}`, { method: "POST" });
    }
    loadFavorites();
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="app">
      <header>
        <h1>Pokédex</h1>
      </header>

      <nav>
        <button
          className={view === "list" ? "active" : ""}
          onClick={() => setView("list")}
        >
          All Pokémon
        </button>
        <button
          className={view === "favorites" ? "active" : ""}
          onClick={() => setView("favorites")}
        >
          Favorites ({favorites.size})
        </button>
      </nav>

      {view === "list" && (
        <>
          <div className="controls">
            <input
              type="text"
              placeholder="Search by name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All types</option>
              {types.map((t) => (
                <option key={t} value={t}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {loading ? (
            <div className="loading">Loading...</div>
          ) : pokemon.length === 0 ? (
            <div className="empty">No Pokémon found</div>
          ) : (
            <>
              <div className="grid">
                {pokemon.map((p) => (
                  <div
                    key={p.id}
                    className="card"
                    onClick={() => setSelected(p.id)}
                  >
                    <button
                      className={`fav-btn ${favorites.has(p.id) ? "active" : ""}`}
                      onClick={(e) => toggleFav(p.id, e)}
                    >
                      {favorites.has(p.id) ? "★" : "☆"}
                    </button>
                    <img src={p.sprite} alt={p.name} />
                    <div className="id">#{String(p.id).padStart(3, "0")}</div>
                    <div className="name">{p.name}</div>
                  </div>
                ))}
              </div>
              <div className="pagination">
                <button
                  disabled={offset === 0}
                  onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
                >
                  Previous
                </button>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  disabled={offset + PAGE_SIZE >= total}
                  onClick={() => setOffset((o) => o + PAGE_SIZE)}
                >
                  Next
                </button>
              </div>
            </>
          )}
        </>
      )}

      {view === "favorites" && (
        <>
          {favList.length === 0 ? (
            <div className="empty">
              No favorites yet. Click ☆ on a Pokémon to add one!
            </div>
          ) : (
            <div className="grid">
              {favList.map((p) => (
                <div
                  key={p.pokemon_id}
                  className="card"
                  onClick={() => setSelected(p.pokemon_id)}
                >
                  <button
                    className="fav-btn active"
                    onClick={(e) => toggleFav(p.pokemon_id, e)}
                  >
                    ★
                  </button>
                  <img src={p.sprite} alt={p.name} />
                  <div className="id">
                    #{String(p.pokemon_id).padStart(3, "0")}
                  </div>
                  <div className="name">{p.name}</div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {selected != null && (
        <div className="detail-overlay" onClick={() => setSelected(null)}>
          <div className="detail" onClick={(e) => e.stopPropagation()}>
            <button className="close" onClick={() => setSelected(null)}>
              ×
            </button>
            {detail == null ? (
              <div className="loading">Loading...</div>
            ) : (
              <>
                <div style={{ textAlign: "center" }}>
                  <img src={detail.sprite} alt={detail.name} />
                  <h2>{detail.name}</h2>
                  <div className="types">
                    {detail.types.map((t) => (
                      <span key={t} className={`type-badge type-${t}`}>
                        {t}
                      </span>
                    ))}
                  </div>
                  <button
                    className={`fav-btn ${favorites.has(detail.id) ? "active" : ""}`}
                    style={{ position: "static", fontSize: "1.5rem", opacity: 1 }}
                    onClick={(e) => toggleFav(detail.id, e)}
                  >
                    {favorites.has(detail.id)
                      ? "★ Remove Favorite"
                      : "☆ Add Favorite"}
                  </button>
                </div>

                <div className="info">
                  <p>
                    <strong>Height:</strong> {detail.height / 10}m{" "}
                    <strong>Weight:</strong> {detail.weight / 10}kg
                  </p>
                  <p>
                    <strong>Abilities:</strong>{" "}
                    {detail.abilities
                      .map((a) => a.replace("-", " "))
                      .join(", ")}
                  </p>
                </div>

                <div className="stats">
                  {Object.entries(detail.stats).map(([name, val]) => (
                    <div key={name} className="stat-row">
                      <span className="stat-name">
                        {name.replace("special-", "sp. ")}
                      </span>
                      <div className="stat-bar">
                        <div
                          className="stat-fill"
                          style={{ width: `${Math.min(100, (val / 255) * 100)}%` }}
                        />
                      </div>
                      <span className="stat-val">{val}</span>
                    </div>
                  ))}
                </div>

                {detail.flavor_text && (
                  <p className="flavor">{detail.flavor_text}</p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
