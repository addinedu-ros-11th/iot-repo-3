import os
import sys
import time
import logging

import serial  # pip install pyserial
import pymysql  # pip install pymysql


# 기본 설정값 (필요하면 환경변수로 덮어쓰기)
SERIAL_PORT = os.environ.get("CURTAIN_SERIAL_PORT", "/dev/ttyACM0")
SERIAL_BAUDRATE = int(os.environ.get("CURTAIN_SERIAL_BAUD", "9600"))

DB_HOST = os.environ.get("CURTAIN_DB_HOST", "database-northpard.c9ygm4yuimcy.ap-northeast-2.rds.amazonaws.com")
DB_PORT = int(os.environ.get("CURTAIN_DB_PORT", "3306"))
DB_USER = os.environ.get("CURTAIN_DB_USER", "ioclean_user")
DB_PASSWORD = os.environ.get("CURTAIN_DB_PASSWORD", "CHANGE_ME")
DB_NAME = os.environ.get("CURTAIN_DB_NAME", "ioclean")


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
    """파싱 포맷: device_id,light_value,motor_direction,current_step,max_steps"""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 5:
        raise ValueError(f"Invalid log format (need 5 fields): {line!r}")

    device_id = parts[0]
    light_value = int(parts[1])
    motor_direction = int(parts[2])
    current_step = int(parts[3])
    max_steps = int(parts[4])

    return device_id, light_value, motor_direction, current_step, max_steps


def main():
    if DB_PASSWORD == "CHANGE_ME":
        logging.error("DB_PASSWORD is still 'CHANGE_ME'. Set CURTAIN_DB_PASSWORD env var before running.")
        sys.exit(1)

    ser = connect_serial()
    conn = connect_db()

    insert_sql = (
        "INSERT INTO curtain_log "
        "(device_id, light_value, motor_direction, current_step, max_steps) "
        "VALUES (%s, %s, %s, %s, %s)"
    )

    try:
        with conn.cursor() as cur:
            while True:
                try:
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode(errors="ignore").strip()
                    if not line:
                        continue

                    try:
                        device_id, light_value, motor_direction, current_step, max_steps = parse_log_line(line)
                    except ValueError as e:
                        logging.warning(f"Skip invalid line: {e}")
                        continue

                    cur.execute(
                        insert_sql,
                        (device_id, light_value, motor_direction, current_step, max_steps),
                    )
                    logging.info(
                        f"Inserted: device_id={device_id}, light={light_value}, dir={motor_direction}, "
                        f"step={current_step}/{max_steps}"
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
    main()
