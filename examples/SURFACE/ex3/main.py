"""SURFACE / ex3 — Threshold alerting via MQTT (event-driven usage).

Persona: a person who needs to know the instant any station in a region reports 
for example a dangerous wind gust or rain rate — not on some polling cadence, 
but as soon as the observation lands.

E-SOH publishes a notification over MQTT for every new observation
record (topic hierarchy: country/organization/station(wigos_id)/observation).
This example subscribes and raises an alert the moment a threshold is
crossed inside the region of interest — the event-driven counterpart to
polling a REST endpoint.

MQTT broker: observations.meteogate.eu:443 (WebSocket over TLS), 
Username: "everyone"
Password: "everyone"

Usage:
    uv run python main.py
"""

from __future__ import annotations

import json

import aiomqtt
import anyio

MQTT_HOST = "observations.meteogate.eu"
MQTT_PORT = 443
MQTT_USERNAME = "everyone"
MQTT_PASSWORD = "everyone"
# '+' wildcards the station wigos_id — every station in the region.
# '#' wildcards the observation type (standard_name) — every observation.
# Use for example fi/fmi/+/# to get every observation from every FMI station in Finland.
# Use for example nl/knmi/+/# to get every observation from every KNMI station in the Netherlands.
# NOTE! Some of the data is flowing in from GTS / WIS2, use eu/eumetnet/wigos_id/# if you know
# the WIGOS ID of the station you want to monitor, otherwise you will get a lot of noise.
TOPIC = "no/met/+/#"

# standard_name -> threshold; alert when the observed value exceeds it.
ALERT_THRESHOLDS = {
    "wind_speed_of_gust": 20.0,  # m/s
    "precipitation_rate": 30.0,  # mm/h
}


async def process_notification(payload: dict) -> None:
    properties = payload.get("properties", {})
    station_name = properties.get("platform_name", "unknown station")
    platform_id = properties.get("platform", "unknown platform")
    content = properties.get("content", {})

    standard_name = content.get("standard_name")
    threshold = ALERT_THRESHOLDS.get(standard_name)
    if threshold is None:
        return

    value = content.get("value")
    # NOTE!: Comment out the next line if you don't want to see every observation, only the alerts.
    print(f"Received {standard_name} = {value} from {station_name} ({platform_id})")
    if value is not None and float(value) > threshold:
        print(f"ALERT — {station_name}: {standard_name} = {value} > {threshold}")


async def main() -> None:
    async with aiomqtt.Client(
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        username=MQTT_USERNAME,
        password=MQTT_PASSWORD,
        transport="websockets",
        tls_params=aiomqtt.TLSParameters(),
        websocket_path="/mqtt/",
        websocket_headers={"Host": MQTT_HOST},
    ) as mqtt_client:
        await mqtt_client.subscribe(TOPIC)
        print(f"Subscribed to {TOPIC} — watching for threshold breaches...")

        async for message in mqtt_client.messages:
            try:
                payload = json.loads(message.payload)
                await process_notification(payload)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                print(f"Skipping malformed notification: {exc}")


if __name__ == "__main__":
    anyio.run(main)
