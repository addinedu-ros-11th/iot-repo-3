import os
import sys
import time
import logging

import serial
import pymysql

import dotenv

dotenv.load_dotenv()

SERIAL_PORT = os.getenv("SERIAL_PORT")
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUD"))

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)


def connect_serial():
    while True:
        try:
            logging.info(f"Trying to open serial port {SERIAL_PORT} @ {SERIAL_BAUDRATE} baud")
            ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1)
            logging.info("Serial port opened")
            return ser
        except serial.SerialException as e:
            logging.error(f"Serial open failed: {e}. Retry in 5s...")
            time.sleep(5)


def connect_db():
    while True:
        try:
            logging.info(f"Connecting to MySQL {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                charset="utf8mb4",
                autocommit=True,
            )
            logging.info("MySQL connected")
            return conn
        except pymysql.MySQLError as e:
            logging.error(f"MySQL connection failed: {e}. Retry in 5s...")
            time.sleep(5)


def parse_log_line(line: str):
    """파싱 포맷: event_type,device_id,uid
    event_type: OPENED, VALID, FAILED"""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 3:
        raise ValueError(f"Invalid log format (need 3 fields): {line!r}")

    event_type = parts[0].upper()
    device_id = parts[1]
    uid = parts[2]
    
    # 유효한 event_type 검증
    valid_types = ["OPENED", "VALID", "FAILED"]
    if event_type not in valid_types:
        raise ValueError(f"Invalid event_type '{event_type}'. Must be one of {valid_types}")

    return event_type, device_id, uid


def entrance_log_main():
    if DB_PASSWORD == "CHANGE_ME":
        logging.error("DB_PASSWORD is still 'CHANGE_ME'. Set DB_PASSWORD env var before running.")
        sys.exit(1)

    ser = connect_serial()
    conn = connect_db()

    insert_sql = (
        "INSERT INTO entrance_log "
        "(event_type, device_id, card_uid) "
        "VALUES (%s, %s, %s)"
    )

    try:
        with conn.cursor() as cur:
            while True:
                try:
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode(errors="ignore").strip()
                    if not line or line.startswith("[DEBUG]"):
                        continue

                    try:
                        event_type, device_id, uid = parse_log_line(line)
                    except ValueError as e:
                        logging.warning(f"Skip invalid line: {e}")
                        continue

                    cur.execute(
                        insert_sql,
                        (event_type, device_id, uid),
                    )
                    logging.info(
                        f"Inserted: event_type={event_type}, device_id={device_id}, uid={uid}"
                    )

                except serial.SerialException as e:
                    logging.error(f"Serial error: {e}. Reconnecting...")
                    ser.close()
                    ser = connect_serial()

                except pymysql.MySQLError as e:
                    logging.error(f"MySQL error: {e}. Reconnecting DB...")
                    conn.close()
                    conn = connect_db()
                    cur = conn.cursor()

    finally:
        try:
            ser.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    entrance_log_main()