# Project Architecture Rules (Non-Obvious Only)

- Authentication uses OAuth2 Client Credentials (`/oauth/token`) with token persistence on the `BWLSearchApp` instance (`self._token`), lazily populated on first request and invalidated on 401/403.
- Process hierarchy resolution in `has_mandatory_metadata()` traverses through four fallback paths to locate the root activity node: `items[processId]["rootActivityID"]`, `items[*]["rootActivityID"]`, `process[processId]["rootActivityID"]`, and direct `process["rootActivityID"]`.
- Process compliance verification requires an additional `fetch_process_data()` call per process returned in search results to retrieve full metadata items.
- PDF diagram generation uses `fitz.open(stream=pdf_bytes, filetype="pdf")` and converts each page to PNG at 120 DPI, stacked vertically inside a Tkinter `Canvas` with scrollable viewports.
