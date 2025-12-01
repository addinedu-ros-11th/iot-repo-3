# 스마트 커튼 디바이스 상세 설명

이 문서는 스마트 커튼 디바이스의 하드웨어 배선,
아두이노 스케치 업로드, 파이썬 도구 실행 방법을 자세히 설명합니다.

## 1. 개요

스마트 커튼 디바이스는 조도 센서(LDR)로 외부 밝기를 측정하고,
밝기에 따라 커튼을 자동으로 열고 닫으며, 동작 로그를 공통 DB(AWS RDS)에 저장합니다.

## 2. 하드웨어 구성

### 2-1. 사용 부품

- Arduino Uno (또는 호환 보드)
- 28BYJ-48 스텝모터 + ULN2003 드라이버 보드
- 조도 센서(LDR)
- 10kΩ 저항 (LDR 분압용)
- 점퍼 케이블, 브레드보드
- (선택) 커튼을 감을 풀리/도르래 및 간단한 기구 부품

### 2-2. 배선 (예시)

**스텝모터 + ULN2003**

- ULN2003 IN1 → Arduino D8
- ULN2003 IN2 → Arduino D10
- ULN2003 IN3 → Arduino D9
- ULN2003 IN4 → Arduino D11
- ULN2003 VCC → 5V
- ULN2003 GND → GND

**조도 센서(LDR) + 10kΩ 저항 (분압 회로)**

- 5V — LDR — A0 — 10kΩ — GND

조도 센서 양단 중 하나는 5V, 다른 쪽은 A0로 연결하고,
A0와 GND 사이에 10kΩ 저항을 연결해 분압 구조를 만듭니다.

## 3. 아두이노 스케치

### 3-1. 파일 위치

- `devices/curtain/arduino/stepper_ldr_curtain.ino`

### 3-2. 주요 동작

- `CurtainController` 클래스를 사용하여 커튼 상태를 관리합니다.
- 약 **3초 주기**로 LDR 값을 읽어 밝기를 판단합니다.
- 조도 **임계값 500**을 기준으로 밝기 상태를 판별합니다.
  - 500 이상: 커튼 열기 방향으로 모터 동작
  - 500 미만: 커튼 닫기 방향으로 모터 동작
- 모터는 1스텝씩 비동기적으로 움직이며, 현재 스텝 수를 내부에서 관리합니다.
- 매 3초 주기마다 다음 정보를 CSV 한 줄로 시리얼에 출력합니다.

```text
device_id,light_value,motor_direction,current_step,max_steps
```

### 3-3. 업로드 방법

1. Arduino IDE에서 `stepper_ldr_curtain.ino`를 엽니다.
2. 보드와 포트를 선택합니다.
3. 스케치를 업로드합니다.
4. (테스트용) 시리얼 모니터에서 CSV 로그가 주기적으로 출력되는지 확인합니다.
   이후 파이썬 업로더를 사용할 때는 시리얼 모니터를 닫습니다.

## 4. 파이썬 업로더 / 뷰어

### 4-1. 환경 설정 (.env)

`devices/curtain/tools/`에서:

```bash
cd devices/curtain/tools
cp .env.example .env
```

`.env` 파일을 열고 실제 환경에 맞게 값을 수정합니다.

- `CURTAIN_DB_HOST` : RDS/MySQL 호스트
- `CURTAIN_DB_PORT` : 포트 (기본 3306)
- `CURTAIN_DB_USER` : DB 사용자 (예: `ioclean_user`)
- `CURTAIN_DB_PASSWORD` : DB 비밀번호
- `CURTAIN_DB_NAME` : DB 이름 (예: `ioclean`)
- `CURTAIN_SERIAL_PORT` : 아두이노 시리얼 포트 (예: `/dev/ttyACM0`)
- `CURTAIN_SERIAL_BAUD` : 보레이트 (예: `9600`)

`.env` 파일은 Git에 커밋하지 않고, 로컬에서만 사용합니다.

### 4-2. 파이썬 의존성 설치

```bash
cd devices/curtain/tools
pip install -r requirements.txt
```

### 4-3. 로그 업로더 실행 (Arduino → RDS)

```bash
cd devices/curtain/tools
python curtain_log_uploader.py
```

- 아두이노 보드는 `stepper_ldr_curtain.ino`가 업로드된 상태여야 합니다.
- Arduino IDE의 시리얼 모니터는 닫혀 있어야 포트 충돌이 발생하지 않습니다.
- 스크립트는 시리얼 라인을 읽어 `ioclean.curtain_log` 테이블에 INSERT 합니다.
- 데이터는 대략 3초 간격으로 업로드됩니다.

### 4-4. 로그 뷰어 실행 (RDS → 화면)

```bash
cd devices/curtain/tools
python curtain_log_viewer.py
```

- `.env` 또는 환경변수에서 DB 설정을 읽어 연결합니다.
- 상단에서 `device_id`, `최근 분`, `최대 행 수`를 설정할 수 있습니다.
- 5초마다 자동으로 최신 데이터를 조회하며,
  "최근 데이터 갱신" 버튼으로 수동 새로고침도 가능합니다.

## 5. 데이터 흐름 / DB 구조 요약

- Arduino (조도 측정 & 모터 제어)
- → 시리얼(CSV 로그)
- → `curtain_log_uploader.py` (Python)
- → AWS RDS MySQL `ioclean.curtain_log` 테이블
- → `curtain_log_viewer.py` (PyQt 뷰어)

`curtain_log` 테이블 주요 컬럼은 시리얼 로그 포맷과 1:1로 대응합니다.

## 6. 트러블슈팅

- **시리얼 포트 열기 오류 (Device or resource busy)**
  - Arduino IDE 시리얼 모니터 또는 다른 프로그램이 포트를 점유하고 있는지 확인하고 모두 닫습니다.

- **DB 연결 오류 (환경변수 설정 필요)**
  - `.env` 내용이 올바른지, RDS 보안 그룹에서 현재 PC IP가 허용되었는지 확인합니다.

- **로그는 쌓이는데 뷰어에서 안 보이는 경우**
  - `최근 분` 값을 넉넉하게(예: 60분) 설정하고 다시 조회합니다.
  - `device_id` 필터가 실제 `device_id` 값과 일치하는지 확인합니다.
