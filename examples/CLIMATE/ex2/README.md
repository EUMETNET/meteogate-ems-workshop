# CLIMATE / ex2 — Long-term precipitation trend analysis

**Persona:** A researcher who needs a multi-decade annual precipitation-total time series for a station, to compute a rolling mean and a simple linear trend

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
