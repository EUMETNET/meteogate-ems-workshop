"""ORD / ex3 — Event-driven composite processing via MQTT.

Persona: a person building an event-driven pipeline who
wants to react the moment a new scan is published, instead of
polling the REST API on a fixed schedule.

The ORD API publishes a MQTT notification for every new scan.
This example subscribes to the topic corresponding to the DBZH 
quantity and triggers a processing callback for each notification.

Docs: https://eumetnet.github.io/openradardata-documentation/
MQTT broker: radar.meteogate.eu:8884 (WebSocket over TLS), username "everyone"

TOPIC hierarchy: ORD/naming_authority/id/quantity

Usage:
    uv run python main.py
"""

from __future__ import annotations

import json

import aiomqtt
import anyio
import httpx

MQTT_HOST = "radar.meteogate.eu"
MQTT_PORT = 8884
MQTT_USERNAME = "everyone"
MQTT_PASSWORD = "everyone"

# All sites with DBZH quantity from Finland
# Change naming authority to wanted location 
# e.g se.smhi, de.dwd, nl.knmi, is.vedur etc. 
# to get the DBZH scans from that country. 
# To get all sites with DBZH scans from all countries, 
# use the + wildcard for naming authority and site id, 
# e.g. ORD/+/+/DBZH
TOPIC = "ORD/fi.fmi/+/DBZH"


async def process_notification(client: httpx.AsyncClient, payload: dict) -> None:
    """Download and hand off the scan announced by a notification."""
    data = next((k for k in payload["links"] if "download" in k["title"].lower()), None)
    href = data["href"] if data else None
    properties = payload["properties"]
    print()
    print(f"--- New {properties['format']} available from {properties['platform_name']} ({properties['platform']}) ---")

    try:
        response = await client.get(href, timeout=60.0)
        print(f"Downloaded {len(response.content)} bytes from {href}")
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"  failed to fetch {href}: {exc}")
        return

    # Hand off to downstream processing — nowcasting job, cache, etc.
    print("--- dispatching to processing queue ---")
    print()


async def main() -> None:
    async with httpx.AsyncClient() as http_client:
        async with aiomqtt.Client(
            hostname=MQTT_HOST,
            port=MQTT_PORT,
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            transport="websockets",
            tls_params=aiomqtt.TLSParameters(),
            websocket_path="/ordmqtt/",
            websocket_headers={"Host": MQTT_HOST},
        ) as mqtt_client:
            await mqtt_client.subscribe(TOPIC)
            print(f"Subscribed to {TOPIC} — watching for new DBZH scans")

            async for message in mqtt_client.messages:
                try:
                    payload = json.loads(message.payload)
                    await process_notification(http_client, payload)
                except (json.JSONDecodeError, ValueError, TypeError) as exc:
                    print(f"Skipping malformed notification: {exc}")


if __name__ == "__main__":
    anyio.run(main)
