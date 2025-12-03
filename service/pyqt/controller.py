from datetime import datetime
from PyQt6.QtCore import QTimer

from models import SensorSimulator, DeviceState, AutoControl
from views import MainWindow


class SmartHomeController:
    """스마트홈 시스템 컨트롤러"""
    
    def __init__(self):
        self.view = MainWindow()
        
        # 모델 초기화
        self.sensor = SensorSimulator()
        self.device_state = DeviceState()
        self.auto_control = AutoControl(self.sensor, self.device_state)
        
        # 신호 연결
        self.connect_signals()
        
        # 타이머 초기화
        self.init_timers()
    
    def connect_signals(self):
        """신호 연결"""
        # 센서 신호
        self.sensor.temp_changed.connect(self.on_temp_changed)
        self.sensor.humidity_changed.connect(self.on_humidity_changed)
        self.sensor.illumination_changed.connect(self.on_illumination_changed)
        
        # 홈페이지 버튼 신호
        self.view.home_page.humidifier_on_btn.clicked.connect(
            lambda: self.on_device_toggled('humidifier', True))
        self.view.home_page.humidifier_off_btn.clicked.connect(
            lambda: self.on_device_toggled('humidifier', False))
        
        self.view.home_page.ac_on_btn.clicked.connect(
            lambda: self.on_device_toggled('ac', True))
        self.view.home_page.ac_off_btn.clicked.connect(
            lambda: self.on_device_toggled('ac', False))
        
        self.view.home_page.heater_on_btn.clicked.connect(
            lambda: self.on_device_toggled('heater', True))
        self.view.home_page.heater_off_btn.clicked.connect(
            lambda: self.on_device_toggled('heater', False))
        
        self.view.home_page.curtain_open_btn.clicked.connect(
            lambda: self.on_device_toggled('curtain_open', True))
        self.view.home_page.curtain_close_btn.clicked.connect(
            lambda: self.on_device_toggled('curtain_open', False))
        
        # 실외페이지 버튼 신호
        self.view.outside_page.call_elevator_btn.clicked.connect(
            self.on_elevator_called)
        
        # 자동 제어 신호
        self.auto_control.log_signal.connect(self.add_log)
        self.device_state.state_changed.connect(self.on_device_state_changed)
    
    def init_timers(self):
        """타이머 초기화"""
        # 센서 업데이트 타이머
        self.sensor_timer = QTimer()
        self.sensor_timer.timeout.connect(self.sensor.simulate)
        self.sensor_timer.start(1000)
        
        # 자동 제어 타이머
        self.auto_control_timer = QTimer()
        self.auto_control_timer.timeout.connect(self.on_auto_control_tick)
        self.auto_control_timer.start(2000)
    
    def on_temp_changed(self, temp):
        """온도 변경"""
        self.view.home_page.temp_display.setText(f"{temp:.1f}°C")
    
    def on_humidity_changed(self, humidity):
        """습도 변경"""
        self.view.home_page.humidity_display.setText(f"{humidity:.1f}%")
        self.view.home_page.humidity_circle.set_value(humidity)
    
    def on_illumination_changed(self, illumination):
        """조도 변경"""
        self.view.home_page.illumination_display.setText(f"{illumination:.0f} lux")
        self.view.home_page.illumination_bar.setValue(int(illumination))
    
    def on_device_toggled(self, device, state):
        """장치 토글"""
        self.device_state.set_device_state(device, state)
        self.auto_control.set_auto_mode(device.replace('_open', ''), False)
        
        status = "ON" if state else "OFF"
        self.add_log(f"🔧 {device.upper()} → 수동 {status}")
    
    def on_device_state_changed(self, device, state):
        """장치 상태 변경"""
        status_text = "ON ✓" if state else "OFF"
        
        if device == 'humidifier':
            self.view.home_page.humidifier_status.setText(f"가습기: {status_text}")
        elif device == 'ac':
            self.view.home_page.ac_status.setText(f"에어컨: {status_text}")
        elif device == 'heater':
            self.view.home_page.heater_status.setText(f"히터: {status_text}")
        elif device == 'curtain_open':
            curtain_status = "개방" if state else "폐쇄"
            self.view.home_page.curtain_status.setText(f"커튼: {curtain_status}")
    
    def on_elevator_called(self):
        """엘리베이터 호출"""
        self.device_state.set_device_state('elevator_called', True)
        self.view.outside_page.elevator_status_label.setText("상태: 호출됨 ⬆️")
        self.add_log("📞 엘리베이터 호출 - 공동현관 층으로 이동중")
        
        # 3초 후 도착
        QTimer.singleShot(3000, self.on_elevator_arrived)
    
    def on_elevator_arrived(self):
        """엘리베이터 도착"""
        self.device_state.set_device_state('elevator_called', False)
        self.view.outside_page.elevator_status_label.setText("상태: 대기중")
        self.add_log("✅ 엘리베이터 도착")
    
    def on_auto_control_tick(self):
        """자동 제어 실행"""
        self.auto_control.execute()
    
    def add_log(self, message):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.view.home_page.log_text.append(log_message)
        self.view.home_page.log_text.verticalScrollBar().setValue(
            self.view.home_page.log_text.verticalScrollBar().maximum()
        )
    
    def show(self):
        """윈도우 표시"""
        self.view.show()
    
    def stop(self):
        """타이머 정지"""
        self.sensor_timer.stop()
        self.auto_control_timer.stop()