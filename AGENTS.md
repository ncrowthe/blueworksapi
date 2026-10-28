# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Commands
- Run application: `python bwl_search.py` (or `.\.venv\Scripts\python bwl_search.py` on Windows)
- Install dependencies: `pip install -r requirements.txt`
- Syntax / byte-compile check: `python -m py_compile bwl_search.py`
- Run single test (unittest): `python -m unittest tests.test_module.TestClass.test_method`
- Run all tests: `python -m unittest discover`

## Code Style & Conventions
- **Configuration**: `config.ini` must reside alongside `bwl_search.py`; missing file triggers fatal `FileNotFoundError` on startup.
- **Threading & UI Safety**: Network calls (`requests`) must run on daemon background threads (`threading.Thread(..., daemon=True)`). Any UI mutation must be dispatched back to the main thread via `self.after(0, ...)`.
- **Tkinter Image Retention**: PyMuPDF-rendered `PhotoImage` instances must be appended to an explicit list and stored on the window object (e.g. `setattr(win, "_diagram_images", images)`) to prevent Python garbage collection from blanking the canvas.
- **Metadata Compliance**: Metadata field keys in `check_node_compliance()` must be checked across exact, leading-lowercase camelCase, and all-lowercase variants.
- **Treeview Column Configuration**: Treeview internal columns include `"id"` for data binding, but `"id"` is excluded from `displaycolumns`.
- **Token Invalidation**: Catch `requests.HTTPError` with status codes 401/403 to reset `self._token = None` and update `_auth_indicator`.
