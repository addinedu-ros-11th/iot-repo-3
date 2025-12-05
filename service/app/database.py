# database.py
"""MySQL 데이터베이스 관리"""

import threading
import pymysql


class DatabaseHandler:
    """MySQL 데이터베이스 관리"""
    
    def __init__(self, host: str, user: str, password: str, database: str):
        self.config = {
            'host': host, 'user': user, 'password': password,
            'database': database, 'charset': 'utf8mb4'
        }
        self.conn = None
        self.lock = threading.Lock()
    
    def connect(self) -> bool:
        """DB 연결"""
        try:
            self.conn = pymysql.connect(**self.config)
            print(f"[✓] DB 연결 성공: {self.config['host']}/{self.config['database']}")
            return True
        except pymysql.Error as e:
            print(f"[✗] DB 연결 실패: {e}")
            return False
    
    def insert_log(self, device_id: str, data_type: str, metric_name: str, value: str) -> bool:
        """데이터 저장"""
        if not self.conn:
            print("[✗] DB 연결이 없습니다")
            return False
        
        try:
            with self.lock:
                with self.conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO logs (device_id, data_type, metric_name, value) VALUES (%s, %s, %s, %s)",
                        (device_id, data_type, metric_name, value)
                    )
                    self.conn.commit()
            print(f"[✓] DB 저장: {device_id},{data_type},{metric_name},{value}")
            return True
        except pymysql.Error as e:
            print(f"[✗] DB 저장 실패: {e}")
            self._reconnect()
            return False
    
    def _reconnect(self):
        """DB 재연결"""
        try:
            if self.conn:
                self.conn.ping()
        except:
            self.connect()
    
    def close(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()
            print("[○] DB 연결 종료")