# React Carbon Migration Plan

## Overview

Migrate the Blueworks Live desktop search tool (`bwl_search.py`, Tkinter) to a web application built with **React + Carbon Design System** on the frontend and **Python FastAPI** on the backend, deployed as a **single container on IBM Cloud Code Engine**.

### Scope
- Port all existing features: process search, compliance checking, glossary viewer, PDF diagram download
- Replace Tkinter desktop UI with Carbon Design System React components
- Replace direct API calls from the desktop app with REST endpoints exposed by FastAPI
- Deploy as a single container (FastAPI serves both the API and the built React SPA)
- Secrets injected via Code Engine environment variables — no credentials in files

### Non-goals
- No user authentication / login flow (URL-based access control is sufficient)
- No inline PDF rendering (download-only)
- No changes to existing Blueworks Live API integration logic
- No new features beyond what exists today

### Repo Layout (Target)
```
blueworksapi/
├── backend/
│   ├── main.py              # FastAPI app, mounts static files, registers routes
│   ├── auth.py              # OAuth token acquisition and caching
│   ├── routes/
│   │   ├── search.py        # POST /api/search
│   │   ├── process.py       # GET /api/process/{process_id}
│   │   ├── diagram.py       # GET /api/diagram/{process_id}
│   │   └── glossary.py      # GET /api/glossary
│   ├── compliance.py        # check_node_compliance / has_mandatory_metadata
│   ├── config.py            # Reads CLIENT_ID, CLIENT_SECRET, MANDATORY_METADATA from env
│   └── requirements.txt     # fastapi, uvicorn, requests, python-dotenv
├── frontend/
│   ├── index.html
│   ├── package.json         # Vite + React + @carbon/react
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/
│       │   ├── SearchBar.jsx
│       │   ├── ResultsTable.jsx
│       │   ├── GlossaryModal.jsx
│       │   └── DiagramDownload.jsx
│       └── api/
│           └── client.js    # fetch wrappers for backend endpoints
├── Dockerfile
├── .dockerignore
└── bwl_search.py            # Original file — kept, not deleted
```

---

## Sub-Tasks

---

### Sub-Task 1 — Scaffold Repository Structure

**Status:** `[ ] pending`

**Intent:**
Create the `backend/` and `frontend/` directory skeletons so subsequent sub-tasks have a clear home. No logic is written here — only empty directories, placeholder files, and dependency manifests.

**Expected Outcomes:**
- `backend/` directory exists with `requirements.txt` listing `fastapi`, `uvicorn[standard]`, `requests`, `python-dotenv`
- `frontend/` directory exists as a Vite + React project (initialised via `npm create vite@latest`)
- `@carbon/react` and `@carbon/icons-react` added to `frontend/package.json`
- All existing files (`bwl_search.py`, `config.ini`, etc.) remain untouched

**Todo List:**
- [ ] Create `backend/` directory with empty `__init__.py`, `requirements.txt`, and stub `main.py`
- [ ] Create `backend/routes/` directory with empty `__init__.py`
- [ ] Run `npm create vite@latest frontend -- --template react` (or equivalent manual scaffold) to create the `frontend/` project
- [ ] Add `@carbon/react`, `@carbon/icons-react`, `sass` to `frontend/package.json` dependencies
- [ ] Run `npm install` inside `frontend/`
- [ ] Verify `frontend/node_modules` is in `.gitignore`

**Relevant Context:**
- Vite is preferred over Create React App for faster builds and smaller output
- Carbon requires Sass (`sass` package) for style compilation
- `@carbon/react` v1.x targets Carbon Design System v11

---

### Sub-Task 2 — FastAPI Backend Core

**Status:** `[ ] pending`

**Intent:**
Build the FastAPI application skeleton: configuration loading from environment variables, OAuth token acquisition/caching, a health-check endpoint, and static file serving of the React build. This is the foundation all API routes depend on.

**Expected Outcomes:**
- `backend/config.py` reads `CLIENT_ID`, `CLIENT_SECRET`, `MANDATORY_METADATA` from environment variables (with a fallback `.env` file for local development)
- `backend/auth.py` provides a `get_token()` function that caches the bearer token in memory and refreshes on 401/403
- `backend/main.py` starts a FastAPI app, registers a `GET /api/health` endpoint, and mounts `frontend/dist` at `/` as static files
- Running `uvicorn backend.main:app` starts the server without errors (health endpoint returns `{"status": "ok"}`)

