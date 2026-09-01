"""Shared workshop configuration.

Reads personal settings (MeteoGate API key, preferred station) from a
`config.toml` file at the repository root — copy `config.example.toml` to
`config.toml` and fill in your own values to get started.

`config.toml` is git-ignored (it may hold a personal API key), so every
example falls back to the `METEOGATE_API_KEY` environment variable and a
sensible default station when it's absent, and keeps working out of the box.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _REPO_ROOT / "config.toml"

DEFAULT_STATION_NAME = "Helsinki Kumpula"
DEFAULT_STATION_WIGOS_ID = "0-246-0-101004"
DEFAULT_STATION_LON = 24.9613
DEFAULT_STATION_LAT = 60.2031
DEFAULT_WKT = "POLYGON((21.0 59.5, 28.0 59.5, 28.0 61.5, 21.0 61.5, 21.0 59.5))"


@dataclass(frozen=True)
class StationPreference:
    """A single named point, e.g. a preferred observation or climate station."""

    name: str
    wigos_id: str
    lon: float
    lat: float


@dataclass(frozen=True)
class WorkshopConfig:
    api_key: str | None
    station: StationPreference
    polygon: str


def _read_config_file() -> dict:
    if not _CONFIG_PATH.exists():
        return {}
    with _CONFIG_PATH.open("rb") as handle:
        return tomllib.load(handle)


def load_config() -> WorkshopConfig:
    """Load `config.toml`, falling back to env vars and defaults."""
    raw = _read_config_file()

    api_key = raw.get("meteogate", {}).get("api_key") or None
    if not api_key:
        api_key = os.environ.get("METEOGATE_API_KEY")

    station_raw = raw.get("station", {})
    station = StationPreference(
        name=station_raw.get("name") or DEFAULT_STATION_NAME,
        wigos_id=station_raw.get("wigos_id") or DEFAULT_STATION_WIGOS_ID,
        lon=station_raw.get("lon", DEFAULT_STATION_LON),
        lat=station_raw.get("lat", DEFAULT_STATION_LAT),
    )

    polygon = raw.get("polygon", {}).get("wkt") or DEFAULT_WKT

    return WorkshopConfig(api_key=api_key, station=station, polygon=polygon)
