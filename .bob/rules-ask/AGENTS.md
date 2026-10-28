# Project Documentation Context (Non-Obvious Only)

- The entire client application is encapsulated in a single file `bwl_search.py` with no subpackages.
- The results Treeview defines 6 columns (`name`, `id`, `type`, `space`, `activities`, `compliance`), but `displaycolumns` explicitly hides `id` from user view while retaining it for selection event retrieval.
- `json_to_table()` in glossary fetching explicitly whitelists and displays only `["name", "category", "added-by-user"]`; all other dictionary keys in glossary items are ignored.
- Blueworks Live API versions are hardcoded in endpoint URLs (`?version=20191214` for Search and ProcessData endpoints).
- Search query targets space names rather than process names (`searchFieldName="space_name"` in `search_bwl()`).
