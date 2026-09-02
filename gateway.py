import asyncio
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone

UDP_PORT = 5005

MQTT_BROKER = "172.16.2.117"   # Change to your MQTT broker IP
MQTT_PORT = 1883

MQTT_TOPIC = "traffic/aggregated"

# Edge sends data every 10 seconds.
# Gateway aggregates approximately 2 minutes of data.
AGGREGATION_WINDOW_SEC = 120

MQTT_CLIENT_ID = "TRAFFIC_GATEWAY"
# ==================================================================

# บัฟเฟอร์สำหรับเก็บรวบรวมค่าจากเซนเซอร์แต่ละตัวแยกออกจากกัน (Per-Sensor Buffer)
payload_buffers = []

# สร้าง Client สำหรับเชื่อมต่อ MQTT
try:
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    # สำหรับ Paho-MQTT v1.x รุ่นเก่า
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID)

class AsyncUDPReceiverProtocol(asyncio.DatagramProtocol):
    def connection_made(self, transport):
        self.transport = transport
        print("==================================================================")
        print(f" IoT Gateway ({MQTT_CLIENT_ID}) [ACTIVE]")
        print(f" - รอรับข้อมูล UDP ที่พอร์ต: {UDP_PORT}")
        print(f" - ช่วงเวลาทำ Aggregation: {AGGREGATION_WINDOW_SEC} วินาที")
        print("==================================================================")

    def datagram_received(self, data, addr):
        global payload_buffer

        try:
            # Convert UDP data to JSON
            message = data.decode("utf-8")
            data_json = json.loads(message)

            # Add received payload to buffer
            payload_buffer.append(data_json)

            print(
                f"[UDP IN] Received traffic payload "
                f"from {addr}"
            )

            print(
                f"   -> Buffer: "
                f"{len(payload_buffer)} payload(s)"
            )

        except json.JSONDecodeError:
            print(
                f"[ERROR] Invalid JSON received from {addr}"
            )

        except Exception as e:
            print(
                f"[ERROR] Failed to process UDP data: {e}"
            )

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

        # --------------------------------------
        # Publish to MQTT
        # --------------------------------------

        if mqtt_client.is_connected():

            mqtt_client.publish(
                MQTT_TOPIC,
                mqtt_message,
                qos=1
            )

            print(
                f"[MQTT] Published to "
                f"'{MQTT_TOPIC}'"
            )

        else:

            print(
                "[ERROR] MQTT broker is not connected."
            )

        # --------------------------------------
        # Clear buffer
        # --------------------------------------

        payload_buffer.clear()

async def main():
    # 1. เริ่มทำการเชื่อมต่อกับ MQTT Broker ส่วนกลาง
    print(f"กำลังเชื่อมต่อกับ MQTT Broker ที่ {MQTT_BROKER}:{MQTT_PORT}...")
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print("เชื่อมต่อ MQTT Broker สำเร็จ!")
    except Exception as e:
        print(f"ไม่สามารถเชื่อมต่อ MQTT Broker ได้: {e}")
        return

    # 2. ทำการเปิดพอร์ตรับข้อมูล UDP (Port 5005)
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: AsyncUDPReceiverProtocol(),
        local_addr=('0.0.0.0', UDP_PORT)
    )

    # 3. รัน Task ประมวลผลข้อมูล Aggregation แยกเซนเซอร์ ควบคู่ไปด้วยแบบไม่ขัดจังหวะกัน
    asyncio.create_task(aggregation_task())

    try:
        # รักษาลูปให้สคริปต์รันทำงานอย่างต่อเนื่องแบบ Non-blocking
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("\nกำลังยกเลิกการทำงาน...")
    finally:
        transport.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("ปิดการทำงานของ Gateway เรียบร้อยแล้ว")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nปิดโปรแกรมสำเร็จด้วยคีย์บอร์ด")