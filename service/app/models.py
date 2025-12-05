# models.py
"""데이터 모델 정의"""

import time
from dataclasses import dataclass, field


@dataclass
class CMORequest:
    """CMO 요청"""
    device_id: str
    metric_name: str
    value: str
    command: str
    timestamp: float = field(default_factory=time.time)
    timeout: float = 10.0
    
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.timeout
    
    def elapsed_time(self) -> float:
        return time.time() - self.timestamp


@dataclass
class SerialData:
    """파싱된 시리얼 데이터"""
    device_id: str
    data_type: str
    metric_name: str
    value: str