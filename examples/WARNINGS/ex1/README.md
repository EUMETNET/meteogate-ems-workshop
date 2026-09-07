# WARNINGS / ex1 — Live warnings dashboard tile

**Persona:** A person interested in whether any warning is currently in effect for their country

Polls the `warnings` collection on MeteoGate for every warning currently
active in a single country (`locations` query, one GeoJSON feature per
warning area/info-block-language combination) and resolves each one to
its full CAP warning document.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```

The API key and country queried are read from `config.toml` at the repo
root (falling back to the `METEOGATE_API_KEY` env var and a default
country) — copy `config.example.toml` to get started.

Note: the API requires a `datetime` (sent-window) filter capped at 24
hours, so this tile only ever sees warnings *issued* in the last day — one
sent earlier that is still active would be missed. See WARNINGS/ex3 for
paging further back into the archive.
