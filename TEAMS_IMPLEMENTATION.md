# Pokemon Teams Feature — Implementation Reference

## Status: Not yet started

---

## Design Decisions (finalized)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Team naming | User-provided name (required at creation) |
| 2 | Renaming teams | Allowed via inline edit |
| 3 | Deleting teams | Full deletion (team + members) |
| 4 | Active team concept | Single active team, dropdown switcher |
| 5 | Adding Pokémon | Button on each Pokémon card only (not in detail modal) |
| 6 | Team full behavior | Disable "Add to team" button at 6, no modal |
| 7 | Duplicate Pokémon | Disallowed within a team |
| 8 | Removing members | From team view only |
| 9 | Team view placement | New top-level tab ("Teams") |
| 10 | Type coverage basis | Pokémon types only (not movesets) |
| 11 | Type data source | Fetched from PokeAPI at startup, cached in memory |
| 12 | Coverage computation | Backend (`GET /api/teams/{id}/coverage`) |
| 13 | Team switcher UI | Dropdown at top of Teams tab |
| 14 | Max teams | 5 |
| 15 | Member ordering | No ordering — insertion order only, no reorder UI |

---

## Type Coverage Definitions

- **Strong against**: ≥1 team member's type deals super-effective (2×) damage to that type
- **Weak against**: the entire team takes super-effective damage from that type (full vulnerability)
- **No coverage**: no team member can hit that type super-effectively

---

## Database Schema

```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    pokemon_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sprite TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, pokemon_id)
);
```

---

## API Endpoints

| Method | Path | Description | Constraints |
|--------|------|-------------|-------------|
| `GET` | `/api/teams` | List all teams (id, name, member count) | — |
| `POST` | `/api/teams` | Create team with name | Max 5 teams; 409 if at limit |
| `PATCH` | `/api/teams/{id}` | Rename team | 404 if not found |
| `DELETE` | `/api/teams/{id}` | Delete team + all members | 404 if not found |
| `GET` | `/api/teams/{id}` | Get team with full member list | 404 if not found |
| `POST` | `/api/teams/{id}/members/{pokemon_id}` | Add Pokémon to team | Max 6 members; 409 if duplicate; fetches name/sprite from PokeAPI |
| `DELETE` | `/api/teams/{id}/members/{pokemon_id}` | Remove Pokémon from team | 404 if not found |
| `GET` | `/api/teams/{id}/coverage` | Type coverage summary | Returns `{strong, weak, no_coverage}` |

---

## Frontend Plan

### State to add to App.jsx
```javascript
const [teams, setTeams] = useState([]);           // all teams (id, name, member_count)
const [activeTeamId, setActiveTeamId] = useState(null);
const [activeTeam, setActiveTeam] = useState(null); // full team with members
const [coverage, setCoverage] = useState(null);   // {strong, weak, no_coverage}
```

### New UI elements
- **"Teams" tab** in top nav alongside "All Pokémon" and "Favorites"
- **Team view**:
  - Dropdown to select active team
  - "New Team" button (disabled + tooltip at 5 teams)
  - Inline rename for active team name
  - Delete team button
  - Member grid (sprite + name + remove button per member)
  - Type coverage section below grid
- **Card-level button**: "Add to team" (➕ or similar icon)
  - Disabled when active team is full (6) or Pokémon already on team
  - Only shown when a team exists

---

## Implementation Order

### Phase 1 — Backend
- [ ] Update `database.py`: add `teams` and `team_members` tables to `init_db()`
- [ ] Update `pokeapi.py`: build and cache type effectiveness chart at startup
- [ ] Create `backend/routes/teams.py` with all 8 endpoints
- [ ] Update `main.py`: register teams router
- [ ] Update `schemas.py`: add Pydantic models for teams

### Phase 2 — Frontend
- [ ] Add team state variables to `App.jsx`
- [ ] Add `loadTeams()` and `loadActiveTeam()` fetch helpers
- [ ] Add "Add to team" button on Pokémon cards
- [ ] Add "Teams" tab to nav
- [ ] Build Teams view (switcher, member grid, coverage display)

### Phase 3 — Tests
- [ ] `backend/tests/test_teams.py`: CRUD + constraint tests
- [ ] Coverage endpoint tests

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/database.py` | Edit — add teams/team_members tables |
| `backend/pokeapi.py` | Edit — add type chart cache |
| `backend/routes/teams.py` | Create |
| `backend/main.py` | Edit — register teams router |
| `backend/schemas.py` | Edit — add team schemas |
| `backend/tests/test_teams.py` | Create |
| `frontend/src/App.jsx` | Edit — teams state + UI |
| `frontend/src/style.css` | Edit — teams tab + coverage styles |
