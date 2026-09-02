"""ORD / ex2 — Single-site volume data for a convective-storm case study.

Persona: A researcher studying a specific convective storm who needs raw, single-site 
radar radial velocity scans (VRADH) for individual elevation sweeps around a known event time, 
in order to examine storm dynamics using a tool such as wradlib or Py-ART.

API: https://api.meteogate.eu/eu-eumetnet-weather-radar
     (single-site volumes are cached for 24h, then move to the archive)

The API key is read from `config.toml` at the repo root — copy
`config.example.toml` to get started (falls back to the METEOGATE_API_KEY
env var, or anonymous access, if config.toml is absent).

Usage:
    uv run python main.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import anyio
import httpx

from ems_meteogate_workshop.config import load_config

BASE_URL = "https://api.meteogate.eu/eu-eumetnet-weather-radar"
CONFIG = load_config()

SITE_NAME = CONFIG.ord_station.name
SITE_ID = CONFIG.ord_station.site_id

# Currently the MeteoGate Radar archive is being populated so
# we use the 24h available from the api data for the test window
EVENT_START = datetime.now(tz=UTC) - timedelta(hours=24)
EVENT_END = datetime.now(tz=UTC)

OUTPUT_DIR = Path("./radar_volumes")


async def list_scans(client: httpx.AsyncClient) -> list[dict]:
    """List the scans available for SITE during the event window."""
    url = f"{BASE_URL}/collections/observations/locations/{SITE_ID}"
    params = {
        "datetime": f"{EVENT_START.isoformat()}/{EVENT_END.isoformat()}",
        "parameter-name": "VRADH:scan",
    }

    try:
        response = await client.get(url, params=params, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"ORD request failed for {url}: {exc}") from exc

    coverages = response.json().get("coverages", [])

    return coverages


async def download_scans(client: httpx.AsyncClient, item: dict) -> list[str]:
    level = item["domain"]["axes"]["z"]["values"][0]
    links = [link["href"] for link in item["links"] if link["type"] == "application/x-odim"]

    for link in links:
        destination = OUTPUT_DIR / str(level) / link.rsplit("/", 1)[-1]
        
        print(f"Downloading scan for level {level} from {link} to {destination}")

        # NOTE! Remove the # if you want to actually download the files. The code is commented out to avoid downloading 
        # large files during the workshop

        #OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        #destination.parent.mkdir(parents=True, exist_ok=True)
        
        #try:
        #    async with client.stream("GET", link, timeout=60.0) as response:
        #        response.raise_for_status()
        #        with destination.open("wb") as handle:
        #            async for chunk in response.aiter_bytes():
        #                handle.write(chunk)
        #except httpx.HTTPError as exc:
        #    raise RuntimeError(f"Failed to download volume scan from {link}: {exc}") from exc

    return links


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        coverages = await list_scans(client)
        print(f"Found {len(coverages)} elevation level scans for site '{SITE_NAME}' during the event window.")

        downloaded: list[str] = []
        async with anyio.create_task_group() as task_group:
            limiter = anyio.Semaphore(4)

            async def worker(scan: dict) -> None:
                async with limiter:
                    downloaded.extend(await download_scans(client, scan))

            for coverage in coverages:
                task_group.start_soon(worker, coverage)

    print(f"Downloaded {len(downloaded)} scans to {OUTPUT_DIR} for offline analysis.")


if __name__ == "__main__":
    anyio.run(main)
