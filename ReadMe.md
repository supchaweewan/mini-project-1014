## Vehicle Checker (Vehicle Detection for Amount of Vehicles on an Intersection)

## Executive Summary
This project detects and scans vehicles on a specific road or intersection in Thailand, before verifying and calculating the preference of drivers around that area during the time it was detected. This is in analyzing the preference of what vehicle during what time of the day. For example, people might prefer to be on trucks or cars at night, while in the morning and evening there may be more motorcycles. This is to also observe vehicle quantities during times of the day, to see when the roads are the most active.

## Installation & Usage

1. Download the ZIP file or clone the repository
2. Ensure that the required libraries are present in the repository
3. Replace the following values in the python files as necessary
- Edge_Detect.py: MQTT_BROKER, STUDENT_ID, url
- gateway.py: MQTT_BROKER
- to_influxdb.py: MQTT_BROKER, INFLUX_TOKEN, INFLUX_URL, INFLUX_ORG
- model_training.py: INFLUX_TOKEN, INFLUX_URL, INFLUX_ORG
- to_kafka.py: MQTT_BROKER, KAFKA_BROKER
- kafka_ai_worker: KAFKA_BROKER, INFLUX_TOKEN, INFLUX_URL, INFLUX_ORG
4. Run each file in a dedicated terminal
- You MUST have enough data on influxdb before running model_training to obtain a traffic_model.pkl, which is used by kafka_ai_worker.py

## Required Libraries
Ensure that these libraries are imported and present in your work environment.
- OpenCV (opencv-python)
- ultralytics
- NumPy
- paho-mqtt
- influxdb-client
- kafka-python
- pandas
- joblib
- scikit-learn