"""
OAuth token acquisition and caching for the Blueworks Live FastAPI backend.

Ported from get_token() in bwl_search.py (line 44).  All Tkinter / UI
references have been removed.
"""

import requests

from backend.config import CLIENT_ID, CLIENT_SECRET, TOKEN_URL

# Module-level token cache.  Set to None to force a refresh on the next call.
_token: str | None = None


def get_token() -> str:
    """Return the cached bearer token, fetching a new one if needed.

    Raises:
        requests.HTTPError: if the token endpoint returns a non-2xx status.
        ValueError: if the response JSON contains neither 'access_token' nor 'token'.
    """
    global _token
    if _token is not None:
        return _token

    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=(
            "grant_type=client_credentials"
            "&client_id=" + CLIENT_ID
            + "&client_secret=" + CLIENT_SECRET
        ),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        raise ValueError("No access_token in response: " + str(data))
    _token = token
    return _token


def invalidate_token() -> None:
    """Discard the cached token so the next call to get_token() fetches a new one.

    Call this whenever an upstream request returns HTTP 401 or 403.
    """
    global _token
    _token = None
