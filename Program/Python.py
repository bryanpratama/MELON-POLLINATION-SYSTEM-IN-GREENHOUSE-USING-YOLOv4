import cv2
import numpy as np
import serial
import time

net = cv2.dnn.readNet("C:/yolov4_melon_v2/darknet/cfg/yolov4-custom.cfg", "C:/yolov4_melon_v2/training/yolov4-custom_6000.weights")

class_names = []
with open("C:/yolov4_melon_v2/darknet/data/obj.names", "r") as f:
    class_names = [line.strip() for line in f.readlines()]

video = cv2.VideoCapture(1)

input_width = 416
input_height = 416

object_count = {}
nms_threshold = 0.4

# Inisialisasi koneksi serial dengan Arduino
arduino = serial.Serial('COM5 ', 9600)  
last_sent_time = time.time()
countdown_start_time = time.time()
countdown_duration = 5
flower_detected = False

color_bunga1 = (255, 0, 0)  # Merah
color_bunga2 = (0, 255, 0)  # Hijau
color_bunga3 = (0, 0, 255)  # Biru
color_hijau = (0, 255, 0)  # Hijau
koordinat_hijau = (20, 20)  # Koordinat titik hijau (x, y)
koordinat_tengah_hijau = (0, 0)  # Inisialisasi koordinat titik tengah hijau
tengah_tidak_terdeteksi = True

while True:
    ret, frame = video.read()
    resized_frame = cv2.resize(frame, (input_width, input_height))
    blob = cv2.dnn.blobFromImage(resized_frame, 1 / 255.0, (input_width, input_height), swapRB=True, crop=False)
    net.setInput(blob)
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
    outs = net.forward(output_layers)
    object_presence = {}
    class_ids = []
    confidences = []
    boxes = []
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * frame.shape[1])
                center_y = int(detection[1] * frame.shape[0])
                box_width = int(detection[2] * frame.shape[1])
                box_height = int(detection[3] * frame.shape[0])
                left = int(center_x - box_width / 2)
                top = int(center_y - box_height / 2)
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([left, top, box_width, box_height])
                label = class_names[class_id]
                if label in object_presence:
                    object_presence[label] += 1
                else:
                    object_presence[label] = 1
    indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, nms_threshold)
    indices = [i for i in indices]
    object_count = {}
    for i in indices:
        label = class_names[class_ids[i]]
        if label in object_count:
            object_count[label] += 1
        else:
            object_count[label] = 1
    colors = np.random.uniform(0, 255, size=(len(class_names), 3))
    for i in indices:
        x, y, w, h = boxes[i]
        label = class_names[class_ids[i]]
        confidence = confidences[i]
        if label == "Bunga Betina Kuncup":
            color = color_bunga1
        elif label == "Bunga Betina Mekar":
            color = color_bunga2
        elif label == "Bunga Jantan":
            color = color_bunga3
        else:
            color = colors[class_ids[i]]
        cv2.rectangle(frame, (x, y), (x + w, y + h),color, 2)
        cv2.putText(frame, f"{label}: {confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    current_time = time.time()
    if current_time - countdown_start_time < countdown_duration and "Bunga Betina Mekar" in object_count:
        countdown = countdown_duration - int(current_time - countdown_start_time)
        cv2.putText(frame, f"Next Send in: {countdown} s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    elif any(label == "Bunga Betina Mekar" for label in object_count.keys()):
        tengah_tidak_terdeteksi = True  
        for i in indices:
            x, y, w, h = boxes[i]
            center_x = x + w // 2
            center_y = y + h // 2
            if label == "Bunga Betina Mekar":
                koordinat_tengah_hijau = (center_x, center_y)
                cv2.circle(frame, koordinat_hijau, 10, color_hijau, -1)
                cv2.circle(frame, koordinat_tengah_hijau, 5, color_hijau, -1)
                tengah_tidak_terdeteksi = False
            else:
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
            center_threshold = frame.shape[1] // 10  
            if abs(center_x - frame.shape[1] // 2) < center_threshold:
                if not flower_detected:
                    current_time = time.time()
                    if current_time - last_sent_time >= 5:
                        arduino.write(b'1')  # Mengirim angka '1' ke Arduino
                        last_sent_time = current_time
                        countdown_start_time = time.time()
                    flower_detected = True
                cv2.putText(frame, "Mulai Polinasi", (35, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                break
        else:
            flower_detected = False
    else:
        if flower_detected:
            arduino.write(b'')  # Mengirim angka '0' ke Arduino
            flower_detected = False
        if tengah_tidak_terdeteksi:
            koordinat_tengah_hijau = (0, 0)
        cv2.circle(frame, koordinat_hijau, 10, (0, 0, 255), -1)

    cv2.putText(frame, "Bunga Terdeteksi:", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    y_offset = 90
    for label, count in object_count.items():
        if count > 0:
            cv2.putText(frame, f"{label}: {count}", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            y_offset += 30

    # Garis vertikal di tengah frame
    cv2.line(frame, (frame.shape[1] // 2, 0), (frame.shape[1] // 2, frame.shape[0]), (0, 255, 0), 1)

    cv2.imshow("Deteksi Objek YOLOv4", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

arduino.close()
video.release()
cv2.destroyAllWindows()