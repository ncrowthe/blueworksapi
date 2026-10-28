"""
Glossary route for the Blueworks Live FastAPI backend.

Ported from bwl_search.py fetch_glossary() at lines 219–234.

Exposes:
  GET /api/glossary — returns the Blueworks Live glossary as JSON.
"""

import requests
from fastapi import APIRouter, HTTPException

from backend.auth import get_token, invalidate_token
from backend.config import GLOSSARY_URL

router = APIRouter()


# ---------------------------------------------------------------------------
# Business-logic helper
# ---------------------------------------------------------------------------

def fetch_glossary(token: str):
    """Call the Glossary API and return the parsed JSON."""
    resp = requests.get(
        GLOSSARY_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept":        "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        raise ValueError(
            "Glossary response was not JSON (Content-Type: "
            + resp.headers.get("Content-Type", "unknown") + ")"
        )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get("/glossary")
def get_glossary():
    """Return the Blueworks Live glossary as JSON."""
    token = get_token()
    try:
        return fetch_glossary(token)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            invalidate_token()
            raise HTTPException(status_code=401, detail="Upstream authentication failed")
        raise
