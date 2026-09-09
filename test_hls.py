import cv2
import time

URL = "https://camera1.iticfoundation.org/hls/10.8.0.23_8555.m3u8"

cap = cv2.VideoCapture(URL)

if not cap.isOpened():
    print("[ERROR] Could not open HLS stream")
    exit()

print("[OK] HLS stream opened")

frame_count = 0
start_time = time.time()

while True:

    print("[DEBUG] Reading frame...")

    ret, frame = cap.read()

    if not ret:
        print("[ERROR] Failed to read frame")
        break

    frame_count += 1

    print(f"[OK] Frame {frame_count} received")

    cv2.imshow("HLS Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()