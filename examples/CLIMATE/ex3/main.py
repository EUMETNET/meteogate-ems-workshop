"""CLIMATE / ex3 — Bulk regional export for a feature store.

Persona: a data engineer preparing training data for a downstream ML model
who needs several decades of multiple climate parameters for every station
in an area, exported as a single CSV.

Uses the EDR `area` query to fetch all three parameters for every station
inside a polygon in one request (CoverageJSON "coverage collection", one
coverage per station) — far cheaper than a naive one-request-per-station
loop. The `area` response identifies each station only by WIGOS id and
coordinates, so a single follow-up `locations` query (also polygon-scoped)
is used to look up human-readable station names.

Usage:
    uv run python main.py
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

URL_BASE = "https://api.meteogate.eu/eu-eumetnet-climate-observations/v1"
COLLECTION = "eu-daily"
STANDARD_NAMES = ["precipitation_amount", "air_temperature", "duration_of_sunshine"]
METHODS = ["sum", "mean"]
DURATION = "-P1D,P1D"
DATETIME = "1950-01-01T00:00:00Z/2026-12-31T00:00:00Z"
OUTPUT_CSV = Path("./climate_export.csv")

CONFIG = load_config()
COORDS = CONFIG.climate_polygon


def polygon_bbox(wkt: str) -> str:
    """Extract "lon_min,lat_min,lon_max,lat_max" out of a WKT POLYGON string."""
    numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", wkt)]
    lons = numbers[0::2]
    lats = numbers[1::2]
    return f"{min(lons)},{min(lats)},{max(lons)},{max(lats)}"


async def fetch_area_normals(client: httpx.AsyncClient) -> list[dict]:
    """Fetch every parameter for every station inside COORDS in one request (EDR `area` query)."""
    params = {
        "coords": COORDS,
        "standard_name": ",".join(STANDARD_NAMES),
        "method": ",".join(METHODS),
        "duration": DURATION,
        "datetime": DATETIME,
        "f": "CoverageJSON",
    }
    url = f"{URL_BASE}/collections/{COLLECTION}/area"

    try:
        response = await client.get(url, params=params, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"MeteoGate request failed for {url}: {exc}") from exc

    return response.json().get("coverages", [])


async def fetch_station_names(client: httpx.AsyncClient) -> dict[str, str]:
    """Look up station_id -> name for every station inside COORDS (EDR `locations` query).

    The `area` response only carries a WIGOS id and coordinates per station, so
    this second, much cheaper request (metadata only, no observations) is used
    to enrich the export with human-readable names.
    """
    params = {"bbox": polygon_bbox(COORDS)}
    url = f"{URL_BASE}/collections/{COLLECTION}/locations"

    try:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"MeteoGate request failed for {url}: {exc}") from exc

    features = response.json().get("features", [])
    return {feature["id"]: feature["properties"].get("name", "unknown") for feature in features}


def coverage_to_rows(coverage: dict, station_names: dict[str, str]) -> list[dict]:
    station_id = coverage.get("eumetnet:locationId", "unknown")
    station_name = station_names.get(station_id, "unknown")
    times = coverage["domain"]["axes"]["t"]["values"]
    ranges = coverage.get("ranges", {})

    # One composite range key per standard_name, e.g. "air_temperature:1.5:mean:-P1D".
    range_keys = {
        standard_name: next((key for key in ranges if key.startswith(standard_name)), None)
        for standard_name in STANDARD_NAMES
    }

    rows = []
    for index, timestamp in enumerate(times):
        row = {"station_id": station_id, "station_name": station_name, "time": timestamp}
        for standard_name, range_key in range_keys.items():
            values = ranges.get(range_key, {}).get("values", []) if range_key else []
            row[standard_name] = values[index] if index < len(values) else None
        rows.append(row)
    return rows


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}

    async with httpx.AsyncClient(headers=headers) as client:
        coverages = await fetch_area_normals(client)
        print(f"Exporting {len(STANDARD_NAMES)} parameters for {len(coverages)} stations...")
        station_names = await fetch_station_names(client)

    all_rows = [row for coverage in coverages for row in coverage_to_rows(coverage, station_names)]

    if not all_rows:
        print("No data collected — nothing written.")
        return

    fieldnames = ["station_id", "station_name", "time", *STANDARD_NAMES]
    with OUTPUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    anyio.run(main)
