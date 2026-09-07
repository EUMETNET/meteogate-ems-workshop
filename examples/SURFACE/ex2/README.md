# SURFACE / ex2 — Case-study time series

**Persona:** A person wanting to make a case-study on a specific weather event who needs an hourly mean-temperature time series over a region for the last 24 hours.

Uses the EDR `area` query to pull an hourly mean air-temperature time series
for every station inside a WKT polygon over the last 24 hours, then loads
the CoverageJSON response into a pandas `DataFrame` for quick per-station
statistics. A typical first step before case-study analysis or plotting.

The polygon queried is read from `config.toml` at the repo root (defaults
to a Southern Finland / Gulf of Finland region) — copy
`config.example.toml` to get started.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
