# EMS2026 MeteoGate Workshop

Hands-on examples for using [MeteoGate](https://meteogate.eu/), EUMETNET's
one-stop shop for open meteorological and hydrological data, across its
four main data domains:

- **SURFACE** — Near instant land-surface observations
- **ORD** — Open Radar Data (single-site volumes, OPERA composites)
- **CLIMATE** — National climate normals and long-term time series
- **WARNINGS** - Realtime and archived weather warnings issued by the MeteoAlarm member countries

Each domain has three example folders (`ex1`–`ex3`) under `examples/`,
each targeting a different persona and use case — see the `README.md` in
each folder for details.

## Setup

Requires Python 3.11+

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
```

Without uv, using plain `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

Copy `config.example.toml` to `config.toml` at the repo root and fill in
your own MeteoGate API key and preferred station:

```bash
cp config.example.toml config.toml
```

`config.toml` is git-ignored, so your personal API key never gets
committed. If it's absent, examples fall back to the `METEOGATE_API_KEY`
environment variable (or anonymous access) and a default station.

## Running an example

With uv:

```bash
cd examples/SURFACE/ex1
uv run python main.py
```

Without uv (with the `.venv` from the pip setup above activated):

```bash
cd examples/SURFACE/ex1
python main.py
```
