import os
import sys
import time
import logging
from datetime import datetime

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
    try_count = 0  # 재시도 횟수 추가
    while try_count < 5:  # 최대 5번 재시도
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
            try_count += 1
    logging.error("MySQL connection failed after 5 retries. Exiting...")
    sys.exit(1)


def parse_log_line(line: str):
    """파싱 포맷: device_id, temperature, humidity"""
    # 온도와 습도를 파싱할 수 있도록 수정
    if '온도' in line:
        # 온도 파싱: "온도:25.3°C"
        temperature = float(line.split(":")[1].replace('°C', '').strip())
        return None, temperature, None  # 온도만 추출해서 반환
    elif '습도' in line:
        # 습도 파싱: "습도:17%"
        humidity = int(line.split(":")[1].replace('%', '').strip())
        return None, None, humidity  # 습도만 추출해서 반환
    elif 'DHT' in line:
        # device_id는 "DHT-01"과 같은 형식
        device_id = line.strip()
        return device_id, None, None  # device_id만 추출해서 반환
    else:
        raise ValueError(f"Invalid log format (need 3 fields): {line!r}")

def main():
    if DB_PASSWORD == "CHANGE_ME":
        logging.error("DB_PASSWORD is still 'CHANGE_ME'. Set CURTAIN_DB_PASSWORD env var before running.")
        sys.exit(1)

    ser = connect_serial()
    conn = connect_db()

    insert_sql = (
        "INSERT INTO DHT11_log "
        "(device_id, temperature, humidity, created_at) "
        "VALUES (%s, %s, %s, %s)"
    )

    try:
        device_id = None
        temperature = None
        humidity = None

        with conn.cursor() as cur:
            while True:
                try:
                    raw = ser.readline()
                    if not raw:
                        continue

                    line = raw.decode(errors="ignore").strip()
                    if not line:
                        continue

                    logging.info(f"Received raw data: {line}")  # 데이터 읽기 확인용

                    try:
                        new_device_id, new_temperature, new_humidity = parse_log_line(line)

                        # 각각의 값이 존재하면 누적하여 저장
                        if new_device_id:
                            device_id = new_device_id
                        if new_temperature:
                            temperature = new_temperature
                        if new_humidity:
                            humidity = new_humidity

                        # device_id, temperature, humidity가 모두 채워졌을 때만 데이터 삽입
                        if device_id and temperature is not None and humidity is not None:
                            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            logging.info(f"Inserting into DB: device_id={device_id}, temp={temperature}, hum={humidity}, created_at={created_at}")
                            cur.execute(insert_sql, (device_id, temperature, humidity, created_at))
                            conn.commit()  # 커밋을 통해 DB에 반영
                            logging.info(f"Inserted data for device {device_id}")
                            # 삽입 후 값 초기화 (다음 값을 받을 준비)
                            device_id, temperature, humidity = None, None, None  

                    except ValueError as e:
                        logging.warning(f"Skip invalid line: {e}")
                        continue

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
