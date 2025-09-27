# Driver Drowsiness Detection and Alarm
# Driver Drowsiness Detection and Alert System

A real-time driver monitoring system that detects drowsiness from a webcam feed, triggers alerts via an Arduino-based hardware module (buzzer, LEDs, vibration motor), logs events to MySQL, and reverse-geocodes GPS coordinates received from the Arduino GPS module.

This repository contains:
- Python application for face/eye landmark-based drowsiness detection.
- Arduino sketch for alerting and GPS reporting.
- MySQL logging module for event persistence.


## Features
- Eye Aspect Ratio-based blink/drowsiness detection using dlib 68-face-landmarks.
- Serial communication with Arduino to trigger alerts:
  - 'a' = Alert (sleep/drowsy)
  - 'b' = Safe mode
- GPS integration via Arduino (NEO-6M) and reverse geocoding in Python via Nominatim/Geopy.
- MySQL event logging for system and alert events with timestamps and optional location details.
- On-screen status overlay while monitoring.


## Project Structure
```
21-09-25/
├─ main.py                        # Main Python script (webcam + detection + serial + reverse geocode)
├─ database_handler.py           # MySQL database initialization and logging
├─ Arduino_IDE_code.ino          # Arduino sketch (LCD, buzzer, LEDs, vibration motor, GPS)
├─ shape_predictor_68_face_landmarks.dat # dlib landmark model (large file ~100MB)
└─ README.md                     # This file
```


## Prerequisites
- Windows (tested) with Python 3.8+ recommended
- Webcam
- Arduino (e.g., Uno/Nano)
- NEO-6M GPS module
- LCD 1602 with I2C backpack
- Buzzer, 2x LEDs (Red/Green), vibration motor (via transistor + diode), jumper wires
- MySQL Server running locally or remotely


## Python Dependencies
- opencv-python
- numpy
- dlib
- imutils
- pyserial
- geopy
- mysql-connector-python

Install from `requirements.txt`:
```
pip install -r requirements.txt
```

Note on dlib installation on Windows:
- Ensure you have Visual C++ Build Tools installed or use a prebuilt wheel compatible with your Python version.
- If `pip install dlib` fails, search for a prebuilt wheel (e.g., "dlib‑19.24.2‑cp39‑cp39‑win_amd64.whl") matching your Python.


## Database Setup
The Python app auto-creates the database and table if they do not exist.
- Default config is defined in `database_handler.py`:
```
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "driver_db"
}
```
- Update `user`, `password`, and `host` as needed for your environment.
- Table created: `events` with columns
  - ID, Event_type, Event_date, Event_time, Alert_type, Driver_status, Location_coords, Location_place, Notes


## Arduino Hardware Wiring (from `Arduino_IDE_code.ino`)
- Buzzer: D8
- Red LED: D9
- Green LED: D7
- Vibration Motor: D6 (through a transistor + flyback diode)
- LCD I2C: Address 0x27, SDA/SCL to Arduino I2C pins
- GPS NEO-6M via SoftwareSerial:
  - GPS TX -> Arduino D4
  - GPS RX -> Arduino D3

Baud rates:
- PC Serial: 9600
- GPS Serial: 9600


## Arduino Sketch Behavior
- Commands from PC (Python) over Serial:
  - 'a' => trigger alert sequence (buzzer + red LED + after 3s vibration; auto-off after 5s)
  - 'b' => set safe mode (green LED on; all alerts off)
- On alert, prints GPS data to Serial as:
  - `Lat: <lat>, Lng: <lng>` when a valid fix is present
  - `[GPS] No valid location yet...` otherwise

Load `Arduino_IDE_code.ino` onto your Arduino using the Arduino IDE.


## Python Application Behavior (from `main.py`)
- Auto-detects the first available COM port and connects at 9600 baud.
- Opens default camera (`cv2.VideoCapture(0)`).
- Loads `shape_predictor_68_face_landmarks.dat` for eye landmark detection.
- Maintains counters for `sleep`, `drowsy`, and `active` states.
- Status logic:
  - If eye ratio indicates closed eyes for >6 frames => `SLEEPING !!!` => send 'a' to Arduino; logs Critical event.
  - If borderline for >6 frames => `Drowsy !` => send 'a' to Arduino; logs Warning event.
  - If eyes normal for >6 frames => `Active :)` => send 'b' to Arduino; logs periodic Info status updates.
- Reads Arduino Serial lines. When a line contains `GPS Location` or `Lat:` format, attempts to parse latitude and longitude and reverse-geocode to an address using Geopy `Nominatim`.
- Logs events via `database_handler.log_event()` including coordinates/address if available.

Window controls:
- Press `ESC` to exit. The app will release the camera, close windows, close serial, and log a shutdown event.


## Running the System
1. Install Python dependencies:
```
pip install -r requirements.txt
```
2. Ensure MySQL is running and `database_handler.py` credentials are correct.
3. Flash `Arduino_IDE_code.ino` to Arduino. Keep the Arduino connected via USB.
4. Connect the GPS antenna outdoors or near a window for a fix.
5. Place `shape_predictor_68_face_landmarks.dat` in the same folder as the Python script (already present).
6. Run the Python script:
```
python main.py
```
7. Grant camera permissions if prompted and ensure the correct COM port is auto-detected. If not, edit the script to use the right port.


## Notes and Limitations
- The `shape_predictor_68_face_landmarks.dat` file is large (~100MB). Consider using Git LFS if pushing to GitHub, or provide a download link and add it to `.gitignore`.
- Reverse geocoding uses OpenStreetMap Nominatim via Geopy and requires internet connectivity. Nominatim has rate limits; excessive requests may be throttled.
- Lighting conditions and camera placement significantly affect detection accuracy.
- For multiple cameras or non-default camera index, update `cv2.VideoCapture(0)` accordingly.


## Troubleshooting
- Camera not opening: check another index (0/1/2), or ensure no other app is using the camera.
- dlib install fails: use compatible Python version and prebuilt wheel; ensure C++ Build Tools installed.
- Serial not connecting: ensure Arduino shows up in Device Manager and that no other Serial monitor is open.
- GPS shows no valid location: move to open sky and wait for a fix; ensure GPS wiring and power are correct.
- MySQL errors: verify credentials and that MySQL service is running; test with a simple client.


## Security
- Do not commit real database passwords to public repos. Consider using environment variables or a config file ignored by Git. For now, credentials are in `database_handler.py` for simplicity.


## License
MIT License (update if different).


## Acknowledgments
- dlib and the 68-point facial landmark predictor.
- OpenCV, imutils.
- Geopy + OpenStreetMap Nominatim.
- Arduino community libraries: TinyGPS++, LiquidCrystal_I2C.



