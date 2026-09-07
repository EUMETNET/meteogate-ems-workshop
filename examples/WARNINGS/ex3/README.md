# WARNINGS / ex3 — Real-time warning notifications via MQTT

**Persona:** Somebody who wants to know the instant any warning is issued, anywhere

Subscribes to MeteoGate's Global Broker for a live feed of WIS2
Notification Messages on new and updated warnings, resolves each one to
its full CAP warning document (severity, event, headline, area, validity
window), and prints it as it arrives.

A single warning fans out into several notifications — one per language,
and one per area/geometry it covers within that language — but the CAP
document each notification links to already carries every language and
area regardless, so each alert is only reported once rather than once per
notification. `LANGUAGE` in `main.py` picks which language to display
(defaults to `"en-GB"`), falling back to the first language the warning
was actually issued in when it wasn't issued in that one.

With uv:

```bash
uv run python main.py
```

Without uv (with the `.venv` activated):

```bash
python main.py
```

Connects to `globalbroker.meteo.fr:8883` over MQTT/TLS with the public
`everyone`/`everyone` credentials — no `config.toml` or API key needed for
this one, the notification itself and the CAP document it links to are
both open.
