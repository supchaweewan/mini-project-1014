import json
import joblib
import numpy as np
import pandas as pd

from collections import deque
from datetime import datetime, timezone

from kafka import KafkaConsumer

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


# ============================================================
# 1. Kafka configuration
# ============================================================

KAFKA_BROKER = "172.16.2.117:9092"

KAFKA_TOPIC = "vehicle_count_6610301014"

KAFKA_GROUP = "traffic-ai-worker-6610301014"


# ============================================================
# 2. InfluxDB configuration
# ============================================================

INFLUX_URL = "http://172.16.2.117:8086"
INFLUX_TOKEN = "ai3V3vxPXNMwE_4aGePni-5uLU7MumFckIpHbYi5_O52LkpH38b9IM4WucD6RoKSm8oBx-Wy8ZOfSITZqrTQ7A=="
INFLUX_ORG = "e761e698e5720d2f"

INFLUX_BUCKET = "mini_project"


# ============================================================
# 3. Load trained model
# ============================================================

print("[AI] Loading traffic prediction model...")

saved_model = joblib.load(
    "traffic_model.pkl"
)

model = saved_model["model"]
features = saved_model["features"]

print("[AI] Model loaded successfully.")


# ============================================================
# 4. Connect to Kafka
# ============================================================

print(
    f"[Kafka] Connecting to {KAFKA_BROKER}..."
)

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    group_id=KAFKA_GROUP,
    auto_offset_reset="latest"
)

print(
    f"[Kafka] Listening to topic: {KAFKA_TOPIC}"
)


# ============================================================
# 5. Connect to InfluxDB
# ============================================================

db_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = db_client.write_api(
    write_options=SYNCHRONOUS
)

print("[InfluxDB] Connected.")


# ============================================================
# 6. Historical buffer
# ============================================================

history = deque(
    maxlen=3
)


# ============================================================
# 7. Create ML feature vector
# ============================================================

def create_features(
    timestamp,
    history
):

    dt = pd.to_datetime(
        timestamp,
        utc=True
    )

    hour = dt.hour
    day_of_week = dt.dayofweek

    row = {
        "hour_sin":
            np.sin(2 * np.pi * hour / 24),

        "hour_cos":
            np.cos(2 * np.pi * hour / 24),

        "day_sin":
            np.sin(2 * np.pi * day_of_week / 7),

        "day_cos":
            np.cos(2 * np.pi * day_of_week / 7)
    }

    cars = [
        item["car"]
        for item in history
    ]

    trucks = [
        item["truck"]
        for item in history
    ]

    motorcycles = [
        item["motorcycle"]
        for item in history
    ]

    row["car_lag1"] = cars[-1]
    row["car_lag2"] = cars[-2]
    row["car_lag3"] = cars[-3]
    row["car_rolling3"] = np.mean(cars)

    row["truck_lag1"] = trucks[-1]
    row["truck_lag2"] = trucks[-2]
    row["truck_lag3"] = trucks[-3]
    row["truck_rolling3"] = np.mean(trucks)

    row["motorcycle_lag1"] = motorcycles[-1]
    row["motorcycle_lag2"] = motorcycles[-2]
    row["motorcycle_lag3"] = motorcycles[-3]
    row["motorcycle_rolling3"] = np.mean(motorcycles)

    return pd.DataFrame(
        [row],
        columns=features
    )


# ============================================================
# 8. Real-time Kafka processing
# ============================================================

print("\n==============================================")
print(" TRAFFIC AI WORKER [RUNNING]")
print("==============================================\n")


