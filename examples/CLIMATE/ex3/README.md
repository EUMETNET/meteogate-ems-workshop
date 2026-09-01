# CLIMATE / ex3 — Bulk regional export for a feature store

**Persona:** data engineer preparing ML training data.

Uses the EDR `area` query to fetch multiple climate parameters for every
station inside a region in a single request, then a second `locations`
query (polygon-scoped, metadata only) to attach human-readable station
names — and writes it all out as one tidy CSV, replacing what would
otherwise be many manual portal downloads.

The region queried is read from `config.toml` at the repo root (defaults
to a small area around De Bilt, NL) — copy `config.example.toml` to get
started.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
