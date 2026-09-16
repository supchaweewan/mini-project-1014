import json
import paho.mqtt.client as mqtt
from kafka import KafkaProducer


# =========================
# MQTT Configuration
# =========================

MQTT_BROKER = "172.16.2.117"
MQTT_PORT = 1883
MQTT_TOPIC = "vehiclecount/aggregated"


# =========================
# Kafka Configuration
# =========================

KAFKA_BROKER = "172.16.2.117:9092"
KAFKA_TOPIC = "vehicle_count_6610301014"


# =========================
# Kafka Producer
# =========================

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda value: json.dumps(value).encode("utf-8")
)


# =========================
# MQTT Callbacks
# =========================

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker")

    client.subscribe(MQTT_TOPIC)

    print(f"Subscribed to MQTT topic: {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        # Convert MQTT payload from bytes to JSON
        payload = json.loads(msg.payload.decode("utf-8"))

        print("\nReceived MQTT message:")
        print(json.dumps(payload, indent=4))

        # Send JSON to Kafka
        producer.send(
            KAFKA_TOPIC,
            value=payload
        )

        producer.flush()

        print(f"Sent message to Kafka topic: {KAFKA_TOPIC}")

    except json.JSONDecodeError:
        print("Received invalid JSON from MQTT")

    except Exception as e:
        print(f"Error sending message to Kafka: {e}")


# =========================
# MQTT Client
# =========================

mqtt_client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


# =========================
# Connect and Run
# =========================

print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")

mqtt_client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

print("MQTT → Kafka bridge is running...")

mqtt_client.loop_forever()