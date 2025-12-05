# main.py
"""메인 실행 파일"""

import os
from dotenv import load_dotenv

from app import SerialMonitorApp


def main():
    load_dotenv()
    
    # DB 설정
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    # 포트 설정
    port_config = {
        'ent_001': '/dev/ttyACM1',
        'ele_001': '/dev/ttyACM0',
        'dht_001': '/dev/ttyACM9',
        'cur_001': '/dev/ttyACM#',
    }
    
    # 애플리케이션 실행
    app = SerialMonitorApp(db_config, port_config)
    app.run()


if __name__ == '__main__':
    main()