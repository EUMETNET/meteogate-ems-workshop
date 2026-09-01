# CLIMATE / ex2 — Long-term precipitation trend analysis

**Persona:** climate-change researcher.

Pulls a multi-decade annual precipitation-total time series for one station
through the Climate API, then computes a 10-year rolling mean and a
simple linear trend (mm/decade) with pandas and numpy.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
