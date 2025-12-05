# test_app.py
"""시리얼 모니터 통합 테스트"""

import time
import threading
from queue import Queue
from unittest.mock import Mock, MagicMock, patch

from models import CMORequest, SerialData
from parser import SerialParser
from monitor import SerialMonitor
from queue_processor import QueueProcessor
from database import DatabaseHandler


class MockSerialPort:
    """시리얼 포트 Mock"""
    
    def __init__(self):
        self.is_open = True
        self.data_to_read = []
        self.sent_data = []
        self.in_waiting = 0
    
    def readline(self):
        if self.data_to_read:
            return self.data_to_read.pop(0).encode('utf-8')
        return b''
    
    def write(self, data):
        self.sent_data.append(data.decode('utf-8'))
    
    def close(self):
        self.is_open = False


def test_parser():
    """파서 테스트"""
    print("\n[TEST 1] 파서 테스트")
    print("=" * 60)
    
    # SEN 파싱
    result = SerialParser.parse("SEN,temperature,25.5", "sensor_001")
    assert result.data_type == "SEN"
    assert result.metric_name == "temperature"
    assert result.value == "25.5"
    print("✓ SEN 파싱 성공")
    
    # CMD 파싱
    result = SerialParser.parse("CMD,ele,ON", "controller_001")
    assert result.data_type == "CMD"
    assert result.metric_name == "ele"
    assert result.value == "ON"
    print("✓ CMD 파싱 성공")
    
    # 잘못된 형식
    result = SerialParser.parse("INVALID,data", "device_001")
    assert result is None
    print("✓ 잘못된 형식 감지 성공")


def test_find_target_device():
    """대상 device 찾기 테스트"""
    print("\n[TEST 2] 대상 device 찾기 테스트")
    print("=" * 60)
    
    available_devices = ["ele_001", "ele_002", "ent_001", "pump_001"]
    
    # ele로 시작하는 device 찾기
    result = SerialMonitor.find_target_device("ele", available_devices)
    assert result in ["ele_001", "ele_002"]
    print(f"✓ metric_name 'ele' → device '{result}' 찾음")
    
    # ent로 시작하는 device 찾기
    result = SerialMonitor.find_target_device("ent", available_devices)
    assert result == "ent_001"
    print(f"✓ metric_name 'ent' → device '{result}' 찾음")
    
    # 없는 device
    result = SerialMonitor.find_target_device("hvac", available_devices)
    assert result is None
    print("✓ 없는 device는 None 반환")


def test_cmo_request_timeout():
    """CMORequest 타임아웃 테스트"""
    print("\n[TEST 3] CMORequest 타임아웃 테스트")
    print("=" * 60)
    
    cmo = CMORequest(
        device_id="ele_001",
        metric_name="ele",
        value="ON",
        command="ele_001,CMO,ele,ON",
        timeout=0.5  # 0.5초 타임아웃
    )
    
    assert not cmo.is_expired()
    print(f"✓ 즉시 생성: 만료되지 않음 (경과: {cmo.elapsed_time():.2f}초)")
    
    time.sleep(0.6)
    assert cmo.is_expired()
    print(f"✓ 0.6초 후: 만료됨 (경과: {cmo.elapsed_time():.2f}초)")


def test_queue_processor_pending():
    """QueueProcessor pending 요청 테스트"""
    print("\n[TEST 4] QueueProcessor pending 요청 테스트")
    print("=" * 60)
    
    cmd_queue = Queue()
    monitors = {}
    
    # Mock monitor 생성
    mock_monitor = Mock()
    mock_monitor.send_command.return_value = True
    monitors["ele_001"] = mock_monitor
    
    processor = QueueProcessor(cmd_queue, monitors)
    
    # CMO 요청 처리
    cmo = CMORequest(
        device_id="ele_001",
        metric_name="ele",
        value="ON",
        command="ele_001,CMO,ele,ON",
        timeout=2.0
    )
    processor._process_cmo(cmo)
    
    # pending_requests에 추가되었는지 확인
    assert "ele_001:ele" in processor.pending_requests
    print("✓ CMO 요청이 pending_requests에 추가됨")
    
    # send_command 호출 확인
    mock_monitor.send_command.assert_called_with("ele_001,CMO,ele,ON")
    print("✓ send_command가 호출됨")


def test_queue_processor_ack_handling():
    """QueueProcessor ACK 처리 테스트"""
    print("\n[TEST 5] QueueProcessor ACK 처리 테스트")
    print("=" * 60)
    
    cmd_queue = Queue()
    monitors = {}
    mock_monitor = Mock()
    monitors["ele_001"] = mock_monitor
    
    processor = QueueProcessor(cmd_queue, monitors)
    
    # CMO 요청 추가
    cmo = CMORequest(
        device_id="ele_001",
        metric_name="ele",
        value="ON",
        command="ele_001,CMO,ele,ON",
        timeout=2.0
    )
    processor._process_cmo(cmo)
    
    print(f"✓ pending 요청 개수: {len(processor.pending_requests)}")
    
    # ACK 수신
    processor.handle_ack("ele_001", "ele")
    
    # pending_requests에서 제거되었는지 확인
    assert "ele_001:ele" not in processor.pending_requests
    print("✓ ACK 수신 후 pending_requests에서 제거됨")


