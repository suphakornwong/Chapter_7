import cv2
import numpy as np
import pyfirmata
from ultralytics import YOLO
import time

# 1. การตั้งค่า Servo และ Arduino
PORT = "COM5"  # ตรวจสอบ Port ให้ถูกต้องตรงกับ Arduino IDE
SERVO_PIN_X = 9
SERVO_PIN_Y = 10

SERVO_X_MIN_LIMIT = 55
SERVO_X_MAX_LIMIT = 125
SERVO_Y_MIN_LIMIT = 55
SERVO_Y_MAX_LIMIT = 125
SMOOTHING_FACTOR = 0.6

OFFSET_X = 15
OFFSET_Y = 0

# โหลดโมเดล YOLO
model = YOLO("BestNano.pt")

# ตั้งค่ากล้อง
cap = cv2.VideoCapture(1) # ปรับเป็น 0 กล้อง Laptop หรือ 1 กล้อง USB
ws, hs = 1280, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, ws)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hs)

if not cap.isOpened():
    print("Camera couldn't Access!!!")
    exit()

# เชื่อมต่อ Arduino
try:
    board = pyfirmata.Arduino(PORT)
    iter8 = pyfirmata.util.Iterator(board)
    iter8.start()
    servo_pinX = board.get_pin(f'd:{SERVO_PIN_X}:s')
    servo_pinY = board.get_pin(f'd:{SERVO_PIN_Y}:s')
    print("Arduino Connected Successfully")
except Exception as e:
    print(f"Connection Error: {e}")
    exit()

# ตัวแปรเก็บตำแหน่งปัจจุบัน
current_servo_x = 100
current_servo_y = 90

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

prev_time = 0

prev_servo_x = -1
prev_servo_y = -1

while True:
    success, img = cap.read()
    if not success:
        continue

    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    results = model(img, stream=True, verbose=False)

    target_found = False
    
    target_x_deg = 100
    target_y_deg = 90

    # วาด Bounding Box
    for r in results:
        boxes = r.boxes
        if len(boxes) > 0:
            best_box = max(boxes, key=lambda x: x.conf[0])
            
            x1, y1, x2, y2 = map(int, best_box.xyxy[0])
            fx = int((x1 + x2) / 2)
            fy = int((y1 + y2) / 2)
            target_found = True

            target_x_deg = np.interp(fx, [0, ws], [SERVO_X_MAX_LIMIT, SERVO_X_MIN_LIMIT])
            target_y_deg = np.interp(fy, [0, hs], [SERVO_Y_MAX_LIMIT, SERVO_Y_MIN_LIMIT])
            
            target_x_deg += OFFSET_X
            target_y_deg += OFFSET_Y

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(img, (fx, fy), 5, (0, 0, 255), cv2.FILLED)
            cv2.putText(img, "TARGET LOCKED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    if target_found:
        current_servo_x += (target_x_deg - current_servo_x) * SMOOTHING_FACTOR
        current_servo_y += (target_y_deg - current_servo_y) * SMOOTHING_FACTOR
    else:
        pass

    final_x = int(clamp(current_servo_x, 0, 180))
    final_y = int(clamp(current_servo_y, 0, 180))

    if abs(final_x - prev_servo_x) >= 1 or abs(final_y - prev_servo_y) >= 1:
        servo_pinX.write(final_x)
        servo_pinY.write(final_y)
        prev_servo_x = final_x
        prev_servo_y = final_y

    # แสดงผลในส่วน User interface
    cv2.putText(img, f'Servo: {final_x}, {final_y}', (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)
    cv2.putText(img, f'FPS: {int(fps)}', (ws-150, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
    
    cv2.imshow("Laser Bird Repellent", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
board.exit()