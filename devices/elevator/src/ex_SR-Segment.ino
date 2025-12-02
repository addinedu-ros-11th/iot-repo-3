// 74HC595 시프트 레지스터 제어에 사용될 핀 정의
const int dataPin = 2;   // DS (Serial Data Input)
const int clockPin = 3;  // SHCP (Shift Register Clock)
const int latchPin = 4;  // STCP (Storage Register Clock/Latch)

// 7-Segment 표시 패턴 배열 (8-bit)
// 공통 애노드(Common Anode) 가정: 0 = 켜짐, 1 = 꺼짐
// 연결 순서: Q0(a), Q1(b), ..., Q6(g), Q7(dp)
const byte segmentPatterns[] = {
  // 7 6 5 4 3 2 1 0 (dp g f e d c b a)
  // 0
  B10000000, // 0xC0 
  // 1
  B11111001, // 0xF9
  // 2
  B10100100, // 0xA4
  // 3
  B10110000, // 0xB0
  // 4
  B10011001, // 0x99
  // 5
  B10010010, // 0x92
  // 6
  B10000010, // 0x82
  // 7
  B11111000, // 0xF8
  // 8
  B10000000, // 0x80
  // 9
  B10010000, // 0x90
};

// 첫 번째 시프트 레지스터 (7-Segment가 연결되지 않은 레지스터)를 위한 더미 데이터
// 16비트 전송에서 나중에 전송되어 첫 번째 레지스터에 남는 데이터입니다.
// 모든 출력을 끄기 위해 1111 1111 (0xFF)로 설정합니다. (공통 애노드 기준)
const byte dummyData = 0x00; 


void setup() {
  pinMode(latchPin, OUTPUT);
  pinMode(clockPin, OUTPUT);
  pinMode(dataPin, OUTPUT);
}

void loop() {
  // 0부터 9까지 순차적으로 표시
  for (int i = 0; i < 10; i++) {
    // 1. Latch Pin LOW (전송 준비)
    digitalWrite(latchPin, LOW);
    
    // **2. 데이터 전송 (총 16비트)**
    
    // a) 7-Segment 패턴 전송 (8비트)
    // 이 데이터가 가장 먼저 전송되어 Daisy-Chain의 끝, 즉 **두 번째 레지스터**로 이동합니다.
    shiftOut(dataPin, clockPin, MSBFIRST, segmentPatterns[i]);
    
    // b) 더미 데이터 전송 (8비트)
    // 이 데이터가 나중에 전송되어 **첫 번째 레지스터**에 남게 됩니다.
    shiftOut(dataPin, clockPin, MSBFIRST, dummyData);
    
    // 3. Latch Pin HIGH (데이터 출력)
    digitalWrite(latchPin, HIGH);

    // 0.5초 대기
    delay(500);
  }
}