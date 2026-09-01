# SURFACE / ex3 — Threshold alerting via MQTT

**Persona:** a person who requires notifications on weather phenomenom.

Subscribes to E-SOH's MQTT notification topic instead of polling a
REST endpoint, and raises an alert the instant a station inside the region
of interest reports a wind gust or rain rate above a configured threshold —
the event-driven counterpart to for example ex1.

Connects to `observations.meteogate.eu:443` (MQTT over WebSocket/TLS,
public `everyone`/`everyone` credentials) and subscribes to a
`country/organization/station/observation` topic — edit `TOPIC` in
`main.py` to point at a different country, NMHS, or WIGOS station id.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
