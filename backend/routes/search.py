"""
Search route for the Blueworks Live FastAPI backend.

Ported from bwl_search.py:
  - fetch_process_data() at line 139
  - search_bwl()         at line 154

Exposes:
  POST /api/search  — accepts {"query": "string"}, returns list of process results.
"""

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.auth import get_token, invalidate_token
from backend.compliance import has_mandatory_metadata
from backend.config import AVAILABLE_METADATA_FIELDS, PROCESS_DATA_URL, SEARCH_URL

router = APIRouter()


# ---------------------------------------------------------------------------
# Business-logic helpers
# ---------------------------------------------------------------------------

def fetch_process_data(token: str, process_id: str) -> dict:
    """Fetch process JSON details for the given process ID from PROCESS_DATA_URL."""
    resp = requests.get(
        PROCESS_DATA_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept":        "application/json",
        },
        params={"processId": process_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def search_bwl(token: str, search_value: str, mandatory_fields: list) -> list:
    """Call the Blueworks Live search endpoint and return a list of process result dicts."""
    resp = requests.post(
        SEARCH_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept":        "application/json",
        },
        params={
            "searchValue":     search_value,
            "searchFieldName": "space_name",
            "returnFields":    "output",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for space in data.get("spaces", []):
        space_name = space.get("name", "-")
        for process in space.get("processes", []):
            process_id = process.get("id") or process.get("processId")
            activity_count = 0
            for milestone in process.get("milestones", []):
                for _activity in milestone.get("activities", []):
                    activity_count += 1

            # Fetch detailed process data to check for mandatory metadata
            compliant = False
            if process_id:
                try:
                    process_data = fetch_process_data(token, process_id)
                    compliant = has_mandatory_metadata(process_data, mandatory_fields)
                except Exception as ex:
                    print(f"Error fetching process data for {process_id}: {ex}")
                    compliant = has_mandatory_metadata(process, mandatory_fields)
            else:
                compliant = has_mandatory_metadata(process, mandatory_fields)

            results.append({
                "name":       process.get("name", "-"),
                "id":         process.get("id", "-"),
                "type":       "Process",
                "space":      space_name,
                "activities": activity_count,
                "compliance": "Compliant" if compliant else "Non-compliant",
            })
    return results


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str
    mandatory_fields: list[str] = []


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/metadata-fields")
def get_metadata_fields() -> list[str]:
    """Return the available metadata field names configured on the server."""
    return AVAILABLE_METADATA_FIELDS


@router.post("/search")
def post_search(body: SearchRequest) -> list:
    """Search Blueworks Live spaces and return process results with compliance status."""
    token = get_token()
    try:
        return search_bwl(token, body.query, body.mandatory_fields)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            invalidate_token()
            raise HTTPException(status_code=401, detail="Upstream authentication failed")
        raise
