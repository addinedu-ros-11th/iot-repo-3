# 스마트 커튼 디바이스

28BYJ-48 스텝모터와 조도 센서(LDR, Light Dependent Resistor)를 이용해
실내 밝기에 따라 커튼을 자동으로 여닫고, 동작 로그를 공통 DB에 저장하는 디바이스입니다.

## 구성 디렉터리

- `arduino/`
  - `stepper_ldr_curtain.ino`
    - 28BYJ-48 스텝모터 + ULN2003 드라이버 보드
    - 조도 센서(LDR)를 이용한 자동 커튼 제어 스케치
    - 시리얼 출력 포맷: `device_id,light_value,motor_direction,current_step,max_steps`

- `tools/`
  - `curtain_log_uploader.py`
    - 아두이노 시리얼 로그를 AWS RDS(MySQL) `ioclean.curtain_log` 테이블에 INSERT
  - `curtain_log_viewer.py`
    - RDS의 `curtain_log`를 조회하는 PyQt 기반 뷰어 (5초 자동 새로고침)
  - `requirements.txt`
    - 업로더/뷰어 실행에 필요한 파이썬 패키지 목록
  - `.env.example`
    - DB/시리얼 설정 예시 파일
    - 실제 사용 시 `.env`로 복사 후 값 채워서 사용 (`.env`는 Git에 커밋하지 않음)
  - `.gitignore`
    - `.env` 등 민감 정보를 Git 추적에서 제외

- `docs/`
  - `README.md`
    - 커튼 디바이스 하드웨어/배선/사용 상세 설명

## 동작 개요

1. 조도 센서(LDR)가 실내 밝기를 주기적으로 측정합니다.
2. 밝기가 임계값보다 낮으면 커튼을 열고, 너무 밝으면 커튼을 닫습니다.
3. 각 측정 시점마다 다음 정보를 시리얼 로그로 남깁니다.
   - `device_id` (예: `curtain-01`)
   - `light_value` (0~1023)
   - `motor_direction` (`1`: 열기, `-1`: 닫기, `0`: 정지)
   - `current_step` (현재 스텝 위치)
   - `max_steps` (완전 개폐에 필요한 최대 스텝 수)
4. `curtain_log_uploader.py`가 시리얼 로그를 읽어 공통 DB(`ioclean.curtain_log`)에 적재합니다.
5. `curtain_log_viewer.py`로 최근 로그를 조회하고 모니터링할 수 있습니다.

## 빠른 시작

1. `devices/curtain/docs/README.md`를 참고해 하드웨어를 배선하고
   `arduino/stepper_ldr_curtain.ino`를 업로드합니다.
2. `devices/curtain/tools/.env.example`를 복사해 `.env`를 만들고 DB/포트 설정을 채웁니다.
3. `devices/curtain/tools/requirements.txt` 기반으로 파이썬 의존성을 설치합니다.
4. `curtain_log_uploader.py` → `curtain_log_viewer.py` 순서로 실행하여
   커튼 로그가 DB에 쌓이고 뷰어에서 보이는지 확인합니다.
