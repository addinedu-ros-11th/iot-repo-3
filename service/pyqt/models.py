import random
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class SensorSimulator(QObject):
    """센서 데이터 시뮬레이터"""
    temp_changed = pyqtSignal(float)
    humidity_changed = pyqtSignal(float)
    illumination_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.temp = 22.0
        self.humidity = 50.0
        self.illumination = 500.0
        
    def simulate(self):
        """센서 데이터 시뮬레이션"""
        """지금은 랜덤 값으로 설정. 추후 db 쿼리문으로 변경 필요"""
        self.temp += random.uniform(-0.5, 0.5)
        self.humidity += random.uniform(-2, 2)
        self.illumination += random.uniform(-50, 50)
        
        self.temp = max(15, min(35, self.temp))
        self.humidity = max(20, min(80, self.humidity))
        self.illumination = max(0, min(10000, self.illumination))
        
        self.temp_changed.emit(self.temp)
        self.humidity_changed.emit(self.humidity)
        self.illumination_changed.emit(self.illumination)


class DeviceState(QObject):
    """장치 상태 관리"""
    state_changed = pyqtSignal(str, bool)
    
    def __init__(self):
        super().__init__()
        self.devices = {
            'humidifier': False,
            'ac': False,
            'heater': False,
            'curtain_open': False,
            'elevator_called': False,
        }
    
    def set_device_state(self, device, state):
        """장치 상태 설정"""
        if device in self.devices:
            self.devices[device] = state
            self.state_changed.emit(device, state)
    
    def get_device_state(self, device):
        """장치 상태 조회"""
        return self.devices.get(device, False)


class AutoControl(QObject):
    """자동 제어 로직"""
    log_signal = pyqtSignal(str)
    
    def __init__(self, sensor, device_state):
        super().__init__()
        self.sensor = sensor
        self.device_state = device_state
        self.auto_mode = {
            'humidifier': True,
            'ac': True,
            'heater': True,
            'curtain': True,
        }
    
    def set_auto_mode(self, device, enabled):
        """자동 제어 모드 설정"""
        if device in self.auto_mode:
            self.auto_mode[device] = enabled
    
    def get_auto_mode(self, device):
        """자동 제어 모드 조회"""
        return self.auto_mode.get(device, False)
    
    def execute(self):
        """자동 제어 실행"""
        temp = self.sensor.temp
        humidity = self.sensor.humidity
        illumination = self.sensor.illumination
        
        self._control_humidifier(humidity)
        self._control_ac(temp)
        self._control_heater(temp)
        self._control_curtain(illumination)
    
    def _control_humidifier(self, humidity):
        """가습기 자동 제어"""
        if not self.auto_mode['humidifier']:
            return
        
        if humidity < 40 and not self.device_state.get_device_state('humidifier'):
            self.device_state.set_device_state('humidifier', True)
            self.log_signal.emit("💧 가습기 자동 ON")
        elif humidity > 60 and self.device_state.get_device_state('humidifier'):
            self.device_state.set_device_state('humidifier', False)
            self.log_signal.emit("💧 가습기 자동 OFF")
    
    def _control_ac(self, temp):
        """에어컨 자동 제어"""
        if not self.auto_mode['ac']:
            return
        
        if temp > 26 and not self.device_state.get_device_state('ac'):
            self.device_state.set_device_state('ac', True)
            self.log_signal.emit("❄️ 에어컨 자동 ON")
        elif temp < 22 and self.device_state.get_device_state('ac'):
            self.device_state.set_device_state('ac', False)
            self.log_signal.emit("❄️ 에어컨 자동 OFF")
    
    def _control_heater(self, temp):
        """히터 자동 제어"""
        if not self.auto_mode['heater']:
            return
        
        if temp < 18 and not self.device_state.get_device_state('heater'):
            self.device_state.set_device_state('heater', True)
            self.log_signal.emit("🔥 히터 자동 ON")
        elif temp > 22 and self.device_state.get_device_state('heater'):
            self.device_state.set_device_state('heater', False)
            self.log_signal.emit("🔥 히터 자동 OFF")
    
    def _control_curtain(self, illumination):
        """커튼 자동 제어"""
        if not self.auto_mode['curtain']:
            return
        
        if illumination > 7000 and not self.device_state.get_device_state('curtain_open'):
            self.device_state.set_device_state('curtain_open', True)
            self.log_signal.emit("🪟 커튼 자동 개폐")
        elif illumination < 3000 and self.device_state.get_device_state('curtain_open'):
            self.device_state.set_device_state('curtain_open', False)
            self.log_signal.emit("🪟 커튼 자동 폐쇄")