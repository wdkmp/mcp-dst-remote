"""
MCP Server for Danmarks Statistik's Statistikbank API.
Remote deployment version (Streamable HTTP + SSE transport).

This server exposes Danmarks Statistik's API endpoints as MCP tools,
designed to be deployed as a remote service for Claude.ai web integration.

Run locally:  python server.py
Run via Docker: see Dockerfile / docker-compose.yml
"""

import os
import logging
import sys
from typing import Any, Literal, Optional, Union, Dict

from fastmcp import FastMCP
import requests

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration via environment variables
# ---------------------------------------------------------------------------
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))  # $PORT is auto-set by Railway/Render/Fly.io
TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")  # "streamable-http" or "sse"

# ---------------------------------------------------------------------------
# Initialize FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("Danmarks Statistik API")

# Base URL for DST API
BASE_URL = "https://api.statbank.dk/v1"

# Valid data formats
DataFormat = Literal[
    "JSONSTAT", "JSON", "CSV", "XLSX", "BULK", "PX", "TSV", "HTML5", "HTML5InclNotes"
]


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------
@mcp.tool()
def get_subjects(
    subjects: list[str] = None,
    includeTables: bool = False,
    recursive: bool = False,
    omitInactiveSubjects: bool = False,
    lang: str = "da",
) -> dict:
    """Get subjects from Danmarks Statistik API.

    Args:
        subjects: Optional list of subject codes. If provided, fetches sub-subjects for these subjects.
        includeTables: If True, includes tables in the result under each subject.
        recursive: If True, fetches sub-subjects (and tables) recursively through all levels.
        omitInactiveSubjects: If True, omits subjects/sub-subjects that are no longer updated.
        lang: Language code ("da" or "en", default "da").
    """
    payload: dict = {"format": "JSON", "lang": lang}
    if subjects:
        payload["subjects"] = subjects
    if includeTables:
        payload["includeTables"] = True
    if recursive:
        payload["recursive"] = True
    if omitInactiveSubjects:
        payload["omitInactiveSubjects"] = True

    r = requests.post(f"{BASE_URL}/subjects", json=payload)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def get_tables(
    subjects: list[str] = None,
    pastdays: int = None,
    includeInactive: bool = False,
    lang: str = "da",
) -> dict:
    """Get tables from Danmarks Statistik API.

    Args:
        subjects: Optional list of subject codes to filter tables on.
        pastdays: Optional number of days; only tables updated within these days are included.
        includeInactive: If True, includes inactive (discontinued) tables.
        lang: Language code ("da" or "en", default "da").
    """
    payload: dict = {"format": "JSON", "lang": lang}
    if subjects:
        payload["subjects"] = subjects
    if pastdays is not None:
        payload["pastdays"] = pastdays
    if includeInactive:
        payload["includeInactive"] = True

    r = requests.post(f"{BASE_URL}/tables", json=payload)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def get_table_info(table_id: str, lang: str = "da") -> dict:
    """Get table metadata from Danmarks Statistik API.

    Args:
        table_id: The table code (e.g., "folk1c").
        lang: Language code ("da" or "en", default "da").
    """
    payload = {"table": table_id, "format": "JSON", "lang": lang}
    r = requests.post(f"{BASE_URL}/tableinfo", json=payload)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def get_data(
    table_id: str,
    variables: list[dict] = None,
    format: DataFormat = "JSON",
    timeOrder: Optional[Literal["Ascending", "Descending"]] = None,
    lang: str = "da",
    valuePresentation: Optional[Literal["Code", "Text"]] = None,
) -> Union[dict, str]:
    """Get data from Danmarks Statistik API.

    Args:
        table_id: The table code (e.g., "folk1c").
        variables: Optional list of dicts to filter data.
                   Each dict must have "code" (variable code) and "values" (list of desired value codes).
        format: Output format (default "JSON"). Valid: JSONSTAT, JSON, CSV, XLSX, BULK, PX, TSV, HTML5, HTML5InclNotes.
        timeOrder: Optional sort order for time series ("Ascending" or "Descending").
        lang: Language code ("da" or "en", default "da").
        valuePresentation: Optional value presentation ("Code" or "Text").
    """
    fmt = format.upper()
    payload: dict = {"table": table_id, "format": fmt, "lang": lang}

    if variables:
        for var in variables:
            if not isinstance(var, dict) or "code" not in var or "values" not in var:
                raise ValueError("Each variable must be a dict with 'code' and 'values' keys")
            if not isinstance(var["values"], list):
                var["values"] = [var["values"]]
        payload["variables"] = variables

    if timeOrder:
        payload["timeOrder"] = timeOrder
    if valuePresentation:
        payload["valuePresentation"] = valuePresentation

    r = requests.post(f"{BASE_URL}/data", json=payload)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if r.status_code == 400:
            error_detail = r.json() if r.text else "No error details"
            raise ValueError(f"Bad request to DST API: {error_detail}")
        raise

    if fmt in ("JSON", "JSONSTAT"):
        return r.json()
    return r.text


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info(
        "Starting Danmarks Statistik MCP Server — transport=%s, host=%s, port=%s",
        TRANSPORT, HOST, PORT,
    )
    mcp.run(transport=TRANSPORT, host=HOST, port=PORT)
