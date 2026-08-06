# E-Commerce Documentary Lab

## What this project does

This is a small full-stack marketplace demo: a Node/Express **backend** serves a
product catalog (apparel and footwear) over a REST API, and a React (Vite)
**frontend** consumes that API to render a searchable, filterable product grid
plus curated "collections" (highlight lists grouped by category).

It doubles as a **codebase-understanding lab** ("Module 4 · Codebase
Understanding" per the UI header): the code is intentionally small and
readable so that the two-layer flow — `route → controller → service → data`
on the backend, and `fetch → state → render` on the frontend — is easy to
trace end to end. The frontend even ships with a "Prompt strategy log" panel
that models how to ask an AI assistant (e.g. Claude) to explain the code at
function-level vs. folder-level granularity.

**Objective of the complete project:** give a learner (or an AI assistant) a
realistic, self-contained example of a REST API + SPA client pair to read,
run, and explain — not a production storefront. There is no database,
authentication, cart, or checkout; catalog data is a static JSON file and all
"business logic" is a handful of pure filtering/lookup functions.

## Architecture

```
ecommerce-documentary/
├── backend/                        Express REST API (port 4000)
│   └── src/
│       ├── server.js               App bootstrap: middleware + router mounting
│       ├── routes/products.js      Maps HTTP verbs/paths to controller functions
│       ├── controllers/
│       │   └── productsController.js   Translates HTTP req/res <-> service calls
│       ├── services/
│       │   └── inventoryService.js     Business logic: filter/lookup over catalog.json
│       └── data/catalog.json       Static product catalog (the "database")
└── frontend/                       React 18 + Vite SPA (port 5173 by default)
    └── src/
        ├── main.jsx                React entry point, mounts <App/>
        ├── App.jsx                 Single page: fetches catalog + collections, renders UI
        └── styles.css              Page styling
```

Request flow: **Browser → `App.jsx` (`fetch`) → Express `server.js` → `routes/products.js`
→ `productsController.js` → `inventoryService.js` → `catalog.json`** and back.

## How to run it

Two terminals — the backend and frontend are independent processes.

### 1. Backend API

```bash
cd backend
npm install
npm start        # plain node (recommended)
# or: npm run dev   # uses nodemon for auto-restart on change —
#                      nodemon isn't a listed dependency, so install it
#                      globally first (`npm i -g nodemon`) or add it to
#                      backend/package.json devDependencies
```

Starts the API at `http://localhost:4000` (override with the `PORT` env var).

### 2. Frontend app

```bash
cd frontend
npm install
npm run dev
```

Starts the Vite dev server (default `http://localhost:5173`). The frontend
calls the API at `http://localhost:4000/api` by default; override with a
`VITE_API_URL` env var (see `App.jsx`) if the backend runs elsewhere.

Open the printed Vite URL in a browser — the catalog grid loads once the
backend is also running.

## API reference

All routes are mounted under `/api` (`server.js`).

| Method | Path | Query params | Description |
|---|---|---|---|
| GET | `/api/products` | `category`, `q` | List products, optionally filtered by category (exact match, case-insensitive) and/or a keyword matched against product name and tags |
| GET | `/api/products/:id` | — | Fetch a single product by id; `404` if not found |
| GET | `/api/collections` | — | Two curated lists ("Apparel Highlights", "Footwear Spotlight") built from the same catalog |

Any undefined route returns a `404` with a JSON error body (`server.js`).

## Functions and their objectives

### Backend

**`server.js`**
- Bootstraps the Express app: enables CORS and JSON body parsing, mounts the
  products router at `/api`, and adds a catch-all `404` handler for undefined
  routes. Starts listening on `PORT` (default `4000`).

**`routes/products.js`**
- Pure routing table — no logic. Wires `GET /products`, `GET /products/:id`,
  and `GET /collections` to their controller functions.

**`controllers/productsController.js`** — the HTTP-facing layer; each function
translates a request into a service call and shapes the JSON response:
- `listProducts(req, res)` — reads `category`/`q` from the query string, calls
  `inventoryService.listProducts()`, and responds with `{ count, results }`.
- `getProductById(req, res)` — looks up one product by `req.params.id`;
  responds `404` if the service returns nothing, otherwise returns the full
  product object.
- `listCollections(req, res)` — returns the curated collection lists as-is.

**`services/inventoryService.js`** — the actual business logic, decoupled
from HTTP:
- `listProducts(filters)` — filters `catalog.products` by `category` (exact,
  case-insensitive) and/or `q` (substring match against name or tags), then
  projects each result down to `{ id, name, price, category, inventory }`
  (description/type/tags are dropped from list responses).
- `getProductById(id)` — returns the full matching product object, or
  `undefined`.
- `listCollections()` — partitions the catalog into `Apparel` and `Footwear`
  groups and returns just `{ id, name }` per item, for lightweight highlight
  lists.

### Frontend (`App.jsx`)

- **`fetchCatalog` (inside a `useEffect`)** — builds a query string from the
  `category`/`query` state, calls `GET /api/products`, and updates `products`
  and a human-readable `status` message. Re-runs whenever `category` or
  `query` changes, so typing/selecting live-filters the grid.
- **Second `useEffect`** — fetches `GET /api/collections` once on mount to
  populate the "Collections" panel.
- **`inventorySummary` (via `useMemo`)** — derives the total item count and
  summed inventory across the currently displayed `products`, recomputed only
  when `products` changes.
- **JSX render body** — three panels: a catalog grid with category/keyword
  filter controls, a collections panel, and a static "Prompt strategy log"
  panel documenting example function-level vs. folder-level prompts for
  exploring this codebase with an AI assistant.

## Data model

`backend/src/data/catalog.json` holds an array of products, each with:
`id`, `name`, `category` (`Apparel` | `Footwear`), `type`, `price`,
`inventory` (stock count), `tags` (string array), `description`. This file is
the sole data source — there is no persistence layer to set up.

## Known limitations

- No database, auth, cart, or checkout — read-only catalog browsing only.
- `catalog.json` is loaded once at process start; changes require a backend
  restart to take effect.
- No automated tests are included in either package.
