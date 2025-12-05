#include <Bonezegei_DHT11.h>
#include <Stepper.h>

#define STEPS 120
#define relayPin 3
#define AUX_PIN 5 // 5번 핀 정의 (digitalWrite(5, HIGH) 용)
#define R_LED 9   // LED 핀 정의

class ClimateManager {
private:
    // 하드웨어 객체
    Bonezegei_DHT11 dht;
    Stepper stepper;

    // 타이밍 변수
    unsigned long previousMillis;
    const long interval;

    // 제어 상태 플래그 (원본 코드의 전역 변수들)
    bool motorRunning;      // 스테퍼 모터 (에어컨) 제어 상태
    bool AirOnControl;      // 에어컨 수동 켜짐 제어 플래그
    bool HeatOnControl;     // 히터 수동 켜짐 제어 플래그
    bool HumOnControl;      // 가습기 수동 켜짐 제어 플래그
    bool AirStop;           // 에어컨 수동 꺼짐 제어 플래그
    bool HeatStop;          // 히터 수동 꺼짐 제어 플래그
    bool HumStop;           // 가습기 수동 꺼짐 제어 플래그

public:
    // 생성자: 핀 번호를 인자로 받아 초기화
    ClimateManager(int dhtPin, int steps, int sPin1, int sPin2, int sPin3, int sPin4)
      : dht(dhtPin), 
        stepper(steps, sPin1, sPin2, sPin3, sPin4), 
        interval(5000), 
        previousMillis(0),
        motorRunning(false),
        AirOnControl(false), HeatOnControl(false), HumOnControl(false),
        AirStop(false), HeatStop(false), HumStop(false)
    {
    }

    void begin() {
      Serial.begin(9600);
      dht.begin();
      stepper.setSpeed(150);
      pinMode(R_LED, OUTPUT);
      pinMode(relayPin, OUTPUT);
      pinMode(AUX_PIN, OUTPUT);
      digitalWrite(AUX_PIN, HIGH);
    }

    // 시리얼 명령 처리 함수: ACK 출력 및 제어 플래그 업데이트
    void processSerialCommand() {
      if (Serial.available()) {
        char received = Serial.read();
        
        // 플래그 업데이트 및 ACK 출력 (원본 로직과 동일)
        if (received == 'A') { AirOnControl = true; AirStop = false; motorRunning = true; printAck("AIR", "1"); }
        else if (received == 'B') { AirOnControl = false; AirStop = true; motorRunning = false; printAck("AIR", "0"); }
        else if (received == 'G') { AirOnControl = false; AirStop = false; motorRunning = false; printAck("AIR", "-1"); }
        
        else if (received == 'C') { HeatOnControl = true; HeatStop = false; analogWrite(R_LED, HIGH); printAck("HEAT", "1"); }
        else if (received == 'D') { HeatOnControl = false; HeatStop = true; analogWrite(R_LED, LOW); printAck("HEAT", "0"); }
        else if (received == 'H') { HeatOnControl = false; HeatStop = false; printAck("HEAT", "-1"); }
        
        else if (received == 'E') { HumOnControl = true; HumStop = false; digitalWrite(relayPin, HIGH); printAck("HUMI", "1"); }
        else if (received == 'F') { HumOnControl = false; HumStop = true; digitalWrite(relayPin, LOW); printAck("HUMI", "0"); }
        else if (received == 'I') { HumOnControl = false; HumStop = false; printAck("HUMI", "-1"); }
      }
    }

    // 메인 제어 로직: 8개의 함수 대신 이 함수 하나로 통합됨
    void executeControlLogic() {
      // 1. 수동/자동 상태 판단
      // 원본 코드의 복잡한 if-else 구조를 명확하게 대체
      bool isAirManual = AirOnControl || AirStop;
      bool isHeatManual = HeatOnControl || HeatStop;
      bool isHumManual = HumOnControl || HumStop;

      // 2. 센서 데이터 업데이트 주기 체크 (5초)
      unsigned long currentMillis = millis();
      if (currentMillis - previousMillis >= interval) {
        if (dht.getData()) {
          int tempDeg = dht.getTemperature();
          int hum = dht.getHumidity();
          printSensorData(tempDeg, hum); // 센서 출력

          // 각 장치별 자동/수동 로직을 독립적으로 실행
          // 수동 제어가 걸려있지 않은 장치만 센서로 제어
          if (!isHumManual) updateHumidifier(hum);
          if (!isAirManual) updateAirCon(tempDeg);
          if (!isHeatManual) updateHeater(tempDeg);

          // 예외: 모두 수동/정지인 경우, 센서 출력만 실행
          if (isAirManual && isHeatManual && isHumManual) {
             // handleHumidityAndTemperatureNO()와 동일 (센서 출력만 하면 됨)
          } 
          // 다른 조합들은 위에서 이미 필요한 제어 로직이 자동/수동에 따라 실행됨.
        }
        previousMillis = currentMillis;
      }
    }

    // 모터 구동 (loop()의 마지막 부분)
    void runMotorStep() {
      if (motorRunning) {
        stepper.step(STEPS);
      }
    }

private:
    // ** 자동 제어 로직 **
    // A. 가습기 (Relay, Hum)
    void updateHumidifier(int hum) {
        bool humState = (hum < 45);
        digitalWrite(relayPin, humState ? HIGH : LOW);
    }
    
    // B. 에어컨 (Motor, Temp) - motorRunning 플래그만 변경
    void updateAirCon(int temp) {
        if (temp >= 28) motorRunning = true;
        else if (temp <= 26) motorRunning = false;
        // else: motorRunning 상태 유지
    }

    // C. 히터 (LED, Temp)
    void updateHeater(int temp) {
        bool ledState = false;
        // 1. 20도 이하: 켜짐 (가장 우선)
        if (temp <= 20) ledState = true; 
        // 2. 26도 이하: 꺼짐 (20도보다 크고 26도보다 작을 때)
        else if (temp <= 26) ledState = false;
        // 3. 28도 이상: 꺼짐
        else if (temp >= 28) ledState = false;
        
        analogWrite(R_LED, ledState ? 255 : 0);
    }
    
    // 시리얼 헬퍼 함수
    void printAck(const char* dev, const char* val) {
      Serial.print("ACK");
      Serial.print(",");
      Serial.print(dev);
      Serial.print(",");
      Serial.println(val);
    }

    void printSensorData(int temp, int hum) {
      Serial.print("SEN");
      Serial.print(",TEM,");
      Serial.print(temp);
      Serial.print(",HUM,");
      Serial.println(hum);
    }
};

// --- 메인 스케치 ---
// (DHT핀, 스텝수, 모터핀1,2,3,4)
ClimateManager myManager(8, STEPS, 10, 11, 12, 13); 

void setup() {
  myManager.begin();
}

void loop() {
  // 1. 시리얼 명령 처리 (가장 빠름)
  myManager.processSerialCommand(); 
  
  // 2. 제어 로직 실행 (5초에 한 번 센서를 읽고 플래그 업데이트)
  myManager.executeControlLogic();
  
  // 3. 모터 구동 (끊임없이 실행 -> 반응성 및 부드러움 향상)
  myManager.runMotorStep(); 
}