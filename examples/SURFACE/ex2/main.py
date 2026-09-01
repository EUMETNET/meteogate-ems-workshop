"""SURFACE / ex2 — Case-study time series.

Persona: a person wanting to make a case-study on a specific weather event 
who needs an hourly mean-temperature time series over a region for the 
last 24 hours, loaded into pandas for quick statistics and plotting.

MeteoGate's EDR `area` query returns every station inside a bounding box as
a CoverageJSON "coverage collection", one time series per site.

API: https://api.meteogate.eu/eu-eumetnet-surface-observations

Usage:
    uv run python main.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import anyio
import httpx
import pandas as pd

from ems_meteogate_workshop.config import load_config

BASE_URL = "https://api.meteogate.eu/eu-eumetnet-surface-observations"
COLLECTION = "observations"
CONFIG = load_config()

COORDS = CONFIG.surface_polygon
STANDARD_NAME = "air_temperature"
METHOD = "mean"
DURATION = "PT1H"



async def fetch_area_timeseries(client: httpx.AsyncClient) -> dict:
    """Query hourly mean air temperature for every station in BBOX, last 24h."""
    now = datetime.now(UTC)
    window = f"{(now - timedelta(hours=24)).isoformat()}/{now.isoformat()}"

    params = {
        "coords": COORDS,
        "standard_name": STANDARD_NAME,
        "method": METHOD,
        "duration": DURATION,
        "datetime": window,
    }
    url = f"{BASE_URL}/collections/{COLLECTION}/area"

    try:
        response = await client.get(url, params=params, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"MeteoGate request failed for {url}: {exc}") from exc

    return response.json()


def to_dataframe(coverage_collection: dict) -> pd.DataFrame:
    """Flatten a CoverageJSON CoverageCollection into a tidy pandas DataFrame."""
    rows = []
    for coverage in coverage_collection.get("coverages", []):
        station_id = coverage.get("metocean:wigosId") or coverage["domain"]["domainType"]
        times = coverage["domain"]["axes"]["t"]["values"]
        parameter_name = list(coverage["ranges"].keys())[0]
        values = coverage["ranges"][parameter_name]["values"]
        for timestamp, value in zip(times, values, strict=True):
            rows.append({"station_id": station_id, "time": timestamp, "air_temperature_c": value})

    frame = pd.DataFrame(rows)
    frame["time"] = pd.to_datetime(frame["time"])
    return frame


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        coverage_collection = await fetch_area_timeseries(client)

    frame = to_dataframe(coverage_collection)
    if frame.empty:
        print("No observations returned for the requested area/window.")
        return

    print(f"Stations: {frame['station_id'].nunique()}, samples: {len(frame)}")
    summary = frame.groupby("station_id")["air_temperature_c"].agg(["mean", "max", "min"]).round(1)
    print(summary.sort_values("max", ascending=False).head(10))


if __name__ == "__main__":
    anyio.run(main)
