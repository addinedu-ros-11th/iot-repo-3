# parser.py
"""시리얼 데이터 파싱"""

from typing import Optional
from models import SerialData


class SerialParser:
    """시리얼 데이터 파싱"""
    
    DELIMITER = ','
    VALID_TYPES = {'SEN', 'CMD', 'ACK', 'CMO'}
    
    @staticmethod
    def parse(raw_data: str, device_id: str) -> Optional[SerialData]:
        """
        파싱: data_type,metric_name,value
        device_id는 포트에서 주입
        """
        try:
            parts = raw_data.strip().split(SerialParser.DELIMITER)
            if len(parts) != 3:
                print(f"[ERROR] 잘못된 형식: {raw_data}")
                return None
            
            data_type, metric_name, value = parts
            
            if data_type not in SerialParser.VALID_TYPES:
                print(f"[ERROR] 잘못된 data_type: {data_type}")
                return None
            
            return SerialData(device_id, data_type, metric_name, value)
        
        except Exception as e:
            print(f"[ERROR] 파싱 실패: {e}")
            return None