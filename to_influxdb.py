import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


# =========================
# MQTT CONFIGURATION
# =========================

MQTT_BROKER = "172.16.2.117"
MQTT_PORT = 1883
MQTT_TOPIC = "vehiclecount/aggregated"


# =========================
# INFLUXDB CONFIGURATION
# =========================

INFLUXDB_URL = "http://172.16.2.117:8086"
INFLUXDB_TOKEN = "ai3V3vxPXNMwE_4aGePni-5uLU7MumFckIpHbYi5_O52LkpH38b9IM4WucD6RoKSm8oBx-Wy8ZOfSITZqrTQ7A=="
INFLUXDB_ORG = "e761e698e5720d2f"
INFLUXDB_BUCKET = "mini_project"


# =========================
# INFLUXDB CONNECTION
# =========================

influx_client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG
)

write_api = influx_client.write_api(
    write_options=SYNCHRONOUS
)


# =========================
# MQTT CALLBACK
# =========================

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker")

    client.subscribe(MQTT_TOPIC)

    print(f"Subscribed to: {MQTT_TOPIC}")


def on_message(client, userdata, msg):

    try:

        # Convert MQTT message into JSON
        data = json.loads(msg.payload.decode("utf-8"))

        print("\n[MQTT IN]")
        print(json.dumps(data, indent=4))


        # Extract values
        camera_id = data.get("camera_id", "UNKNOWN")
        student_id = data.get("student_id", "UNKNOWN")
        vehicle_counts = data.get(
            "vehicle_counts",
            {}
        )

        car = vehicle_counts.get("car", 0)
        truck = vehicle_counts.get("truck", 0)
        motorcycle = vehicle_counts.get("motorcycle", 0)

        total_vehicles = data.get(
            "total_vehicles",
            0
        )


        # Create InfluxDB point
        point = (
            Point("vehicle_count")
            .tag("camera_id", camera_id)
            .tag("student_id", student_id)
            .field("car", car)
            .field("truck", truck)
            .field("motorcycle", motorcycle)
            .field("total_vehicles", total_vehicles)
        )


        # Write to InfluxDB
        write_api.write(
            bucket=INFLUXDB_BUCKET,
            org=INFLUXDB_ORG,
            record=point
        )

        print("[INFLUXDB] Data written successfully")


    except json.JSONDecodeError:

        print("[ERROR] Received invalid JSON")

    except Exception as e:

        print(f"[ERROR] {e}")


# =========================
# MQTT CLIENT
# =========================

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.on_connect = on_connect
client.on_message = on_message


print(
    f"Connecting to MQTT broker "
    f"{MQTT_BROKER}:{MQTT_PORT}..."
)

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)


client.loop_forever()