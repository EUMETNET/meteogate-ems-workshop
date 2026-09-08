"""WARNINGS / ex3 — Real-time warning notifications via MQTT (event-driven usage).

Persona: somebody who wants to know the instant any MeteoAlarm member
country issues a new (or updated) weather warning.

MeteoGate publishes a WIS2 Notification Message over MQTT for every
new or updated warning. The notification itself only carries index
metadata (alert id, country, publish time, whether it supersedes an
earlier alert) plus a `links` array pointing to the full CAP warning
document.

One CAP warning fans out into *several* notifications: `indexInfo` is
which language block it's about (a warning is issued in more than one
language), and `indexArea`/`indexFeature` are which area/geometry polygon
within that language block — so the same warning arrives once per
language, and again once per area/geometry within each language. The full
CAP document (fetched below) already carries every language and area
regardless of which notification triggered the fetch, so only the first
notification for a given alert needs to be handled at all — the rest are
redundant.

What it does:
- Connects to the WIS2 Global Broker — globalbroker.meteo.fr:8883, plain
  MQTT over TLS (no WebSocket wrapper) with the public credentials
  everyone/everyone.
- Subscribes to a single fixed topic covering every MeteoAlarm member
  country's warnings —
  origin/a/wis2/eu-eumetnet-warnings/data/core/weather/advisories-warnings.
- Loops forever over notifications — each payload is a WIS2 Notification
  Message (a GeoJSON feature carrying alert/country/publish metadata plus
  a `links` array). malformed ones are caught and skipped.
- Dedupes per alert (process_notification) — only the first notification
  for a given alertId is processed, since the CAP document fetched for it
  already carries every language and area the warning covers.
- fetch_cap_info follows the notification's `json` link to the full CAP
  document and picks the `info` block matching LANGUAGE, falling back to
  the first available language.
- Prints "New" or "Updated" (based on whether `referencedAlertIds` is
  present) followed by severity/event/area and the onset/expires window; a
  CAP fetch failure is caught and reported per-alert instead of crashing
  the whole subscription.

Global Broker: globalbroker.meteo.fr:8883
Username: "everyone"
Password: "everyone"
Topic:    origin/a/wis2/eu-eumetnet-warnings/data/core/weather/advisories-warnings

Usage:
    uv run python main.py
"""

from __future__ import annotations

import json

import aiomqtt
import anyio
import httpx

MQTT_HOST = "globalbroker.meteo.fr"
MQTT_PORT = 8883
MQTT_USERNAME = "everyone"
MQTT_PASSWORD = "everyone"
TOPIC = "origin/a/wis2/eu-eumetnet-warnings/data/core/weather/advisories-warnings"

# Preferred language to display
LANGUAGE = "en-GB"


async def fetch_cap_info(client: httpx.AsyncClient, notification: dict) -> dict:
    """Follow the WIS2 notification's `json` link to the full CAP warning"""
    json_link = next(link["href"] for link in notification["links"] if link["rel"] == "json")
    response = await client.get(json_link, timeout=30.0)
    response.raise_for_status()
    cap = response.json()

    return next((info for info in cap["info"] if info.get("language") == LANGUAGE), cap["info"][0])


async def process_notification(client: httpx.AsyncClient, notification: dict, seen_alerts: set[str]) -> None:
    properties = notification.get("properties", {})
    alert_id = properties.get("alertId", "unknown")

    # The CAP document fetched below already carries every language and
    # area for this alert, so only the first notification for it needs to
    # be handled even though notifications for the same alert arrive with
    # different metadata.
    if alert_id in seen_alerts:
        return
    seen_alerts.add(alert_id)

    country_code = properties.get("countryCode", "??")
    kind = "Updated" if properties.get("referencedAlertIds") else "New"

    try:
        info = await fetch_cap_info(client, notification)
    except (KeyError, IndexError, httpx.HTTPError) as exc:
        print(f"[{country_code}] {kind} warning {alert_id} — CAP document unavailable ({exc})")
        return

    print()
    area_names = ", ".join(area["areaDesc"] for area in info.get("area", []))
    print(f"[{country_code}] {kind} — [{info['severity']}] {info['event']} — {area_names}")
    print(f"    valid: {info['onset']} -> {info['expires']}")


async def main() -> None:
    seen_alerts: set[str] = set()

    async with (
        httpx.AsyncClient() as http_client,
        aiomqtt.Client(
            hostname=MQTT_HOST,
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            tls_params=aiomqtt.TLSParameters(),
        ) as mqtt_client,
    ):
        await mqtt_client.subscribe(TOPIC)
        print(f"Subscribed to {TOPIC} — watching for new warnings...")

        async for message in mqtt_client.messages:
            try:
                notification = json.loads(message.payload)
                await process_notification(http_client, notification, seen_alerts)
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                print(f"Skipping malformed notification: {exc}")


if __name__ == "__main__":
    anyio.run(main)
