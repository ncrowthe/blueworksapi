# Project Coding Rules (Non-Obvious Only)

- All HTTP requests (`requests.get`/`requests.post`) must be executed inside `threading.Thread(target=..., daemon=True)` to prevent freezing the Tkinter main loop.
- Never manipulate Tkinter widgets directly from background threads; always marshal updates back to the UI thread using `self.after(0, callback)`.
- When rendering PDF pages via PyMuPDF (`fitz`), keep references to all `tkinter.PhotoImage` objects in an instance attribute on the window (`win._diagram_images`), otherwise Tkinter garbage-collects the images and renders blank shapes.
- `MANDATORY_METADATA` in `config.ini` can be specified as a JSON list (e.g. `["businessOwners", "Inputs"]`) or comma-separated string; parsing supports both formats.
- Node compliance validation in `check_node_compliance()` must test three case variations (`field`, `lowerCamelCase`, and `lowercase`) before marking a metadata field missing.
- When `requests.HTTPError` is caught in `_do_search()` / `_do_glossary()`, check for status codes 401/403 to invalidate `self._token` so subsequent attempts re-authenticate automatically.
