# ORD / ex3 — Event-driven composite processing via MQTT

**Persona:** A person building an event-driven pipeline who wants to react the moment a new scan is published, instead of polling the REST API on a fixed schedule.

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
