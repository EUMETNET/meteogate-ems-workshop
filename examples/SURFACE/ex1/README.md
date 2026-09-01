# SURFACE / ex1 — Live operations dashboard tile

**Persona:** A person interested in latest observations

Polls the E-SOH surface-observations collection on MeteoGate for the latest
air temperature, wind speed, rainfall rate and wind speed of gust
at a single station (`locations` query, CoverageJSON).
The kind of small, frequent request that backs for example a live status 
tile on a dashboard.

```bash
uv run python main.py
```

The API key and station queried are read from `config.toml` at the repo
root (falling back to the `METEOGATE_API_KEY` env var and a default
station) — copy `config.example.toml` to get started.