for message in consumer:

    try:

        # ----------------------------------------------------
        # Decode Kafka JSON
        # ----------------------------------------------------

        raw_data = message.value.decode(
            "utf-8"
        )

        data = json.loads(raw_data)


        # ----------------------------------------------------
        # Extract vehicle counts
        # ----------------------------------------------------

        timestamp = data.get(
            "timestamp"
        )

        camera_id = data.get(
            "camera_id",
            "UNKNOWN_CAMERA"
        )

        counts = data.get(
            "vehicle_counts",
            {}
        )

        car = int(
            counts.get("car", 0)
        )

        truck = int(
            counts.get("truck", 0)
        )

        motorcycle = int(
            counts.get("motorcycle", 0)
        )


        # ----------------------------------------------------
        # Store in history
        # ----------------------------------------------------

        history.append({
            "car": car,
            "truck": truck,
            "motorcycle": motorcycle
        })


        print("\n[EVENT]")
        print(f"Camera: {camera_id}")
        print(f"Car: {car}")
        print(f"Truck: {truck}")
        print(f"Motorcycle: {motorcycle}")


        # ----------------------------------------------------
        # Wait until we have 3 previous observations
        # ----------------------------------------------------

        if len(history) < 3:

            print(
                f"[AI] Collecting history "
                f"({len(history)}/3)..."
            )

            continue


        # ----------------------------------------------------
        # Create ML features
        # ----------------------------------------------------

        X = create_features(
            timestamp,
            history
        )


        # ----------------------------------------------------
        # Predict next interval
        # ----------------------------------------------------

        prediction = model.predict(X)[0]


        predicted_car = max(
            0,
            round(float(prediction[0]))
        )

        predicted_truck = max(
            0,
            round(float(prediction[1]))
        )

        predicted_motorcycle = max(
            0,
            round(float(prediction[2]))
        )


        predicted_total = (
            predicted_car
            + predicted_truck
            + predicted_motorcycle
        )


        # ----------------------------------------------------
        # Calculate vehicle rates
        # ----------------------------------------------------

        if predicted_total > 0:

            car_rate = (
                predicted_car
                / predicted_total
                * 100
            )

            truck_rate = (
                predicted_truck
                / predicted_total
                * 100
            )

            motorcycle_rate = (
                predicted_motorcycle
                / predicted_total
                * 100
            )

        else:

            car_rate = 0
            truck_rate = 0
            motorcycle_rate = 0


        # ----------------------------------------------------
        # Determine most likely vehicle type
        # ----------------------------------------------------

        predicted_rates = {
            "car": car_rate,
            "truck": truck_rate,
            "motorcycle": motorcycle_rate
        }


        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        print("\n================ AI PREDICTION ================")

        print(
            f"Predicted Car:        {predicted_car}"
        )

        print(
            f"Predicted Truck:      {predicted_truck}"
        )

        print(
            f"Predicted Motorcycle: {predicted_motorcycle}"
        )

        print(
            f"Predicted Total:      {predicted_total}"
        )

        print("\nPredicted Vehicle Rates:")

        print(
            f"Car:        {car_rate:.2f}%"
        )

        print(
            f"Truck:      {truck_rate:.2f}%"
        )

        print(
            f"Motorcycle: {motorcycle_rate:.2f}%"
        )

        print(
            "===============================================\n"
        )


        # ----------------------------------------------------
        # Write AI result to InfluxDB
        # ----------------------------------------------------

        point = (
            Point("traffic_ai_prediction")
            .tag(
                "camera_id",
                camera_id
            )
            .field(
                "predicted_car",
                predicted_car
            )
            .field(
                "predicted_truck",
                predicted_truck
            )
            .field(
                "predicted_motorcycle",
                predicted_motorcycle
            )
            .field(
                "predicted_total",
                predicted_total
            )
            .field(
                "car_rate",
                float(car_rate)
            )
            .field(
                "truck_rate",
                float(truck_rate)
            )
            .field(
                "motorcycle_rate",
                float(motorcycle_rate)
            )
        )


        write_api.write(
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG,
            record=point
        )


        print(
            "[InfluxDB] AI prediction written successfully."
        )


    except Exception as e:

        print(
            f"[ERROR] AI processing failed: {e}"
        )