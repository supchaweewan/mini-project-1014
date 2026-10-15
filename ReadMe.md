# Vehicle Checker (Vehicle Detection for Amount of Vehicles on an Intersection)

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
- kafka_ai_worker.py: KAFKA_BROKER, INFLUX_TOKEN, INFLUX_URL, INFLUX_ORG
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

# Vehicle Checker (ระบบตรวจจับและนับจำนวนยานพาหนะบริเวณทางแยก)

## บทสรุปผู้บริหาร (Executive Summary)

โครงงานนี้มีวัตถุประสงค์เพื่อตรวจจับและวิเคราะห์ยานพาหนะบนถนนหรือบริเวณทางแยกแห่งหนึ่งในประเทศไทย โดยนำข้อมูลที่ตรวจจับได้มาวิเคราะห์และคำนวณสัดส่วนของประเภทยานพาหนะที่พบในพื้นที่ดังกล่าว ณ ช่วงเวลาต่าง ๆ เพื่อศึกษาว่าผู้ใช้ถนนมีแนวโน้มใช้ยานพาหนะประเภทใดในแต่ละช่วงเวลาของวัน

ตัวอย่างเช่น ในช่วงเวลากลางคืนอาจพบรถบรรทุกหรือรถยนต์มากขึ้น ขณะที่ในช่วงเช้าและช่วงเย็นอาจพบรถจักรยานยนต์มากกว่า นอกจากนี้ โครงงานยังมีเป้าหมายเพื่อศึกษาปริมาณยานพาหนะในช่วงเวลาต่าง ๆ ของวัน และระบุช่วงเวลาที่การจราจรบนถนนมีความหนาแน่นหรือมีการเคลื่อนไหวมากที่สุด

## การติดตั้งและการใช้งาน (Installation & Usage)

1. ดาวน์โหลดไฟล์ ZIP ของโครงงาน หรือโคลน (Clone) Repository จาก GitHub
2. ตรวจสอบให้แน่ใจว่าไลบรารีที่จำเป็นได้รับการติดตั้งในสภาพแวดล้อมการทำงานแล้ว
3. แก้ไขค่าการตั้งค่าต่อไปนี้ในไฟล์ Python ให้เหมาะสมกับสภาพแวดล้อมของผู้ใช้งาน
- `Edge_Detect.py`: `MQTT_BROKER`, `STUDENT_ID`, `url`
- `gateway.py`: `MQTT_BROKER`
- `to_influxdb.py`: `MQTT_BROKER`, `INFLUX_TOKEN`, `INFLUX_URL`, `INFLUX_ORG`
- `model_training.py`: `INFLUX_TOKEN`, `INFLUX_URL`, `INFLUX_ORG`
- `to_kafka.py`: `MQTT_BROKER`, `KAFKA_BROKER`
- `kafka_ai_worker.py`: `KAFKA_BROKER`, `INFLUX_TOKEN`, `INFLUX_URL`, `INFLUX_ORG`

4. เรียกใช้งานไฟล์แต่ละไฟล์ผ่านหน้าต่าง Terminal แยกกัน
- **ข้อกำหนดสำคัญ:** ต้องมีข้อมูลการจราจรใน InfluxDB เพียงพอก่อนเรียกใช้งาน `model_training.py` เพื่อฝึกโมเดลและสร้างไฟล์ `traffic_model.pkl` ซึ่งจำเป็นสำหรับการทำงานของ `kafka_ai_worker.py`

## ไลบรารีที่จำเป็น (Required Libraries)

ตรวจสอบให้แน่ใจว่าไลบรารีต่อไปนี้ได้รับการติดตั้งและพร้อมใช้งานในสภาพแวดล้อม Python

- OpenCV (`opencv-python`)
- Ultralytics (`ultralytics`)
- NumPy (`numpy`)
- Paho MQTT (`paho-mqtt`)
- InfluxDB Client (`influxdb-client`)
- Kafka Python (`kafka-python`)
- Pandas (`pandas`)
- Joblib (`joblib`)
- Scikit-learn (`scikit-learn`)