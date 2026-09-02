"""Shared workshop configuration.

Reads personal settings (MeteoGate API key, preferred stations) from a
`config.toml` file at the repository root — copy `config.example.toml` to
`config.toml` and fill in your own values to get started.

SURFACE, CLIMATE and ORD examples query different kinds of collections and
contain different datasets, so the config file has separate sections for
`surface_station`, `climate_station`, `ord_station`.

`config.toml` is git-ignored (it may hold a personal API key), so every
example falls back to the `METEOGATE_API_KEY` environment variable and
sensible default stations when it's absent, and keeps working out of the box.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _REPO_ROOT / "config.toml"

DEFAULT_SURFACE_STATION_NAME = "Helsinki Kumpula"
DEFAULT_SURFACE_STATION_WIGOS_ID = "0-246-0-101004"

DEFAULT_CLIMATE_STATION_NAME = "De Bilt"
DEFAULT_CLIMATE_STATION_WIGOS_ID = "0-20000-0-06260"

DEFAULT_SURFACE_WKT = "POLYGON((21.0 59.5, 28.0 59.5, 28.0 61.5, 21.0 61.5, 21.0 59.5))"
DEFAULT_CLIMATE_WKT = "POLYGON((4.0 51.5, 7.0 51.5, 7.0 53.5, 4.0 53.5, 4.0 51.5))"

DEFAULT_ORD_SITE_NAME = "Kaunispää"
DEFAULT_ORD_SITE_ID = "0-246-0-fikau"


@dataclass(frozen=True)
class SurfaceStationPreference:
    """A preferred E-SOH surface station, identified by WIGOS id."""

    name: str
    wigos_id: str


@dataclass(frozen=True)
class ClimateStationPreference:
    """A preferred climate-normals/timeseries station, identified by WIGOS id."""

    name: str
    wigos_id: str


@dataclass(frozen=True)
class ORDStationPreference:
    """A preferred ORD site, identified by site ID."""

    name: str
    site_id: str


@dataclass(frozen=True)
class WorkshopConfig:
    api_key: str | None
    surface_station: SurfaceStationPreference
    climate_station: ClimateStationPreference
    ord_station: ORDStationPreference
    surface_polygon: str
    climate_polygon: str


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

    surface_raw = station_raw.get("surface", {})
    surface_station = SurfaceStationPreference(
        name=surface_raw.get("name") or DEFAULT_SURFACE_STATION_NAME,
        wigos_id=surface_raw.get("wigos_id") or DEFAULT_SURFACE_STATION_WIGOS_ID,
    )

    climate_raw = station_raw.get("climate", {})
    climate_station = ClimateStationPreference(
        name=climate_raw.get("name") or DEFAULT_CLIMATE_STATION_NAME,
        wigos_id=climate_raw.get("wigos_id") or DEFAULT_CLIMATE_STATION_WIGOS_ID
    )

    ord_raw = station_raw.get("ord", {})
    ord_station = ORDStationPreference(
        name=ord_raw.get("name") or DEFAULT_ORD_SITE_NAME,
        site_id=ord_raw.get("site_id") or DEFAULT_ORD_SITE_ID,
    )

    surface_polygon = raw.get("polygon", {}).get("surface_wkt") or DEFAULT_SURFACE_WKT
    climate_polygon = raw.get("polygon", {}).get("climate_wkt") or DEFAULT_CLIMATE_WKT

    return WorkshopConfig(
        api_key=api_key,
        surface_station=surface_station,
        climate_station=climate_station,
        surface_polygon=surface_polygon,
        climate_polygon=climate_polygon,
        ord_station=ord_station,
    )
