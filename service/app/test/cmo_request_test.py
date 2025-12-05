import time
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CMORequest:
    """CMO 요청 데이터 클래스"""
    device_id: str
    metric_name: str
    value: str
    timestamp: float
    timeout: float = 5.0
    
    def is_expired(self):
        """요청이 만료되었는지 확인"""
        return time.time() - self.timestamp > self.timeout

    def get_elapsed_time(self):
        """경과 시간 반환 (초 단위)"""
        return time.time() - self.timestamp
    
    def get_remaining_time(self):
        """남은 시간 반환 (초 단위)"""
        remaining = self.timeout - self.get_elapsed_time()
        return max(0, remaining)

# ============================================================
# 방법 1: 간단한 테스트
# ============================================================
def test_timeout_simple():
    """간단한 타임아웃 테스트"""
    print("=" * 60)
    print("방법 1: 간단한 타임아웃 테스트")
    print("=" * 60)
    
    # 타임아웃 2초로 설정
    request = CMORequest(
        device_id="ele_01",
        metric_name="ele",
        value="1.0",
        timestamp=time.time(),
        timeout=2.0
    )
    
    print(f"요청 생성: {request.device_id}")
    print(f"타임아웃 설정: {request.timeout}초\n")
    
    for i in range(4):
        elapsed = request.get_elapsed_time()
        remaining = request.get_remaining_time()
        is_expired = request.is_expired()
        
        status = "❌ 만료됨" if is_expired else "✓ 대기 중"
        print(f"[{i}초] 경과: {elapsed:.1f}초 | 남은시간: {remaining:.1f}초 | {status}")
        
        time.sleep(1)


# ============================================================
# 방법 2: 시각적 프로그래스바
# ============================================================
def test_timeout_progressbar():
    """프로그래스바로 시각적 타임아웃 표시"""
    print("\n" + "=" * 60)
    print("방법 2: 프로그래스바 테스트")
    print("=" * 60)
    
    request = CMORequest(
        device_id="ele_01",
        metric_name="ele",
        value="1.0",
        timestamp=time.time(),
        timeout=5.0
    )
    
    print(f"요청 생성: {request.device_id}")
    print(f"타임아웃 설정: {request.timeout}초\n")
    
    while not request.is_expired():
        elapsed = request.get_elapsed_time()
        remaining = request.get_remaining_time()
        percentage = (elapsed / request.timeout) * 100
        
        # 프로그래스바 생성
        bar_length = 30
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        print(f"\r[{bar}] {percentage:.0f}% ({elapsed:.1f}/{request.timeout}s)", end="", flush=True)
        time.sleep(0.5)
    
    print(f"\r[{'█' * 30}] 100% - 타임아웃됨!")


# ============================================================
# 방법 3: 큐에 요청 추가하고 타임아웃 확인
# ============================================================
def test_timeout_with_queue():
    """큐 기반 타임아웃 테스트"""
    print("\n" + "=" * 60)
    print("방법 3: 큐 기반 타임아웃 테스트")
    print("=" * 60)
    
    from queue import Queue
    
    test_queue = Queue()
    
    # 다양한 타임아웃을 가진 요청들 생성
    requests = [
        CMORequest("ele_01", "ele", "1.0", time.time(), timeout=3.0),
        CMORequest("ent_01", "ent", "1.0", time.time(), timeout=2.0),
        CMORequest("cur_01", "cur", "1.0", time.time(), timeout=1.0),
    ]
    
    for req in requests:
        test_queue.put(req)
        print(f"요청 추가: {req.device_id} (타임아웃: {req.timeout}초)")
    
    print("\n처리 시작...\n")
    start_time = time.time()
    
    while not test_queue.empty() or (time.time() - start_time) < 5:
        if not test_queue.empty():
            request = test_queue.get()
            
            if request.is_expired():
                print(f"[TIMEOUT] {request.device_id} - 만료됨 (경과시간: {request.get_elapsed_time():.1f}초)")
            else:
                print(f"[PROCESSING] {request.device_id} - 처리 중 (경과시간: {request.get_elapsed_time():.1f}초)")
                # 1초 대기
                time.sleep(1)
                # 다시 확인
                if request.is_expired():
                    print(f"  → 이후 만료됨 (최종 경과시간: {request.get_elapsed_time():.1f}초)")
                else:
                    print(f"  → 아직 유효함 (남은시간: {request.get_remaining_time():.1f}초)")


# ============================================================
# 방법 4: 실시간 모니터링 (실제 환경 시뮬레이션)
# ============================================================
def test_timeout_monitoring():
    """실제 환경과 유사한 타임아웃 모니터링"""
    print("\n" + "=" * 60)
    print("방법 4: 실시간 모니터링")
    print("=" * 60)
    
    from queue import Queue
    
    cmd_queue = Queue()
    
    # 테스트 데이터
    test_data = [
        ("ele_01", "ele", "1.0", 0),      # 즉시 전송
        ("ent_01", "ent", "1.0", 1),      # 1초 후 전송
        ("cur_01", "cur", "1.0", 3),      # 3초 후 전송
        ("dht_01", "dht", "1.0", 6),      # 6초 후 전송 (타임아웃 설정)
    ]
    
    def add_requests():
        """요청 추가 시뮬레이션"""
        for device_id, metric_name, value, delay in test_data:
            time.sleep(delay)
            request = CMORequest(
                device_id=device_id,
                metric_name=metric_name,
                value=value,
                timestamp=time.time(),
                timeout=3.0
            )
            cmd_queue.put(request)
            print(f"  [+ 요청 추가] {device_id} (타임아웃: {request.timeout}초)")
    
    # 요청 추가 스레드
    import threading
    add_thread = threading.Thread(target=add_requests, daemon=True)
    add_thread.start()
    
    print("요청 수신 중...\n")
    print("[모니터링 시작]\n")
    
    start_time = time.time()
    processed = 0
    timeout_count = 0
    
    while (time.time() - start_time) < 10:
        if not cmd_queue.empty():
            request = cmd_queue.get()
            
            print(f"시간: {time.time() - start_time:.1f}s | ", end="")
            
            if request.is_expired():
                print(f"❌ TIMEOUT: {request.device_id} (경과: {request.get_elapsed_time():.1f}s)")
                timeout_count += 1
            else:
                print(f"✓ PROCESS: {request.device_id} (남은: {request.get_remaining_time():.1f}s)")
                processed += 1
        
        time.sleep(0.1)
    
    add_thread.join(timeout=1)
    
    print(f"\n[결과]\n처리됨: {processed}개 | 타임아웃: {timeout_count}개")


# ============================================================
# 실행
# ============================================================
if __name__ == "__main__":
    test_timeout_simple()
    test_timeout_progressbar()
    test_timeout_with_queue()
    test_timeout_monitoring()