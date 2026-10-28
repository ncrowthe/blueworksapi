"""
Configuration loading for the Blueworks Live FastAPI backend.

Reads CLIENT_ID, CLIENT_SECRET, and MANDATORY_METADATA from environment
variables.  A local `.env` file is supported for development via python-dotenv.
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()

# -- Credentials ---------------------------------------------------------------
CLIENT_ID: str = os.environ.get("CLIENT_ID", "")
CLIENT_SECRET: str = os.environ.get("CLIENT_SECRET", "")

# -- Available metadata fields -------------------------------------------------
# These are the fields offered in the GUI dropdown for the user to choose from.
# Accepts a JSON list (e.g. '["businessOwners","Inputs"]') or a
# comma-separated string — mirrors config-loading logic in bwl_search.py
# lines 24-34.
_raw_mandatory: str = os.environ.get("MANDATORY_METADATA", "")
try:
    AVAILABLE_METADATA_FIELDS: list[str] = json.loads(_raw_mandatory)
    if not isinstance(AVAILABLE_METADATA_FIELDS, list):
        AVAILABLE_METADATA_FIELDS = [AVAILABLE_METADATA_FIELDS]
except Exception:
    AVAILABLE_METADATA_FIELDS = [
        item.strip().strip("\"'")
        for item in _raw_mandatory.strip("[]").split(",")
        if item.strip()
    ]

# -- API endpoint URLs ---------------------------------------------------------
TOKEN_URL: str = "https://ibm.blueworkslive.com/oauth/token"
SEARCH_URL: str = "https://ibm.blueworkslive.com/scr/api/Search?version=20191214"
PROCESS_DATA_URL: str = (
    "https://ibm.blueworkslive.com/scr/api/ProcessData?version=20191214"
)
DIAGRAM_URL: str = "https://ibm.blueworkslive.com/scr/api/PrintDiagram"
GLOSSARY_URL: str = "https://ibm.blueworkslive.com/bwl/glossary-values"
