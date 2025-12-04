# monitor.py
"""단일 포트 시리얼 모니터"""

import serial
from queue import Queue
from datetime import datetime

from models import CMORequest
from parser import SerialParser
from database import DatabaseHandler


class SerialMonitor:
    """단일 포트 모니터"""
    
    def __init__(self, device_id: str, port: str, cmd_queue: Queue,
                 db_handler: DatabaseHandler, baudrate: int = 9600):
        self.device_id = device_id
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.cmd_queue = cmd_queue
        self.db_handler = db_handler
        self.available_devices = []  # app.py에서 할당됨
        self.queue_processor = None  # app.py에서 할당됨 (ACK 처리)
    
    @staticmethod
    def find_target_device(metric_name: str, available_devices: list):
        """metric_name으로 대상 device_id 찾기"""
        if metric_name == "FLOOR":
            prefix = "ele" + "_"
            
            for device_id in available_devices:
                if device_id.startswith(prefix):
                    return device_id
        
        return None
    
    def connect(self) -> bool:
        """포트 연결"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            print(f"[✓] {self.port} 연결 성공")
            return True
        except serial.SerialException as e:
            print(f"[✗] {self.port} 연결 실패: {e}")
            return False
    
    def run(self):
        """데이터 수신 및 처리"""
        while self.running:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if not line:
                        continue
                    
                    self._log_received(line)
                    self._process_data(line)
            
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"[ERROR] {self.port} 오류: {e}")
    
    def _process_data(self, line: str):
        """수신 데이터 처리"""
        parsed = SerialParser.parse(line, self.device_id)
        if not parsed:
            return
        
        if hasattr(self, 'system_state') and self.system_state:
            self.system_state.update(
                parsed.device_id,
                parsed.data_type,
                parsed.metric_name,
                parsed.value
        )
        
        if parsed.data_type == 'CMD':
            self._handle_cmd(parsed)
        
        elif parsed.data_type == 'SEN':
            self._handle_sen(parsed)
        
        elif parsed.data_type == 'ACK':
            self._handle_ack(parsed)
    
    def _handle_cmd(self, parsed):
        """CMD 처리 - metric_name으로 target device 찾음"""
        # 1. metric_name에 해당하는 device_id 찾기
        target_device_id = self.find_target_device(parsed.metric_name, self.available_devices)
        
        if not target_device_id:
            print(f"[ERROR] metric_name '{parsed.metric_name}'에 해당하는 device를 찾을 수 없음")
            return
        
        # 2. CMO 명령 생성
        cmo_command = f"CMO,{parsed.metric_name},{parsed.value}"
        
        # 3. CMORequest 생성 및 큐에 추가
        cmo = CMORequest(
            device_id=target_device_id,
            metric_name=parsed.metric_name,
            value=parsed.value,
            command=cmo_command
        )
        self.cmd_queue.put(cmo)
        print(f"[QUEUE] CMO 큐에 추가: {target_device_id} (요청자: {self.device_id})")
    
    def _handle_sen(self, parsed):
        """센서 데이터 처리"""
        self.db_handler.insert_log(parsed.device_id, parsed.data_type,
                                  parsed.metric_name, parsed.value)
    
    def _handle_ack(self, parsed):
        """ACK 응답 처리"""
        print(f"[ACK] {parsed.device_id} 응답 수신 - {parsed.metric_name}")
        
        # queue_processor에 ACK 처리 요청
        if self.queue_processor:
            self.queue_processor.handle_ack(parsed.device_id, parsed.metric_name)
    
    def _log_received(self, data: str):
        """수신 로그"""
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{ts}] [{self.port}] 수신: {data}")
    
    def send_command(self, command: str) -> bool:
        """명령 전송"""
        if not self.ser or not self.ser.is_open:
            return False
        
        try:
            self.ser.write(f"{command}\n".encode('utf-8'))
            print(f"[SEND] [{self.port}] {command}")
            return True
        except Exception as e:
            print(f"[ERROR] {self.port} 전송 실패: {e}")
            return False
    
    def close(self):
        """연결 종료"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[○] {self.port} 연결 종료")