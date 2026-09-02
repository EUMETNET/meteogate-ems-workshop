"""ORD / ex1 — Flood-monitoring composite download.

Persona: a hydrologist feeding a flood-forecasting model that needs the
latest pan-European OPERA rain-rate composite as ODIM HDF5,
on a tight polling loop.

Docs: https://eumetnet.github.io/openradardata-documentation/
API:  https://api.meteogate.eu/eu-eumetnet-weather-radar


The API key is read from `config.toml` at the repo root — copy
`config.example.toml` to get started (falls back to the METEOGATE_API_KEY
env var, or anonymous access, if config.toml is absent).

Usage:
    uv run python main.py
"""

from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime, timedelta

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

BASE_URL = "https://api.meteogate.eu/eu-eumetnet-weather-radar"

LOCATION = "0-20010-0-OPERA"
OUTPUT_DIR = Path("./radar_composites")
MINUTES = 60
RATE_COMP = "RATE:comp"
CONFIG = load_config()

async def fetch_latest_composite_metadata(client: httpx.AsyncClient) -> dict:
    """List the most recent RATE composite for OPERA."""
    url = f"{BASE_URL}/collections/observations/locations/{LOCATION}"
    now = datetime.now(UTC)
    window = f"{(now - timedelta(minutes=MINUTES)).isoformat(timespec='minutes')}/{now.isoformat(timespec='minutes')}"
    
    params = {
        "datetime": window,
    }

    try:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"ORD request failed for {url}: {exc}") from exc

    coverages = response.json().get("coverages", [])
    matching_items = [coverage for coverage in coverages if RATE_COMP in coverage.get("parameters", {})]
    if not matching_items:
        raise RuntimeError(f"No '{LOCATION}' {RATE_COMP} composite available yet")
    return matching_items[0]


async def download_file(client: httpx.AsyncClient, item: dict) -> Path:
    """Download the composite's ODIM HDF5 asset."""
    hdf5_url = item["links"][-1]["href"]
    print(f"Downloading composite from {hdf5_url}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT_DIR / hdf5_url.rsplit("/", 1)[-1]

    try:
        async with client.stream("GET", hdf5_url, timeout=60.0) as response:
            response.raise_for_status()
            with destination.open("wb") as handle:
                async for chunk in response.aiter_bytes():
                    handle.write(chunk)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to download composite from {hdf5_url}: {exc}") from exc

    return destination


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        item = await fetch_latest_composite_metadata(client)
        print(f"Latest 'OPERA' composite: {item['domain']['axes']['t']['values'][-1]} — downloading")

        path = await download_file(client, item)
        print(f"Saved to {path} — ready to feed into the model.")


if __name__ == "__main__":
    anyio.run(main)
