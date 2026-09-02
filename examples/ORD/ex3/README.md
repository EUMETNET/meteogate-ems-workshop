# ORD / ex3 — Event-driven composite processing via MQTT

**Persona:** DevOps / data engineer building an event-driven pipeline.

Subscribes to the ORD API's MQTT notification topic and reacts
the moment a new DBZH (reflectivity) scan is published, instead of polling
REST on a fixed schedule — lower latency, lower load on the API.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```
