# queue_processor.py
"""CMD 큐 처리 및 CMO 전송"""

from typing import Dict
from queue import Queue, Empty

from models import CMORequest


class QueueProcessor:
    """CMO 큐 처리 및 전송, ACK 대기"""
    
    def __init__(self, cmd_queue: Queue, monitors: Dict[str, object]):
        self.cmd_queue = cmd_queue
        self.monitors = monitors  # device_id -> SerialMonitor
        self.running = False
        self.pending_requests = {}  # device_id:metric_name -> CMORequest (전송 대기 중)
    
    def run(self):
        """큐 처리"""
        self.running = True
        
        while self.running:
            try:
                cmo = self.cmd_queue.get(timeout=1)
                self._process_cmo(cmo)
            
            except Empty:
                # 타임아웃 확인
                self._check_pending_timeouts()
                continue
            except Exception as e:
                print(f"[ERROR] 큐 처리 오류: {e}")
    
    def _process_cmo(self, cmo: CMORequest):
        """
        4. CMO 명령 전송
        """
        target_device_id = cmo.device_id
        
        if target_device_id not in self.monitors:
            print(f"[ERROR] device_id '{target_device_id}'에 대한 모니터가 없음")
            return
        
        # 명령 전송
        monitor = self.monitors[target_device_id]
        if monitor.send_command(cmo.command):
            # 전송 성공 -> pending 목록에 추가 (ACK 대기)
            key = f"{target_device_id}:{cmo.metric_name}"
            self.pending_requests[key] = cmo
            print(f"[SEND] CMO 전송: {cmo.command}")
        else:
            print(f"[ERROR] CMO 전송 실패: {cmo.command}")
    
    def _check_pending_timeouts(self):
        """
        5. 타임아웃 확인 - ACK가 없으면 삭제 및 에러 로그
        """
        expired_keys = []
        
        for key, cmo in self.pending_requests.items():
            if cmo.is_expired():
                expired_keys.append(key)
                device_id = cmo.device_id
                metric_name = cmo.metric_name
                print(f"[TIMEOUT] ACK 응답 없음: {device_id},{metric_name} (경과: {cmo.elapsed_time():.1f}초)")
        
        # 만료된 요청 제거
        for key in expired_keys:
            del self.pending_requests[key]
    
    def handle_ack(self, device_id: str, metric_name: str):
        """
        ACK 수신 시 호출 - pending 목록에서 제거
        """
        key = f"{device_id}:{metric_name}"
        
        if key in self.pending_requests:
            cmo = self.pending_requests[key]
            elapsed = cmo.elapsed_time()
            del self.pending_requests[key]
            print(f"[ACK] 응답 수신: {device_id},{metric_name} (응답시간: {elapsed:.1f}초)")
        else:
            print(f"[WARNING] 예상하지 못한 ACK: {device_id},{metric_name}")
    
    def stop(self):
        """처리 중지"""
        self.running = False