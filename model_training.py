import pandas as pd
import numpy as np
import joblib

from influxdb_client import InfluxDBClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error


# ============================================================
# 1. InfluxDB configuration
# ============================================================

INFLUX_URL = "http://172.16.2.117:8086"
INFLUX_TOKEN = "ai3V3vxPXNMwE_4aGePni-5uLU7MumFckIpHbYi5_O52LkpH38b9IM4WucD6RoKSm8oBx-Wy8ZOfSITZqrTQ7A=="
INFLUX_ORG = "e761e698e5720d2f"
INFLUX_BUCKET = "mini_project"

# Change this if your bridge uses another measurement name
INFLUX_MEASUREMENT = "vehicle_count"


# ============================================================
# 2. Connect to InfluxDB
# ============================================================

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()


# ============================================================
# 3. Retrieve historical vehicle data
# ============================================================

query = f'''
from(bucket: "{INFLUX_BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) =>
      r["_measurement"] == "{INFLUX_MEASUREMENT}"
  )
  |> filter(fn: (r) =>
      r["_field"] == "car" or
      r["_field"] == "truck" or
      r["_field"] == "motorcycle" or
      r["_field"] == "total_vehicles"
  )
  |> pivot(
      rowKey: ["_time"],
      columnKey: ["_field"],
      valueColumn: "_value"
  )
  |> sort(columns: ["_time"])
'''

print("[InfluxDB] Retrieving historical traffic data...")

tables = query_api.query_data_frame(query)

if isinstance(tables, list):
    df = pd.concat(tables, ignore_index=True)
else:
    df = tables

print(f"[DATA] Retrieved {len(df)} records")


# ============================================================
# 4. Clean the dataset
# ============================================================

required_columns = [
    "_time",
    "car",
    "truck",
    "motorcycle"
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:
    print("\nERROR: Missing columns:")
    print(missing)
    print("\nAvailable columns:")
    print(df.columns.tolist())
    raise SystemExit


df["_time"] = pd.to_datetime(df["_time"], utc=True)

for column in ["car", "truck", "motorcycle"]:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df = df.dropna(
    subset=["car", "truck", "motorcycle"]
)

df = df.sort_values("_time").reset_index(drop=True)


# ============================================================
# 5. Create time-based features
# ============================================================

df["hour"] = df["_time"].dt.hour
df["day_of_week"] = df["_time"].dt.dayofweek

# Cyclic representation of time
df["hour_sin"] = np.sin(
    2 * np.pi * df["hour"] / 24
)

df["hour_cos"] = np.cos(
    2 * np.pi * df["hour"] / 24
)

df["day_sin"] = np.sin(
    2 * np.pi * df["day_of_week"] / 7
)

df["day_cos"] = np.cos(
    2 * np.pi * df["day_of_week"] / 7
)


# ============================================================
# 6. Create historical traffic features
# ============================================================

vehicle_types = [
    "car",
    "truck",
    "motorcycle"
]

for vehicle in vehicle_types:

    # Previous interval
    df[f"{vehicle}_lag1"] = df[vehicle].shift(1)

    # Two intervals ago
    df[f"{vehicle}_lag2"] = df[vehicle].shift(2)

    # Three intervals ago
    df[f"{vehicle}_lag3"] = df[vehicle].shift(3)

    # Recent average
    df[f"{vehicle}_rolling3"] = (
        df[vehicle]
        .shift(1)
        .rolling(3)
        .mean()
    )


# ============================================================
# 7. Create prediction targets
# ============================================================

# We predict the NEXT interval.

df["target_car"] = df["car"].shift(-1)
df["target_truck"] = df["truck"].shift(-1)
df["target_motorcycle"] = df["motorcycle"].shift(-1)


# Remove rows that don't have enough history
df = df.dropna().reset_index(drop=True)


# ============================================================
# 8. Define features
# ============================================================

features = [
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",

    "car_lag1",
    "car_lag2",
    "car_lag3",
    "car_rolling3",

    "truck_lag1",
    "truck_lag2",
    "truck_lag3",
    "truck_rolling3",

    "motorcycle_lag1",
    "motorcycle_lag2",
    "motorcycle_lag3",
    "motorcycle_rolling3"
]

targets = [
    "target_car",
    "target_truck",
    "target_motorcycle"
]


X = df[features]
y = df[targets]


# ============================================================
# 9. Train/test split
# ============================================================

# IMPORTANT:
# Don't randomly shuffle time-series data.
# Use the earlier data for training and later data for testing.

split_index = int(len(df) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print(f"[DATA] Training records: {len(X_train)}")
print(f"[DATA] Testing records:  {len(X_test)}")


# ============================================================
# 10. Train Random Forest
# ============================================================

print("[AI] Training Random Forest...")

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    min_samples_leaf=2
)

model.fit(X_train, y_train)


# ============================================================
# 11. Evaluate
# ============================================================

predictions = model.predict(X_test)

mae = mean_absolute_error(
    y_test,
    predictions
)

print("\n==============================")
print("MODEL EVALUATION")
print("==============================")
print(f"Mean Absolute Error: {mae:.2f}")


# ============================================================
# 12. Save model
# ============================================================

joblib.dump(
    {
        "model": model,
        "features": features
    },
    "traffic_model.pkl"
)

print("\n[AI] Model saved as traffic_model.pkl")

client.close()