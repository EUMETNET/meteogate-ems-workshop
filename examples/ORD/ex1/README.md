# ORD / ex1 — Flood-monitoring composite download

**Persona:** hydrologist feeding a flood-forecasting model.

Polls the Open Radar Data (ORD) API for the latest OPERA pan-European
rain-rate composite and downloads the ODIM HDF5 asset — the kind of tight
polling loop that keeps a flood model's rainfall input fresh.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```


Set `METEOGATE_API_KEY` for authenticated access — anonymous mode has lower
query limits and isn't meant for continuous polling.
