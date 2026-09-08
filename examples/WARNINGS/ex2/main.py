"""WARNINGS / ex2 — Regional situational-awareness roundup.

Persona: somebody keeping an eye on a handful of neighbouring
countries who wants an at-a-glance count of active warnings per country
and per hazard type.

The `warnings` collection only supports the `locations` data query so a
small region is built by looping over a handful of country location ids,
adding active warnings per country and per hazard type as they come in.

What it does:
- Loops the `warnings` EDR `locations` query once per country in REGION
  (fetch_country_warnings) — there's no `area`/bbox query for warnings, so
  covering a region costs one request per country instead of one.
- Dedupes each country's hub index to one entry per alertId, then follows
  each unique alert's `json` link to resolve its full CAP document
  (fetch_cap_info).
- Pulls the hazard category out of each CAP `info` block's `parameter`
  list (awareness_type_name) — the `awareness_type` entry looks like
  "5; high-temperature" — and lowercases it so the same hazard reported by
  different countries/languages groups together.
- Adding two `collections.Counter`s (by_country, by_hazard) as results
  come in and prints both sorted most-common-first, an empty region prints
  a "no warnings active" message instead of an empty report.

API: https://api.meteogate.eu/warnings

Usage:
    uv run python main.py
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

BASE_URL = "https://api.meteogate.eu/warnings"
COLLECTION = "warnings"
LANGUAGE = "en-GB"

# Some countries bordering the Gulf of Finland
REGION = {"FI": "Finland", "SE": "Sweden", "EE": "Estonia"}

CONFIG = load_config()


async def fetch_country_warnings(client: httpx.AsyncClient, country_code: str) -> list[dict]:
    """Hub index of warnings active in country_code right now, one entry per alert."""
    now = datetime.now(UTC)
    sent_window = f"{(now - timedelta(hours=24)).isoformat()}/{now.isoformat()}"
    active_window = f"{now.isoformat()}/{(now + timedelta(days=2)).isoformat()}"

    params = {"datetime": sent_window, "active": active_window, "language": LANGUAGE}
    url = f"{BASE_URL}/collections/{COLLECTION}/locations/{country_code}"

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
    return next((info for info in cap["info"] if info.get("language") == LANGUAGE), cap["info"][0])


def awareness_type_name(info: dict) -> str:
    """Extract the hazard category out of a CAP info block's `parameter` list"""
    raw = next((p["value"] for p in info.get("parameter", []) if p["valueName"] == "awareness_type"), None)
    return raw.split("; ", 1)[1].lower() if raw else "unknown"


async def main() -> None:
    headers = {"apikey": CONFIG.api_key} if CONFIG.api_key else {}
    by_country: Counter[str] = Counter()
    by_hazard: Counter[str] = Counter()

    async with httpx.AsyncClient(headers=headers) as client:
        for country_code, country_name in REGION.items():
            hub_features = await fetch_country_warnings(client, country_code)
            for feature in hub_features:
                info = await fetch_cap_info(client, feature)
                if info is None:
                    continue
                by_country[country_name] += 1
                by_hazard[awareness_type_name(info)] += 1

    total = by_country.total()
    if total == 0:
        print(f"No warnings active across {', '.join(REGION.values())} right now.")
        return

    print(f"Active warnings across {', '.join(REGION.values())}: {total}")
    print("By country:")
    for country_name, count in by_country.most_common():
        print(f"  {country_name}: {count}")

    print("By hazard type:")
    for hazard, count in by_hazard.most_common():
        print(f"  {hazard}: {count}")


if __name__ == "__main__":
    anyio.run(main)
