"""
Diagram route for the Blueworks Live FastAPI backend.

Ported from bwl_search.py fetch_diagram() at line 207.

Exposes:
  GET /api/diagram/{process_id} — streams the PrintDiagram PDF as a download.
"""

import io

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.auth import get_token, invalidate_token
from backend.config import DIAGRAM_URL

router = APIRouter()


# ---------------------------------------------------------------------------
# Business-logic helper
# ---------------------------------------------------------------------------

def fetch_diagram(token: str, process_id: str) -> bytes:
    """Fetch the PrintDiagram PDF for the given process ID and return raw bytes."""
    resp = requests.get(
        DIAGRAM_URL,
        headers={"Authorization": "Bearer " + token},
        params={"processId": process_id},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get("/diagram/{process_id}")
def get_diagram(process_id: str) -> StreamingResponse:
    """Return the PDF diagram for the given process as a file download."""
    token = get_token()
    try:
        pdf_bytes = fetch_diagram(token, process_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            invalidate_token()
            raise HTTPException(status_code=401, detail="Upstream authentication failed")
        raise
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="diagram.pdf"'},
    )
