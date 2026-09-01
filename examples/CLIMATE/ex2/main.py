"""CLIMATE / ex2 — Long-term precipitation trend analysis.

Persona: a researcher who needs a multi-decade annual
precipitation-total time series for a region, to compute a rolling mean and
a simple linear trend.


The API key and station are read from `config.toml` at the repo root —
copy `config.example.toml` to get started (falls back to the
METEOGATE_API_KEY env var and a default station if config.toml is absent).

Usage:
    uv run python main.py
"""

from __future__ import annotations

import anyio
import httpx
import numpy as np
import pandas as pd

from ems_meteogate_workshop.config import load_config

URL_BASE = "https://api.meteogate.eu/eu-eumetnet-climate-observations/v1"
COLLECTION = "eu-daily"
STANDARD_NAME = "precipitation_amount"
METHOD = "sum"
DURATION = "-P1D,P1D"
DATETIME = "1900-01-01T00:00:00Z/2026-12-31T00:00:00Z"

CONFIG = load_config()
STATION_NAME = CONFIG.climate_station.name
STATION_ID = CONFIG.climate_station.wigos_id



async def fetch_annual_precipitation(client: httpx.AsyncClient) -> dict:
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


def to_series(coverage: dict) -> pd.Series:
    """Daily precipitation totals — one row per day."""
    if coverage.get("type") == "CoverageCollection":
        coverages = coverage.get("coverages", [])
    else:
        coverages = [coverage]

    data = coverages[0]
    parameter_name = next((k for k in data["ranges"] if "precipitation_amount" in k), None)
    values = data["ranges"][parameter_name]["values"]
    days = pd.to_datetime(data["domain"]["axes"]["t"]["values"])
    return pd.Series(values, index=days, name="precipitation_mm").dropna()


def to_annual_totals(daily: pd.Series) -> pd.Series:
    """Collapse a daily series into one summed total per calendar year."""
    return daily.resample("YE").sum()


def to_decade_means(annual: pd.Series) -> pd.Series:
    """Mean annual precipitation per calendar decade (e.g. 1953 -> the 1950s)."""
    decade_start = (annual.index.year // 10) * 10
    return annual.groupby(decade_start).mean()


def linear_trend_mm_per_decade(series: pd.Series) -> float:
    years_since_start = (series.index.year - series.index.year.min()).to_numpy()
    slope, _intercept = np.polyfit(years_since_start, series.to_numpy(), deg=1)
    return slope * 10


async def main() -> None:
    headers = {"Authorization": f"Bearer {CONFIG.api_key}"} if CONFIG.api_key else {}
    async with httpx.AsyncClient(headers=headers) as client:
        coverage = await fetch_annual_precipitation(client)

    daily = to_series(coverage)
    if daily.empty:
        print("No precipitation data returned for the requested period.")
        return

    annual = to_annual_totals(daily)
    rolling_mean = annual.rolling(window=10, min_periods=5).mean()
    trend = linear_trend_mm_per_decade(annual)
    decade_means = to_decade_means(annual)

    print(f"Annual precipitation totals for {CONFIG.climate_station.name}: {len(annual)} years")
    print(f"10-year rolling mean (last value): {rolling_mean.iloc[-1]:.1f} mm")
    print(f"Linear trend: {trend:+.1f} mm / decade")

    print("Decade means (mm/year):")
    for decade_start, mean_mm in decade_means.items():
        print(f"  {decade_start}s: {mean_mm:.1f} mm")


if __name__ == "__main__":
    anyio.run(main)
