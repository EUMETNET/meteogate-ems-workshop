"""SURFACE / ex1 — Live observations.

Persona: Somebody who needs the latest observed air temperature, wind speed,
wind gust, and rainfall rate at a single station, refreshed every few minutes.

MeteoGate exposes European land-surface observations (E-SOH) through an
OGC API - EDR service. A `locations` query returns the latest (or a
time-windowed) observation at an observation station as a CoverageJSON document.

Docs:       https://eumetnet.github.io/meteogate-documentation/
API:        https://api.meteogate.eu/eu-eumetnet-surface-observations/
Collection: observations

The API key and station are read from `config.toml` at the repo root —
copy `config.example.toml` to get started.

Usage:
    uv run python main.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

BASE_URL = "https://api.meteogate.eu/eu-eumetnet-surface-observations"
COLLECTION = "observations"

CONFIG = load_config()
SITE_NAME = CONFIG.station.name
SITE_WIGOS_ID = CONFIG.station.wigos_id

STANDARD_NAMES = [
    "air_temperature",
    "wind_speed",
    "wind_speed_of_gust",
    "rainfall_rate"
]

MINUTES = 30


async def fetch_latest_observation(client: httpx.AsyncClient) -> dict:
    """Query the last {MINUTES} minutes at a single observation station (EDR `locations` query)."""
    now = datetime.now(UTC)
    window = f"{(now - timedelta(minutes=MINUTES)).isoformat(timespec='minutes')}/{now.isoformat(timespec='minutes')}"

    params = {
        "standard_name": ",".join(STANDARD_NAMES),
        "datetime": window,
    }
    url = f"{BASE_URL}/collections/{COLLECTION}/locations/{SITE_WIGOS_ID}"

    try:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"MeteoGate request failed for {url}: {exc}") from exc

    return response.json()


def latest_values(coverage: dict) -> dict[str, float | None]:
    """Pick the most recent value for each parameter out of a CoverageJSON doc."""
    if coverage.get("type") == "CoverageCollection":
        data = coverage.get("coverages", [])
    else:
        data = [coverage]
    values: dict[str, float | None] = {}
    for coverage_item in data:
        ranges = coverage_item.get("ranges", {})
        for name, coverage_range in ranges.items():
            series = coverage_range.get("values", [])
            # Last non-null value in the requested time window.
            values[name] = next((v for v in reversed(series) if v is not None), None)
    return values


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        coverage = await fetch_latest_observation(client)

    values = latest_values(coverage)
    print(f"Latest observations at {SITE_NAME}:")
    for parameter, value in values.items():
        print(f"  {parameter}: {value if value is not None else 'no data'}")


if __name__ == "__main__":
    anyio.run(main)