def test_queue_processor_timeout():
    """QueueProcessor 타임아웃 테스트"""
    print("\n[TEST 6] QueueProcessor 타임아웃 처리 테스트")
    print("=" * 60)
    
    cmd_queue = Queue()
    monitors = {}
    mock_monitor = Mock()
    monitors["ele_001"] = mock_monitor
    
    processor = QueueProcessor(cmd_queue, monitors)
    
    # 짧은 타임아웃으로 CMO 요청
    cmo = CMORequest(
        device_id="ele_001",
        metric_name="ele",
        value="ON",
        command="ele_001,CMO,ele,ON",
        timeout=0.3  # 0.3초
    )
    processor._process_cmo(cmo)
    
    print(f"✓ pending 요청 개수: {len(processor.pending_requests)}")
    
    # 타임아웃 대기
    time.sleep(0.4)
    
    # 타임아웃 확인
    processor._check_pending_timeouts()
    
    # pending_requests에서 제거되었는지 확인
    assert "ele_001:ele" not in processor.pending_requests
    print("✓ 타임아웃 후 pending_requests에서 자동 제거됨")


def test_serial_monitor_cmd_handling():
    """SerialMonitor CMD 처리 테스트"""
    print("\n[TEST 7] SerialMonitor CMD 처리 테스트")
    print("=" * 60)
    
    cmd_queue = Queue()
    db_handler = Mock(spec=DatabaseHandler)
    
    monitor = SerialMonitor("controller_001", "/dev/ttyUSB0", cmd_queue, db_handler)
    monitor.available_devices = ["ele_001", "ele_002", "ent_001"]
    
    # CMD 데이터 처리
    parsed = SerialData("controller_001", "CMD", "ele", "ON")
    monitor._handle_cmd(parsed)
    
    # 큐에 CMORequest가 추가되었는지 확인
    assert not cmd_queue.empty()
    cmo = cmd_queue.get()
    
    assert isinstance(cmo, CMORequest)
    assert cmo.device_id == "ele_001"  # 첫 번째 ele_*
    assert cmo.metric_name == "ele"
    assert cmo.value == "ON"
    print(f"✓ CMD 처리 완료: {cmo.command}")


def test_serial_monitor_sen_handling():
    """SerialMonitor SEN 처리 테스트"""
    print("\n[TEST 8] SerialMonitor SEN 처리 테스트")
    print("=" * 60)
    
    cmd_queue = Queue()
    db_handler = Mock(spec=DatabaseHandler)
    db_handler.insert_log.return_value = True
    
    monitor = SerialMonitor("sensor_001", "/dev/ttyUSB1", cmd_queue, db_handler)
    
    # SEN 데이터 처리
    parsed = SerialData("sensor_001", "SEN", "temperature", "25.5")
    monitor._handle_sen(parsed)
    
    # DB에 저장되었는지 확인
    db_handler.insert_log.assert_called_with("sensor_001", "SEN", "temperature", "25.5")
    print("✓ SEN 데이터 DB 저장 완료")


def test_end_to_end_flow():
    """엔드-투-엔드 흐름 테스트"""
    print("\n[TEST 9] 엔드-투-엔드 흐름 테스트")
    print("=" * 60)
    
    cmd_queue = Queue()
    db_handler = Mock(spec=DatabaseHandler)
    
    # Monitor 생성
    monitor_controller = SerialMonitor("controller_001", "/dev/ttyUSB0", cmd_queue, db_handler)
    monitor_ele = SerialMonitor("ele_001", "/dev/ttyUSB1", cmd_queue, db_handler)
    
    monitors = {"controller_001": monitor_controller, "ele_001": monitor_ele}
    monitor_controller.available_devices = list(monitors.keys())
    monitor_ele.available_devices = list(monitors.keys())
    
    # Mock send_command
    monitor_ele.send_command = Mock(return_value=True)
    
    # QueueProcessor 생성
    processor = QueueProcessor(cmd_queue, monitors)
    monitor_controller.queue_processor = processor
    monitor_ele.queue_processor = processor
    
    print("1️⃣ controller_001에서 CMD 수신")
    parsed = SerialData("controller_001", "CMD", "ele", "ON")
    monitor_controller._handle_cmd(parsed)
    
    print("2️⃣ CMO 요청을 큐에서 꺼내 처리")
    cmo = cmd_queue.get(timeout=1)
    processor._process_cmo(cmo)
    
    print("3️⃣ ele_001로 CMO 명령 전송 확인")
    monitor_ele.send_command.assert_called_with("ele_001,CMO,ele,ON")
    assert "ele_001:ele" in processor.pending_requests
    
    print("4️⃣ ACK 응답 수신")
    processor.handle_ack("ele_001", "ele")
    
    print("5️⃣ pending에서 제거 확인")
    assert "ele_001:ele" not in processor.pending_requests
    
    print("✓ 엔드-투-엔드 흐름 완료!")


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 60)
    print("시리얼 모니터 통합 테스트 시작")
    print("=" * 60)
    
    try:
        test_parser()
        test_find_target_device()
        test_cmo_request_timeout()
        test_queue_processor_pending()
        test_queue_processor_ack_handling()
        test_queue_processor_timeout()
        test_serial_monitor_cmd_handling()
        test_serial_monitor_sen_handling()
        test_end_to_end_flow()
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 예상치 못한 에러: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()