**Todo List:**
- [ ] Write `backend/config.py`: load env vars using `os.environ`; parse `MANDATORY_METADATA` as JSON with comma-separated fallback (mirrors existing logic at lines 24–34 of `bwl_search.py`)
- [ ] Write `backend/auth.py`: port `get_token()` from `bwl_search.py` (line 44); store cached token in a module-level variable; expose `invalidate_token()` helper; remove Tkinter-specific auth indicator logic
- [ ] Write `backend/main.py`: create FastAPI app; add `/api/health`; mount `StaticFiles` at `/` pointing to `frontend/dist` with `html=True`
- [ ] Write `backend/requirements.txt` with pinned minimum versions

**Relevant Context:**
- Original `get_token()` is at line 44 of `bwl_search.py`; it POSTs to `https://ibm.blueworkslive.com/oauth/token`
- Config keys in `config.ini`: `client_id`, `client_secret`, `mandatory_metadata` → become env vars `CLIENT_ID`, `CLIENT_SECRET`, `MANDATORY_METADATA`
- Token caching pattern: module-level `_token = None`; set on first call; reset to `None` on 401/403 (see `_do_search()` at line 458 in `bwl_search.py`)
- `StaticFiles(directory="frontend/dist", html=True)` serves `index.html` as fallback for SPA routing

---

### Sub-Task 3 — API Routes

**Status:** `[ ] pending`

**Intent:**
Port all four Blueworks Live API interactions from `bwl_search.py` into FastAPI route modules. Each route is a thin HTTP handler that delegates to ported business logic.

**Expected Outcomes:**
- `POST /api/search` — accepts `{ "query": "string" }`, returns list of process results with compliance status
- `GET /api/process/{process_id}` — returns raw process data JSON (used internally; exposed for future use)
- `GET /api/diagram/{process_id}` — returns the PDF as a streaming response with `Content-Type: application/pdf` and `Content-Disposition: attachment`
- `GET /api/glossary` — returns the glossary as JSON
- `backend/compliance.py` contains the ported `check_node_compliance()` and `has_mandatory_metadata()` functions
- All routes invalidate the cached token and return HTTP 401 to the caller on upstream 401/403

**Todo List:**
- [ ] Write `backend/compliance.py`: port `check_node_compliance()` (line 64) and `has_mandatory_metadata()` (line 84) verbatim; remove any UI dependencies
- [ ] Write `backend/routes/search.py`: port `search_bwl()` (line 154) and `fetch_process_data()` (line 139); expose as `POST /api/search`; response model: `list[ProcessResult]`
- [ ] Write `backend/routes/diagram.py`: port `fetch_diagram()` (line 207); expose as `GET /api/diagram/{process_id}`; return `StreamingResponse` with PDF bytes
- [ ] Write `backend/routes/glossary.py`: port `fetch_glossary()` (line 219); expose as `GET /api/glossary`
- [ ] Write `backend/routes/process.py`: thin wrapper around `fetch_process_data()`; expose as `GET /api/process/{process_id}`
- [ ] Register all routers in `backend/main.py` under the `/api` prefix
- [ ] Verify all routes reuse `get_token()` from `backend/auth.py` and call `invalidate_token()` on 401/403

**Relevant Context:**
- `search_bwl()` at line 154: iterates spaces → processes → milestones → activities; calls `fetch_process_data()` per process for compliance; returns `[{name, id, type, space, activities, compliance}]`
- `check_node_compliance()` at line 64: 3-variant field name matching (exact, lowercase-first camelCase, all-lowercase)
- `has_mandatory_metadata()` at line 84: four fallback paths for root activity node traversal (documented in AGENTS.md)
- Diagram endpoint must set `Content-Disposition: attachment; filename="diagram.pdf"` so the browser triggers a download
- The `requests.HTTPError` 401/403 pattern is in `_do_search()` at lines 458–461

---

### Sub-Task 4 — React + Carbon Scaffold

**Status:** `[ ] pending`

**Intent:**
Wire up the React application shell: Carbon `Theme` provider, top-level layout, navigation header with the "Glossary" trigger, and a thin API client module. No feature screens are built here — only the frame they will live in.

**Expected Outcomes:**
- `frontend/src/main.jsx` renders `<App />` wrapped in a Carbon `Theme` (g10 or white)
- `frontend/src/App.jsx` renders a Carbon `Header` with the app title and a "Glossary" nav item
- `frontend/src/api/client.js` exports `searchProcesses(query)`, `fetchGlossary()`, and `downloadDiagram(processId)` functions that call the FastAPI backend
- Running `npm run dev` inside `frontend/` starts the Vite dev server; proxying `/api/*` to `http://localhost:8000` so backend and frontend can be developed independently
- `npm run build` produces a `frontend/dist/` folder

