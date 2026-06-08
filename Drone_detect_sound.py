import cv2
import time
import serial
from ultralytics import YOLO

arduino_port = "COM6" # ตรวจสอบ Port ให้ถูกต้องตรงกับ Arduino IDE
baud_rate = 9600 # ตั้งค่าให้ตรงกับ Arduino IDE

try:
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)
    time.sleep(2)
    print(f"Connected to Arduino on {arduino_port}")
except Exception as e:
    print(f"Failed to connect to Arduino: {e}")
    exit()

# --- โหลดโมเดล YOLO ---
model = YOLO("BestNano.pt")

# --- ตั้งค่ากล้อง ---
cap = cv2.VideoCapture(1) # ปรับเป็น 0 กล้อง Laptop หรือ 1 กล้อง USB
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

if not cap.isOpened():
    print("Cannot access webcam!")
    exit()

last_play_time = 0
sound_cooldown = 5

print("Starting Bird Detection System...")

while True:
    success, img = cap.read()
    if not success:
        continue

    results = model(img, stream=True)
    bird_detected = False
    
    # วาด Bounding Box
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            conf = box.conf[0]
            cls = int(box.cls[0])
            class_name = model.names[cls]

            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3) # สีแดง
            cv2.putText(img, f"{class_name} {conf:.2f}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            bird_detected = True

    # --- ส่วนสั่งงาน Arduino ---
    if bird_detected:
        current_time = time.time()
        
        if current_time - last_play_time > sound_cooldown:
            print("Bird Detected! Sending signal to Arduino...")
            
            ser.write(b'1') # ส่งตัวอักษร '1' (byte) ไปทาง Serial
            
            last_play_time = current_time
            
            cv2.putText(img, "WARNING: BIRD DETECTED - PLAYING SOUND", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    cv2.imshow("Bird Guard System", img) # แสดงผลภาพ

    if cv2.waitKey(1) & 0xFF == ord('q'): # กด 'q' เพื่อออก
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
print("System Shutdown.")
