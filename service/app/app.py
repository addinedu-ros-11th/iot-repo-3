# app.py
"""시리얼 모니터 애플리케이션"""

import threading
import time
from typing import Dict
from queue import Queue
from flask import Flask, jsonify, request

from database import DatabaseHandler
from monitor import SerialMonitor
from queue_processor import QueueProcessor


class SystemState:
    """시스템 상태 관리"""
    
    def __init__(self):
        self.device_id = ''
        self.data_type = ''
        self.metric_name = ''
        self.value = ''
        self.lock = threading.Lock()

    def update(self, device_id:str, data_type: str, metric_name: str, value: str):
        """상태 업데이트 """
        with self.lock:
            self.device_id = device_id
            self.data_type = data_type
            self.metric_name = metric_name
            self.value = value

    def to_dict(self):
        """딕셔너리로 반환 """
        with self.lock:
            return {
                'device_id': self.device_id,
                'data_type': self.data_type,
                'metric_name': self.metric_name,
                'value': self.value
            }


class SerialMonitorApp:
    """시리얼 모니터 애플리케이션"""
    
    def __init__(self, db_config: dict, port_config: dict):
        self.db_handler = DatabaseHandler(**db_config)
        self.port_config = port_config
        self.cmd_queue = Queue()
        self.monitors: Dict[str, SerialMonitor] = {}
        self.threads = []
        self.queue_processor = None
        
        # 시스템 상태
        self.system_state = SystemState()
        
        # Flask 앱 생성
        self.flask_app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """REST API 라우트 설정"""
        
        @self.flask_app.route('/api/state', methods=['GET'])
        def get_state():
            """현재 시스템 상태 조회"""
            return jsonify(self.system_state.to_dict())
        
        @self.flask_app.route('/api/command', methods=['POST'])
        def send_command():
            """명령 전송
            
            요청 형식:
            {
                "device_id": "ele_001",  # 대상 디바이스
                "metric_name": "FLOOR",  # 명령 종류
                "value": "1"             # 값
            }
            """
            try:
                data = request.json
                device_id = data.get('device_id')
                metric_name = data.get('metric_name')
                value = data.get('value')
                
                if not all([device_id, metric_name, value]):
                    return jsonify({
                        'success': False,
                        'error': 'Missing parameters: device_id, metric_name, value'
                    }), 400
                
                if device_id not in self.monitors:
                    return jsonify({
                        'success': False,
                        'error': f'Device "{device_id}" not found'
                    }), 404
                
                # CMO 명령 생성
                command = f"CMO,{metric_name},{value}"
                
                # 디바이스로 전송
                monitor = self.monitors[device_id]
                success = monitor.send_command(command)
                
                return jsonify({
                    'success': success,
                    'device_id': device_id,
                    'command': command
                })
            
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.flask_app.route('/api/health', methods=['GET'])
        def health_check():
            """헬스 체크"""
            return jsonify({
                'status': 'ok',
                'devices': len(self.monitors),
                'queue_size': self.cmd_queue.qsize()
            })
    
    def start(self) -> bool:
        """애플리케이션 시작"""
        print("=" * 60)
        print("시리얼 모니터 시작")
        print("=" * 60)
        
        # DB 연결
        if not self.db_handler.connect():
            return False
        
        # 포트 연결
        self._setup_monitors()
        if not self.monitors:
            print("[✗] 연결된 포트가 없습니다")
            self.db_handler.close()
            return False
        
        # 모니터 스레드 시작
        self._start_monitor_threads()
        
        # 큐 처리 스레드 시작
        self._start_queue_processor()
        
        # Flask API 서버 시작
        self._start_flask_server()
        
        print(f"\n[✓] {len(self.monitors)}개 포트 모니터링 중")
        print("[✓] REST API 서버 실행 중 (http://localhost:5000)\n")
        return True
    
    def _setup_monitors(self):
        """모니터 설정"""
        for device_id, port in self.port_config.items():
            monitor = SerialMonitor(device_id, port, self.cmd_queue, self.db_handler)
            monitor.available_devices = list(self.port_config.keys())
            monitor.system_state = self.system_state  # 상태 관리 객체 할당
            if monitor.connect():
                self.monitors[device_id] = monitor
    
    def _start_monitor_threads(self):
        """모니터 스레드 시작"""
        for device_id, monitor in self.monitors.items():
            thread = threading.Thread(
                target=monitor.run,
                daemon=True,
                name=f"Monitor-{device_id}"
            )
            thread.start()
            self.threads.append(thread)
    
    def _start_queue_processor(self):
        """큐 처리 스레드 시작"""
        self.queue_processor = QueueProcessor(self.cmd_queue, self.monitors)
        
        for monitor in self.monitors.values():
            monitor.queue_processor = self.queue_processor
        
        thread = threading.Thread(
            target=self.queue_processor.run,
            daemon=True,
            name="QueueProcessor"
        )
        thread.start()
        self.threads.append(thread)
    
    def _start_flask_server(self):
        """Flask API 서버 시작"""
        flask_thread = threading.Thread(
            target=self._run_flask,
            daemon=True,
            name="FlaskServer"
        )
        flask_thread.start()
        self.threads.append(flask_thread)
        time.sleep(0.5)
    
    def _run_flask(self):
        """Flask 서버 실행"""
        self.flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    def stop(self):
        """애플리케이션 종료"""
        print("\n" + "=" * 60)
        print("종료 중...")
        print("=" * 60)
        
        if self.queue_processor:
            self.queue_processor.stop()
        
        for monitor in self.monitors.values():
            monitor.close()
        
        self.db_handler.close()
        
        for thread in self.threads:
            thread.join(timeout=1)
        
        print("[✓] 모든 리소스 종료 완료")
    
    def run(self):
        """메인 루프"""
        if not self.start():
            return
        
        try:
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nCtrl+C로 종료...")
        
        finally:
            self.stop()