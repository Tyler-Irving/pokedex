import { useState, useEffect, useCallback, useRef } from "react";

const PAGE_SIZE = 20;
const API_KEY = import.meta.env.VITE_API_KEY ?? "";
const STAT_NAMES = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"];

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
  const [error, setError] = useState(null);
  const [showShiny, setShowShiny] = useState(false);
  const [encounters, setEncounters] = useState(null); // null = loading, [] = none
  const [compareIds, setCompareIds] = useState(new Set());
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const pendingFavs = useRef(new Set());

  // Fetch types on mount
  useEffect(() => {
    fetch("/api/types", { headers: { "X-API-Key": API_KEY } })
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load types: ${r.status}`);
        return r.json();
      })
      .then((d) => setTypes(d.types))
      .catch((err) => console.error(err));
  }, []);

  // Fetch favorites set
  const loadFavorites = useCallback(() => {
    fetch("/api/favorites", { headers: { "X-API-Key": API_KEY } })
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load favorites: ${r.status}`);
        return r.json();
      })
      .then((d) => {
        setFavList(d.favorites);
        setFavorites(new Set(d.favorites.map((f) => f.pokemon_id)));
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
      });
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  // Fetch pokemon list
  useEffect(() => {
    if (view !== "list") return;
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(PAGE_SIZE),
    });
    if (search) params.set("search", search);
    if (typeFilter) params.set("type", typeFilter);

    fetch(`/api/pokemon?${params}`, { headers: { "X-API-Key": API_KEY } })
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load Pokémon: ${r.status}`);
        return r.json();
      })
      .then((d) => {
        setPokemon(d.results);
        setTotal(d.total);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, [offset, search, typeFilter, view]);

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [search, typeFilter]);

  // Fetch detail + encounters
  useEffect(() => {
    if (selected == null) {
      setDetail(null);
      setShowShiny(false);
      setEncounters(null);
      return;
    }
    setDetail(null);
    setShowShiny(false);
    setEncounters(null);

    fetch(`/api/pokemon/${selected}`, { headers: { "X-API-Key": API_KEY } })
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load Pokémon detail: ${r.status}`);
        return r.json();
      })
      .then(setDetail)
      .catch((err) => {
        console.error(err);
        setSelected(null);
      });

    fetch(`/api/pokemon/${selected}/encounters`, { headers: { "X-API-Key": API_KEY } })
      .then((r) => (r.ok ? r.json() : []))
      .then(setEncounters)
      .catch(() => setEncounters([]));
  }, [selected]);

  const toggleFav = async (id, e) => {
    e?.stopPropagation();
    if (pendingFavs.current.has(id)) return;
    pendingFavs.current.add(id);
    try {
      const method = favorites.has(id) ? "DELETE" : "POST";
      const r = await fetch(`/api/favorites/${id}`, {
        method,
        headers: { "X-API-Key": API_KEY },
      });
      if (!r.ok) throw new Error(`Failed to update favorite: ${r.status}`);
      loadFavorites();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      pendingFavs.current.delete(id);
    }
  };

  const toggleCompare = (id, e) => {
    e?.stopPropagation();
    setCompareIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < 6) {
        next.add(id);
      }
      return next;
    });
  };

  const runCompare = async () => {
    if (compareIds.size < 2) return;
    setCompareLoading(true);
    setCompareData(null);
    try {
      const r = await fetch(`/api/compare?ids=${[...compareIds].join(",")}`, {
        headers: { "X-API-Key": API_KEY },
      });
      if (!r.ok) throw new Error("Failed to compare Pokémon");
      setCompareData(await r.json());
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setCompareLoading(false);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  const renderCard = (p, id, name, sprite) => (
    <div
      key={id}
      className={`card${compareIds.has(id) ? " in-compare" : ""}`}
      onClick={() => setSelected(id)}
    >
      <button
        className={`cmp-btn ${compareIds.has(id) ? "active" : ""}`}
        title={compareIds.has(id) ? "Remove from compare" : "Add to compare"}
        onClick={(e) => toggleCompare(id, e)}
      >
        ⚔
      </button>
      <button
        className={`fav-btn ${favorites.has(id) ? "active" : ""}`}
        onClick={(e) => toggleFav(id, e)}
      >
        {favorites.has(id) ? "★" : "☆"}
      </button>
      <img src={sprite} alt={name} />
      <div className="id">#{String(id).padStart(3, "0")}</div>
      <div className="name">{name}</div>
    </div>
  );

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
          onClick={() => { setView("favorites"); setSearch(""); setTypeFilter(""); }}
        >
          Favorites ({favorites.size})
        </button>
        {compareIds.size >= 2 && (
          <button onClick={runCompare} className="compare-nav-btn">
            Compare ({compareIds.size})
          </button>
        )}
        {compareIds.size > 0 && (
          <button onClick={() => setCompareIds(new Set())} className="clear-compare-btn">
            Clear
          </button>
        )}
      </nav>

      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}

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
                {pokemon.map((p) => renderCard(p, p.id, p.name, p.sprite))}
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
              {favList.map((p) =>
                renderCard(p, p.pokemon_id, p.name, p.sprite)
              )}
            </div>
          )}
        </>
      )}

      {/* Detail modal */}
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
                  <img
                    src={showShiny && detail.sprite_shiny ? detail.sprite_shiny : detail.sprite}
                    alt={detail.name}
                  />
                  <h2>{detail.name}</h2>
                  <div className="types">
                    {detail.types.map((t) => (
                      <span key={t} className={`type-badge type-${t}`}>
                        {t}
                      </span>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", justifyContent: "center", marginTop: "0.5rem", flexWrap: "wrap" }}>
                    {detail.sprite_shiny && (
                      <button
                        className={`shiny-btn ${showShiny ? "active" : ""}`}
                        onClick={() => setShowShiny((s) => !s)}
                      >
                        {showShiny ? "✨ Shiny" : "✨ Normal"}
                      </button>
                    )}
                    <button
                      className={`fav-btn ${favorites.has(detail.id) ? "active" : ""}`}
                      style={{ position: "static", fontSize: "1.5rem", opacity: 1 }}
                      onClick={(e) => toggleFav(detail.id, e)}
                    >
                      {favorites.has(detail.id) ? "★ Remove Favorite" : "☆ Add Favorite"}
                    </button>
                  </div>
                </div>

                <div className="info">
                  <p>
                    <strong>Height:</strong> {detail.height / 10}m{" "}
                    <strong>Weight:</strong> {detail.weight / 10}kg
                  </p>
                  <p>
                    <strong>Abilities:</strong>{" "}
                    {detail.abilities.map((a) => a.replace("-", " ")).join(", ")}
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

                <div className="encounters">
                  <h3>Wild Encounters</h3>
                  {encounters == null ? (
                    <p style={{ color: "#718096", fontSize: "0.85rem" }}>Loading locations...</p>
                  ) : encounters.length === 0 ? (
                    <p style={{ color: "#a0aec0", fontSize: "0.85rem" }}>Not found in the wild.</p>
                  ) : (
                    <ul>
                      {encounters.map((enc) => (
                        <li key={enc.location_area.name}>
                          {enc.location_area.name.replace(/-/g, " ")}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Compare modal */}
      {compareData != null && (
        <div className="compare-overlay" onClick={() => setCompareData(null)}>
          <div className="compare-panel" onClick={(e) => e.stopPropagation()}>
            <button className="close" onClick={() => setCompareData(null)}>×</button>
            <h2 style={{ marginBottom: "1rem" }}>Stat Comparison</h2>
            {compareLoading ? (
              <div className="loading">Loading...</div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table className="compare-table">
                  <thead>
                    <tr>
                      <th className="stat-label"></th>
                      {compareData.pokemon.map((p) => (
                        <th key={p.id}>
                          <img
                            src={`https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${p.id}.png`}
                            alt={p.name}
                            style={{ width: 64, height: 64, imageRendering: "pixelated" }}
                          />
                          <div style={{ textTransform: "capitalize" }}>{p.name}</div>
                          <div style={{ display: "flex", gap: "0.2rem", justifyContent: "center", flexWrap: "wrap", marginTop: "0.25rem" }}>
                            {p.types.map((t) => (
                              <span key={t} className={`type-badge type-${t}`}>{t}</span>
                            ))}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {STAT_NAMES.map((stat) => (
                      <tr key={stat}>
                        <td className="stat-label">{stat.replace("special-", "sp. ")}</td>
                        {compareData.pokemon.map((p) => (
                          <td
                            key={p.id}
                            className={compareData.best_in_stat[stat] === p.name ? "best" : ""}
                          >
                            {p.stats[stat] ?? "—"}
                            {compareData.best_in_stat[stat] === p.name && " ★"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {compareLoading && compareData == null && (
        <div className="compare-overlay">
          <div className="compare-panel">
            <div className="loading">Comparing...</div>
          </div>
        </div>
      )}
    </div>
  );
}
