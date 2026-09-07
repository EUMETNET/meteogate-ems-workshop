"""WARNINGS / ex1 — Live warnings dashboard tile for one country.

Persona: somebody who wants to know, right now, whether any weather warning
is in effect for their country. This is the warnings counterpart of the
SURFACE/ex1 live observations tile.

MeteoGate exposes weather warnings issued by the MeteoAlarm member countries
through an OGC API - EDR service. The `warnings` collection only supports
the `locations` data query: `locations/{country_code}` returns one GeoJSON
feature per combination, each linking out to the full CAP warning document.

API:        https://api.meteogate.eu/warnings
Collection: warnings

The API key and country are read from `config.toml` at the repo root —
copy `config.example.toml` to get started.

Usage:
    uv run python main.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

BASE_URL = "https://api.meteogate.eu/warnings"
COLLECTION = "warnings"

CONFIG = load_config()
COUNTRY_NAME = CONFIG.warnings_country.name
COUNTRY_CODE = CONFIG.warnings_country.country_code

LANGUAGE = "en-GB"


async def fetch_current_warnings(client: httpx.AsyncClient) -> list[dict]:
    """Hub index of warnings for COUNTRY_CODE, deduplicated to one entry per alert."""
    now = datetime.now(UTC)
    sent_window = f"{(now - timedelta(hours=24)).isoformat()}/{now.isoformat()}"
    active_window = f"{now.isoformat()}/{(now + timedelta(days=2)).isoformat()}"

    params = {
        "datetime": sent_window,
        "active": active_window,
        "language": LANGUAGE,
    }
    url = f"{BASE_URL}/collections/{COLLECTION}/locations/{COUNTRY_CODE}"

    try:
        response = await client.get(url, params=params, timeout=30.0)
        if response.status_code == 204:
            return []
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"MeteoGate request failed for {url}: {exc}") from exc

    features = response.json().get("features", [])
    # One feature per warning area/info-block combination — keep one per alert.
    seen_alerts: dict[str, dict] = {}
    for feature in features:
        seen_alerts.setdefault(feature["properties"]["alertId"], feature)
    return list(seen_alerts.values())


async def fetch_cap_info(client: httpx.AsyncClient, hub_feature: dict) -> dict | None:
    """Follow the hub feature's `json` link to the full CAP warning and pick our language."""
    json_link = next((link["href"] for link in hub_feature["links"] if link["rel"] == "json"), None)
    if json_link is None:
        return None

    response = await client.get(json_link, timeout=30.0)
    response.raise_for_status()
    cap = response.json()

    # The CAP doc carries one `info` block per language
    return next((info for info in cap["info"] if info.get("language") == LANGUAGE), cap["info"][0])


async def main() -> None:
    headers = {"apikey": f"{CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        hub_features = await fetch_current_warnings(client)
        infos = [await fetch_cap_info(client, feature) for feature in hub_features]

    print(f"Active warnings for {COUNTRY_NAME}: {len(infos)}")
    for info in infos:
        if info is None:
            continue
        area_names = ", ".join(area["areaDesc"] for area in info.get("area", []))
        print()
        print(f"  [{info['severity']}] {info['event']} — {area_names}")
        print(f"  [Description] {info['description']}")
        print(f"  [Valid: {info['onset']} -> {info['expires']}]")


if __name__ == "__main__":
    anyio.run(main)