**Todo List:**
- [ ] Configure `vite.config.js` to proxy `/api` to `http://localhost:8000` in dev mode
- [ ] Write `frontend/src/main.jsx`: import Carbon global styles (`@carbon/react/scss/globals`); wrap app in `<Theme theme="g10">`
- [ ] Write `frontend/src/App.jsx`: use Carbon `Header`, `HeaderName`, `HeaderNavigation`, `HeaderMenuItem` for the top bar; include a state hook `showGlossary` that opens the glossary modal (wired up in Sub-Task 6)
- [ ] Write `frontend/src/api/client.js`: implement `searchProcesses`, `fetchGlossary`, `downloadDiagram` using the browser `fetch` API; handle non-OK responses by throwing with the status text

**Relevant Context:**
- Carbon Design System v11 component imports: `import { Header, Theme, ... } from "@carbon/react"`
- Carbon global Sass entry point: `@use "@carbon/react"` in a root `.scss` file
- Vite proxy config: `server.proxy["/api"] = { target: "http://localhost:8000", changeOrigin: true }`
- `downloadDiagram(processId)` should fetch the PDF blob and trigger a browser download using a temporary anchor element with `URL.createObjectURL`

---

### Sub-Task 5 — Search UI

**Status:** `[ ] pending`

**Intent:**
Build the main search screen: a search input with a submit button, a results `DataTable` showing name/type/space/activities/compliance, and compliance row highlighting. This replicates the core of `_build_ui()`, `_on_search()`, and `_populate_results()` in the original app.

**Expected Outcomes:**
- `frontend/src/components/SearchBar.jsx` renders a Carbon `Search` input and a `Button` ("Search"); triggers the search on button click or Enter key
- `frontend/src/components/ResultsTable.jsx` renders a Carbon `DataTable` with columns: Name, Type, Space, Activities, Compliance; the Compliance cell renders a Carbon `Tag` (green = Compliant, red = Non-compliant)
- A loading `InlineLoading` spinner is shown while the search is in progress
- Result count is shown below the table (e.g. "12 results found")
- Selecting a row (checkbox or row click) enables a "Download Diagram" button (wired up in Sub-Task 7)
- The search field defaults to empty (the default value "000 Test Space" in the original is environment-specific and should be removed)

**Todo List:**
- [ ] Write `frontend/src/components/SearchBar.jsx`: Carbon `Search` + `Button`; accept `onSearch(query)` prop; handle Enter key via `onKeyDown`
- [ ] Write `frontend/src/components/ResultsTable.jsx`: Carbon `DataTable`, `TableContainer`, `Table`, `TableHead`, `TableRow`, `TableHeader`, `TableBody`, `TableCell`; map compliance value to a Carbon `Tag` type (`"green"` / `"red"`); accept `rows`, `onRowSelect` props
- [ ] Update `frontend/src/App.jsx`: add `results`, `loading`, `selectedProcessId` state; wire `SearchBar.onSearch` → `api/client.searchProcesses` → update `results`; pass `onRowSelect` to `ResultsTable`
- [ ] Add `InlineLoading` component to show during API call
- [ ] Add result count label beneath the table

