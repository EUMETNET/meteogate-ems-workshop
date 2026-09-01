# CLIMATE / ex1 — Climate normals lookup for a station

**Persona:** A person interested in longer daily mean temperature timeseries

Queries a provider's climate-normals collection through the CLIMATE API 
(`https://api.meteogate.eu/eu-eumetnet-climate-observations/v1`) 
for the 2020-2026 daily mean temperature at one station.


With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
