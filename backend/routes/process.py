"""
Process route for the Blueworks Live FastAPI backend.

Thin wrapper around fetch_process_data() from backend.routes.search.

Exposes:
  GET /api/process/{process_id} — returns raw process data JSON.
"""

import requests
from fastapi import APIRouter, HTTPException

from backend.auth import get_token, invalidate_token
from backend.routes.search import fetch_process_data

router = APIRouter()


@router.get("/process/{process_id}")
def get_process(process_id: str) -> dict:
    """Return raw process data JSON for the given process ID."""
    token = get_token()
    try:
        return fetch_process_data(token, process_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            invalidate_token()
            raise HTTPException(status_code=401, detail="Upstream authentication failed")
        raise
