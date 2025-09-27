import cv2
import numpy as np
import dlib
from imutils import face_utils
import serial
import serial.tools.list_ports
import time
from datetime import datetime
from geopy.geocoders import Nominatim
import database_handler  # Import the database handler module

# -------------------------------
# INITIALIZE DATABASE
# -------------------------------
database_handler.init_db()

# -------------------------------
# CONNECT TO ARDUINO (Auto-detect port)
# -------------------------------
ports = [p.device for p in serial.tools.list_ports.comports()]
s = None

if ports:
    try:
        s = serial.Serial(ports[0], 9600, timeout=1)
        print(f"[INFO] Connected to Arduino on {ports[0]}")
    except Exception as e:
        print(f"[ERROR] Could not connect to {ports[0]}: {e}")
else:
    print("[ERROR] No COM ports found!")

# -------------------------------
# FACE DETECTION SETUP
# -------------------------------
cap = cv2.VideoCapture(0)
hog_face_detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

sleep = 0
drowsy = 0
active = 0
status = ""
color = (0, 0, 0)

# ✅ NEW: Setup geolocator
geolocator = Nominatim(user_agent="driver_drowsiness_system")

def compute(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

def blinked(a, b, c, d, e, f):
    up = compute(b, d) + compute(c, e)
    down = compute(a, f)
    ratio = up / (2.0 * down)
    if ratio > 0.25:
        return 
    elif 0.21 < ratio <= 0.25:
        return 1
    else:
        return 0

# -------------------------------
# MAIN LOOP
# -------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to capture frame from camera.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = hog_face_detector(gray)

    # -------------------------------
    # Read messages from Arduino (GPS, alerts, etc.)
    # -------------------------------
    if s and s.in_waiting > 0:
        incoming = s.readline().decode(errors="ignore").strip()
        if incoming:
            if "GPS Location" in incoming:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # ✅ Extract lat/lng
                try:
                    parts = incoming.split("Lat:")[1].split(", Lng:")
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())

                    # ✅ Reverse geocode -> Place name
                    location = geolocator.reverse((lat, lng), language="en")

                    if location:
                        print(f"[GPS] {now} -> Lat: {lat}, Lng: {lng} | Place: {location.address}")
                    else:
                        print(f"[GPS] {now} -> Lat: {lat}, Lng: {lng} | Place: Not found")
                except Exception as e:
                    print(f"[ERROR] Failed to parse GPS data: {e}")
            else:
                print(f"[RECV] {incoming}")

    # -------------------------------
    # Eye Blink Detection
    # -------------------------------
    for face in faces:
        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)

        left_blink = blinked(landmarks[36], landmarks[37], 
                             landmarks[38], landmarks[41], 
                             landmarks[40], landmarks[39])
        right_blink = blinked(landmarks[42], landmarks[43], 
                              landmarks[44], landmarks[47], 
                              landmarks[46], landmarks[45])

        if left_blink == 0 or right_blink == 0:
            sleep += 1
            drowsy = 0
            active = 0
            if sleep > 6:
                status = "SLEEPING !!!"
                color = (0, 0, 255)
                if s:
                    s.write(b'a')
                    print("[SEND] Driver Sleep !!! (Alert Sent)")
                    # Log sleep event to database
                    database_handler.log_event(
                        event_type="Drowsiness Alert",
                        alert_type="Critical",
                        driver_status="Driver is sleeping",
                        coords=f"{lat}, {lng}" if 'lat' in locals() else "",
                        place=location.address if 'location' in locals() else ""
                    )
                time.sleep(2)

        elif left_blink == 1 or right_blink == 1:
            sleep = 0
            active = 0
            drowsy += 1
            if drowsy > 6:
                status = "Drowsy !"
                color = (0, 0, 255)
                if s:
                    s.write(b'a')
                    print("[SEND] Drowsy Alert !!! (Alert Sent)")
                    # Log drowsy event to database
                    database_handler.log_event(
                        event_type="Drowsiness Warning",
                        alert_type="Warning",
                        driver_status="Driver is drowsy",
                        coords=f"{lat}, {lng}" if 'lat' in locals() else "",
                        place=location.address if 'location' in locals() else ""
                    )
                time.sleep(2)

        else:
            drowsy = 0
            sleep = 0
            active += 1
            if active > 6:
                status = "Active :)"
                color = (0, 255, 0)
                if s:
                    s.write(b'b')
                    print("[SEND] All OK ! (Safe Driving)")
                    # Log normal status to database (less frequently to avoid flooding)
                    if active % 10 == 0:  # Log every 10th active state
                        database_handler.log_event(
                            event_type="Status Update",
                            alert_type="Info",
                            driver_status="Driver is alert and active",
                            coords=f"{lat}, {lng}" if 'lat' in locals() else "",
                            place=location.address if 'location' in locals() else ""
                        )
                time.sleep(2)

        # Show status on video
        cv2.putText(frame, status, (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    cv2.imshow("Driver Monitoring", frame)

    if cv2.waitKey(1) == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()

if s:
    s.close()
    print("[INFO] Serial connection closed.")

# Log application shutdown
database_handler.log_event(
    event_type="System",
    alert_type="Info",
    driver_status="Application shutdown"
)
