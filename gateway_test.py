import asyncio
import json
from datetime import datetime, timezone

UDP_PORT = 5005

payload_buffer = []

AGGREGATION_WINDOW_SEC = 30

class UDPReceiverProtocol(asyncio.DatagramProtocol):

    def connection_made(self, transport):
        self.transport = transport

        print("==========================================")
        print("       TRAFFIC GATEWAY - TEST MODE")
        print("==========================================")
        print(f"Listening for UDP on port {UDP_PORT}")
        print("MQTT: DISABLED")
        print("==========================================")


    def datagram_received(self, data, addr):

        try:
            message = data.decode("utf-8")
            data_json = json.loads(message)

            payload_buffer.append(data_json)

            print("\n[UDP IN] Received payload!")
            print(f"Sender: {addr}")

            print(json.dumps(data_json, indent=4))

        except json.JSONDecodeError:
            print("[ERROR] Received invalid JSON")

        except Exception as e:
            print(f"[ERROR] Failed to process packet: {e}")
async def aggregation_task():

    global payload_buffer

    while True:

        # Wait for the aggregation window
        await asyncio.sleep(AGGREGATION_WINDOW_SEC)

        # Check if we received anything
        if len(payload_buffer) == 0:
            print("[AGGREGATION] No traffic data received.")
            continue

        print(
            f"\n[AGGREGATION] Processing "
            f"{len(payload_buffer)} payload(s)"
        )

        # --------------------------------------
        # Calculate vehicle totals
        # --------------------------------------

        car_total = sum(
            payload.get("vehicle_counts", {}).get("car", 0)
            for payload in payload_buffer
        )

        truck_total = sum(
            payload.get("vehicle_counts", {}).get("truck", 0)
            for payload in payload_buffer
        )

        motorcycle_total = sum(
            payload.get("vehicle_counts", {}).get("motorcycle", 0)
            for payload in payload_buffer
        )

        total_vehicles = (
            car_total
            + truck_total
            + motorcycle_total
        )

        # --------------------------------------
        # Get camera / ROI information
        # --------------------------------------

        camera_id = payload_buffer[0].get(
            "camera_id",
            "UNKNOWN_CAMERA"
        )

        roi_id = payload_buffer[0].get(
            "roi_id",
            "UNKNOWN_ROI"
        )

        # --------------------------------------
        # Create aggregated payload
        # --------------------------------------

        now = datetime.now(timezone.utc)

        aggregated_payload = {
            "timestamp": now.isoformat(),
            "camera_id": camera_id,
            "roi_id": roi_id,
            "aggregation_interval_seconds":
                AGGREGATION_WINDOW_SEC,

            "payload_count": len(payload_buffer),

            "vehicle_counts": {
                "car": car_total,
                "truck": truck_total,
                "motorcycle": motorcycle_total
            },

            "total_vehicles": total_vehicles
        }

        # --------------------------------------
        # Convert to JSON
        # --------------------------------------

        mqtt_message = json.dumps(
            aggregated_payload,
            indent=4
        )

        print("\n[MQTT OUT]")
        print(mqtt_message)

        payload_buffer.clear()

async def main():

    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPReceiverProtocol(),
        local_addr=("0.0.0.0", UDP_PORT)
    )

    print("\n[Gateway] Ready and waiting for data...\n")
    asyncio.create_task(aggregation_task())
    try:
        while True:
            await asyncio.sleep(3600)

    except KeyboardInterrupt:
        pass

    finally:
        transport.close()
    


if __name__ == "__main__":
    asyncio.run(main())