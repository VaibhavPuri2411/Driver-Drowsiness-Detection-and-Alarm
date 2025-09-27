import mysql.connector
from datetime import datetime

# -------------------------------
# MySQL Configuration
# -------------------------------
DB_CONFIG = {
    "host": "localhost",         # 🔹 Change if using remote server
    "user": "root",              # 🔹 Your MySQL username
    "password": "root", # 🔹 Your MySQL password
    "database": "driver_db"      # 🔹 Database name
}

DB_NAME = "driver_db"
TABLE_NAME = "events"

# -------------------------------
# Setup Database and Table
# -------------------------------
def init_db():
    try:
        # Connect without selecting DB (to ensure DB exists first)
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        conn.commit()
        cursor.close()
        conn.close()

        # Now connect to the created database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Event_type VARCHAR(50),
            Event_date DATE,
            Event_time TIME,
            Alert_type VARCHAR(50),
            Driver_status VARCHAR(100),
            Location_coords VARCHAR(100),
            Location_place TEXT,
            Notes TEXT
        )
        """)
        conn.commit()
        print(f"[INFO] Database `{DB_NAME}` and table `{TABLE_NAME}` ensured.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")

# -------------------------------
# Insert Event into Table
# -------------------------------
def log_event(event_type, alert_type, driver_status, coords="", place="", notes=""):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        now = datetime.now()
        event_date = now.strftime("%Y-%m-%d")
        event_time = now.strftime("%H:%M:%S")

        cursor.execute(f"""
            INSERT INTO {TABLE_NAME}
            (Event_type, Event_date, Event_time, Alert_type, Driver_status, Location_coords, Location_place, Notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (event_type, event_date, event_time, alert_type, driver_status, coords, place, notes))

        conn.commit()
        print(f"[DB] Logged event: {event_type} | {driver_status}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to insert into DB: {e}")
