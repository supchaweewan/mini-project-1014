from collections import defaultdict, Counter
import cv2
from ultralytics import YOLO
import json
import time
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime
import socket

model = YOLO("yolov8n.pt")

# this is going to be the MQTT Broker section
"""MQTT_BROKER = "172.16.2.117"
MQTT_PORT = 1883
MQTT_TOPIC = "traffic/camera/ccs06"
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop.start()
"""

# How many recent classifications to remember
MAX_HISTORY = 15

TARGET_FPS = 15
FRAME_INTERVAL = 1.0 / TARGET_FPS

url = "https://camerai1.iticfoundation.org/hls/ccs06.m3u8"

"""

GATEWAY_IP = "127.0.0.1"
GATEWAY_PORT = 5005


udp_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)"""

ROI_POINTS = np.array([(360, 850), (0, 200), (340, 110), (720, 180)], dtype=np.int32)
# ID -> list of recent classifications
vehicle_history = defaultdict(list)

# ID -> final/stable classification
vehicle_classes = {}

# Total number of unique vehicles detected
total_counts = Counter()

# Track IDs that have already been counted
counted_ids = set()

interval_counts = Counter()

# Track IDs seen during the current 10-second interval
interval_ids = set()

PAYLOAD_INTERVAL = 5

last_payload_time = time.time()

cap = cv2.VideoCapture(url)



while True:

    frame_start = time.time() 

    ret, frame = cap.read()

    if not ret:
        break

    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        classes=[2, 3, 7],
        conf=0.3
    )

    boxes = results[0].boxes

    # IDs currently visible in this frame
    active_ids = set()

    if boxes.id is not None:

        track_ids = boxes.id.int().cpu().tolist()

        for box, track_id in zip(boxes, track_ids):

            active_ids.add(track_id)

            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            x1, y1, x2, y2 = box.xyxy[0].int().cpu().tolist()

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            inside_roi = cv2.pointPolygonTest(
                ROI_POINTS,
                (center_x, center_y),
                False
            ) >= 0

            # Add classification to history
            vehicle_history[track_id].append(class_name)

            # Limit history length
            if len(vehicle_history[track_id]) > MAX_HISTORY:
                vehicle_history[track_id].pop(0)

            # Determine most common classification
            final_class = Counter(
                vehicle_history[track_id]
            ).most_common(1)[0][0]

            vehicle_classes[track_id] = final_class
            if len(vehicle_history[track_id]) >= 5:
                # Count this vehicle only once overall
                if track_id not in counted_ids:

                    counted_ids.add(track_id)
                    total_counts[final_class] += 1


                # Count this vehicle only once during the current
                # 10-second interval
                if track_id not in interval_ids:

                    interval_ids.add(track_id)
                    interval_counts[final_class] += 1
    # Count vehicles currently visible
    current_counts = Counter()

    for track_id in active_ids:

        class_name = vehicle_classes.get(track_id)

        if class_name:
            current_counts[class_name] += 1


    current_time = time.time()

    if current_time - last_payload_time >= PAYLOAD_INTERVAL:
        # Create JSON payload for this 10-second period
        payload = {
            "timestamp": datetime.now().isoformat(sep=' '),
            "camera_id": "CAM_ITIC_CCS06",
            "roi_id": "BEFORE_INTERSECTION",
            "interval_seconds": PAYLOAD_INTERVAL,
            "vehicle_counts": {
                "car": interval_counts["car"],
                "truck": interval_counts["truck"],
                "motorcycle": interval_counts["motorcycle"]
            },
            "total_vehicles": sum(interval_counts.values())
        }

        # Convert to JSON
        json_payload = json.dumps(payload, indent=4)

        print("\nJSON PAYLOAD:")
        print(json_payload)

        """        udp_socket.sendto(
                    json_payload.encode("utf-8"),
                    (GATEWAY_IP, GATEWAY_PORT)
                )

                print(
                    f"[UDP OUT] Sent payload to {GATEWAY_IP}:{GATEWAY_PORT}"
                )"""
        #client.publish(MQTT_TOPIC, json_payload)

        # Reset the interval counters
        interval_counts.clear()
        
        interval_ids.clear()

        # Reset the timer
        last_payload_time = current_time
    annotated_frame = results[0].plot()
    cv2.polylines(
        annotated_frame,
        [ROI_POINTS],
        isClosed=True,
        color=(0, 255, 0),
        thickness=2
    )
    cv2.imshow("Tracking Vehicles", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    elapsed = time.time() - frame_start
    sleep_time = FRAME_INTERVAL - elapsed
    if sleep_time > 0:
        time.sleep(sleep_time)

        
cap.release()
cv2.destroyAllWindows()