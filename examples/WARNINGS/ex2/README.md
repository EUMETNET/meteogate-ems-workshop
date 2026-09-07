# WARNINGS / ex2 — Regional situational-awareness roundup

**Persona:** Somebody keeping an eye on a handful of neighbouring countries

Loops the `warnings` collection's `locations` query over a small, hardcoded
region (no `area`/bbox query exists for warnings, unlike SURFACE/CLIMATE),
resolves each active alert to its full CAP document, and adds up the
result into a quick roundup: active warnings per country, and per hazard
type.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```

The API key is read from `config.toml` at the repo root (falling back to
the `METEOGATE_API_KEY` env var) — copy `config.example.toml` to get
started. The region itself is hardcoded in `main.py` (`REGION`) rather than
configurable, since it's just a couple of country codes.