**Relevant Context:**
- Original `_populate_results()` at line 473: tags rows "compliant" (#e8f5e9 green) or "non_compliant" (#ffebee red) based on `compliance` field value
- Original `_search_entry` default value "000 Test Space" is test-environment-specific — do not carry forward
- Carbon `DataTable` docs: rows need `{ id, ...fields }` shape; headers need `{ key, header }` shape
- The hidden `id` column pattern in Treeview (line 511) is replaced by storing the process id in the row data object

---

### Sub-Task 6 — Glossary UI

**Status:** `[ ] pending`

**Intent:**
Build the glossary feature as a Carbon `Modal` dialog containing a `DataTable` with columns Name, Category, Added By. Triggered from the Header nav item added in Sub-Task 4.

**Expected Outcomes:**
- `frontend/src/components/GlossaryModal.jsx` renders a Carbon `Modal` with a `DataTable` inside
- Opening the modal triggers a `GET /api/glossary` call (with a loading state)
- Columns displayed: Name, Category, Added By (matching the `["name", "category", "added-by-user"]` keys from `json_to_table()`)
- Alternating row shading is handled automatically by Carbon DataTable zebra striping (no custom tags needed)
- Modal can be closed via the built-in Carbon close button

**Todo List:**
- [ ] Write `frontend/src/components/GlossaryModal.jsx`: Carbon `Modal` + `DataTable`; fetch glossary on open (not on app load); show `DataTableSkeleton` while loading
- [ ] Update `frontend/src/App.jsx`: pass `showGlossary` state and `setShowGlossary` setter to the Header glossary trigger and `GlossaryModal`

**Relevant Context:**
- Original `_show_glossary()` at line 631: Toplevel with Treeview; alternating odd/even tags
- Original `_do_glossary()` at line 605: fetches glossary then dispatches to main thread
- `json_to_table()` at line 237 filters to keys `["name", "category", "added-by-user"]`
- Carbon `Modal` open state is controlled by `open` prop; `onRequestClose` callback closes it

---

### Sub-Task 7 — Diagram Download

**Status:** `[ ] pending`

**Intent:**
Wire the "Download Diagram" button in the results table to the `GET /api/diagram/{process_id}` endpoint. The backend streams the PDF; the browser saves it as a file download without any inline rendering.

**Expected Outcomes:**
- `frontend/src/components/DiagramDownload.jsx` renders a Carbon `Button` ("Download Diagram") that is disabled when no row is selected
- Clicking the button calls `downloadDiagram(processId)` from `api/client.js`, which fetches the PDF blob and triggers a native browser file download named `diagram-{processId}.pdf`
- A `loading` state disables the button and shows an icon spinner during the fetch
- Errors are surfaced via a Carbon `InlineNotification` (type `"error"`)

**Todo List:**
- [ ] Write `frontend/src/components/DiagramDownload.jsx`: Carbon `Button` with download icon; accept `processId` prop; implement download via `fetch` → `blob()` → `URL.createObjectURL` → temporary `<a>` click pattern
- [ ] Update `frontend/src/App.jsx`: render `<DiagramDownload processId={selectedProcessId} />` below the results table; pass `selectedProcessId` from row selection state
- [ ] Add error notification component for download failures

**Relevant Context:**
- Original `_show_diagram()` at line 536: opens PDF with PyMuPDF and renders pages to canvas — this entire path is replaced by a download
- Original `_do_fetch_diagram()` at line 520: fetches PDF bytes on background thread
- Backend diagram route streams PDF with `Content-Disposition: attachment` header (set up in Sub-Task 3)
- Browser download pattern: `const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = "filename.pdf"; a.click(); URL.revokeObjectURL(url)`

---

### Sub-Task 8 — Dockerfile and IBM Cloud Code Engine Configuration

**Status:** `[ ] pending`

**Intent:**
Package the application as a single container image: build the React SPA, copy the output into the FastAPI container, and document how to deploy to IBM Cloud Code Engine with secrets injected as environment variables.

**Expected Outcomes:**
- `Dockerfile` at repo root performs a two-stage build: Stage 1 builds the React app (`npm run build`); Stage 2 installs Python dependencies and copies the FastAPI backend plus the React `dist/` output
- `.dockerignore` excludes `node_modules`, `__pycache__`, `.venv`, `.bob`, `config.ini`
- `README-deploy.md` documents the Code Engine deployment steps: create application, set secrets (`CLIENT_ID`, `CLIENT_SECRET`, `MANDATORY_METADATA`), point to container image
- Container starts with `uvicorn backend.main:app --host 0.0.0.0 --port 8080`
- Code Engine application listens on port 8080 (Code Engine default)

**Todo List:**
- [ ] Write `Dockerfile`: Stage 1 — `node:20-slim`, copy `frontend/`, run `npm ci && npm run build`; Stage 2 — `python:3.12-slim`, copy `backend/`, install requirements, copy `frontend/dist` to `backend/static/`, set `CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]`
- [ ] Write `.dockerignore`
- [ ] Update `backend/main.py` static files mount path to point to `backend/static/` (the copy destination used in Dockerfile)
- [ ] Write `README-deploy.md` with: `ibmcloud ce application create` command, required env vars / secrets, image build and push steps
- [ ] Verify `Dockerfile` builds cleanly with `docker build -t blueworksapi .`

**Relevant Context:**
- Code Engine requires the container to listen on the port specified in the application config (default 8080)
- Code Engine secrets are set via `ibmcloud ce secret create` and referenced in `ibmcloud ce application create --env-from-secret`
- Two-stage Docker build keeps the final image small (no Node.js runtime in production image)
- `backend/main.py` static files mount must match the directory where `frontend/dist` is copied in Stage 2

---

## Implementation Notes

- The original `bwl_search.py` is **not deleted** — it remains as a reference and fallback
- `config.ini` is **not committed** to the new backend; the backend reads only from environment variables
- All network I/O in the backend is **synchronous** (`requests` library); FastAPI's `run_in_threadpool` or `asyncio.to_thread` should wrap blocking calls if concurrency becomes a concern in future
- The `format_results()` function (line 277 of `bwl_search.py`) is unused in the original — do not port it
