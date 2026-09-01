"""CLIMATE / ex1 — Climate normals lookup for a station.

Persona: a person interested in daily mean temperature for a specific station 
over a longer period (2020-2026).

Climate datasets are published as MeteoGate collections by each National
Meteorological and Hydrological Service (NMHS) and reached through the
MeteoGate Climate API, which works as an aggregator to the provider's own OGC API - EDR

Docs:       https://api.meteogate.eu/eu-eumetnet-climate-observations/v1/docs/
API:        https://api.meteogate.eu/eu-eumetnet-climate-observations/v1
Collection: eu-daily

The API key and station are read from `config.toml` at the repo root —
copy `config.example.toml` to get started (falls back to the
METEOGATE_API_KEY env var and a default station if config.toml is absent).

Usage:
    uv run python main.py
"""

from __future__ import annotations

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

URL_BASE = "https://api.meteogate.eu/eu-eumetnet-climate-observations/v1"
COLLECTION = "eu-daily"
STANDARD_NAME = "air_temperature"
METHOD = "mean"
DURATION = "-P1D,P1D"
DATETIME = "2020-01-01T00:00:00Z/2026-12-31T00:00:00Z"


CONFIG = load_config()
STATION_NAME = CONFIG.climate_station.name
STATION_ID = CONFIG.climate_station.wigos_id


async def fetch_normals(client: httpx.AsyncClient) -> dict:
    params = {
        "standard_name": STANDARD_NAME,
        "method": METHOD,
        "duration": DURATION,
        "datetime": DATETIME,
    }
    url = f"{URL_BASE}/collections/{COLLECTION}/locations/{STATION_ID}"

    try:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"MeteoGate request failed for {url}: {exc}") from exc

    return response.json()


def daily_normals(coverage: dict) -> list[tuple[str, float]]:
    if coverage.get("type") == "CoverageCollection":
        coverages = coverage.get("coverages", [])
    else:
        coverages = [coverage]

    data = coverages[0]
    days = data["domain"]["axes"]["t"]["values"]
    parameter_name = next((k for k in data["ranges"] if "air_temperature" in k), None)
    values = data["ranges"][parameter_name]["values"]
    return list(zip(days, values, strict=True))


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        coverage = await fetch_normals(client)

    print(f"2020-2026 daily mean temperature values — {STATION_NAME}:")
    for day, value in daily_normals(coverage):
        print(f"  {day}: {value:.1f} degC" if value is not None else f"  {day}: no data")


if __name__ == "__main__":
    anyio.run(main)
