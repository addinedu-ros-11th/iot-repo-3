#include <Bonezegei_DHT11.h>
#include <Stepper.h>

#define STEPS 120
#define relayPin 3

Bonezegei_DHT11 dht(8);
const int R_LED = 9;
Stepper stepper(STEPS, 10, 11, 12, 13);

unsigned long previousMillis = 0;
const long interval = 5000;
const char* deviceId = "DHT-01";

bool motorRunning = false;  // 자동 제어 상태
bool AirOnControl = false;  // 에어컨 수동 제어 상태
bool HeatOnControl = false;  // 히터 수동 제어 상태
bool HumOnControl = false;  // 가습기 수동 제어 상태
bool AirStop = false;
bool HeatStop = false;
bool HumStop = false;

void handleHumidityAndTemperatureAIRHEAT()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");

      if (hum < 45)
      {
        digitalWrite(relayPin, HIGH);
      }
      else
      {
        digitalWrite(relayPin, LOW); 
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperatureAIRHUM()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");

      if (tempDeg >= 28)
      {
        analogWrite(R_LED, LOW);
      }
      else if (tempDeg <= 26)
      {
        analogWrite(R_LED, LOW);
      }
      else if (tempDeg <= 20)
      {
        analogWrite(R_LED, HIGH);
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperatureHEATHUM()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");
      
      if (tempDeg >= 28)
      {
        motorRunning = true; 
      }
      else if (tempDeg <= 26)
      {
        motorRunning = false;
      }
      else if (tempDeg <= 20)
      {
        motorRunning = false;
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperatureAIR()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");

      if (hum < 45)
      {
        digitalWrite(relayPin, HIGH);
        if (tempDeg >= 28)
        {
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 26)
        {
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 20)
        {
          analogWrite(R_LED, HIGH);
        }
      }
      else
      {
        digitalWrite(relayPin, LOW); 
        if (tempDeg >= 28)
        {
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 26)
        {
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 20)
        {
          analogWrite(R_LED, HIGH);
        }
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperatureHEAT()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");

      if (hum < 45)
      {
        digitalWrite(relayPin, HIGH);
        if (tempDeg >= 28)
        {
          motorRunning = true; 
        }
        else if (tempDeg <= 26)
        {
          motorRunning = false;
        }
        else if (tempDeg <= 20)
        {
          motorRunning = false;
        }
      }
      else
      {
        digitalWrite(relayPin, LOW); 
        if (tempDeg >= 28)
        {
          motorRunning = true; 
        }
        else if (tempDeg <= 26)
        {
          motorRunning = false;
        }
        else if (tempDeg <= 20)
        {
          motorRunning = false;
        }
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperatureHUM()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");

      if (hum < 45)
      {
        if (tempDeg >= 28)
        {
          motorRunning = true; 
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 26)
        {
          motorRunning = false;
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 20)
        {
          analogWrite(R_LED, HIGH);
          motorRunning = false;
        }
      }
      else
      {
        if (tempDeg >= 28)
        {
          motorRunning = true; 
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 26)
        {
          motorRunning = false;
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 20)
        {
          analogWrite(R_LED, HIGH);
          motorRunning = false;
        }
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperature()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");

      if (hum < 45)
      {
        digitalWrite(relayPin, HIGH);
        if (tempDeg >= 28)
        {
          motorRunning = true; 
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 26)
        {
          motorRunning = false;
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 20)
        {
          analogWrite(R_LED, HIGH);
          motorRunning = false;
        }
      }
      else
      {
        digitalWrite(relayPin, LOW); 
        if (tempDeg >= 28)
        {
          motorRunning = true; 
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 26)
        {
          motorRunning = false;
          analogWrite(R_LED, LOW);
        }
        else if (tempDeg <= 20)
        {
          analogWrite(R_LED, HIGH);
          motorRunning = false;
        }
      }
    }
    previousMillis = currentMillis;
  }
}

void handleHumidityAndTemperatureNO()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      float tempDeg = dht.getTemperature();
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      Serial.print("습도:");
      Serial.print(hum);
      Serial.println("%");
    }
    previousMillis = currentMillis;
  }
}

void setup()
{
  Serial.begin(9600);
  dht.begin();
  pinMode(R_LED, OUTPUT);
  stepper.setSpeed(150);
  pinMode(relayPin, OUTPUT);
  pinMode(5, OUTPUT);
  digitalWrite(5, HIGH);
}

void loop() 
{
  // 시리얼 명령 수신 및 상태 업데이트
  if (Serial.available()) 
  {
    char received = Serial.read();
    
    if (received == 'A')
    {
      AirOnControl = true;
      AirStop = false;
      motorRunning = true;
    }
    else if (received == 'B')
    {
      AirOnControl = false;
      AirStop = true;
      motorRunning = false;
    }
    else if (received == 'C')
    {
      HeatOnControl = true;
      HeatStop = false;
      analogWrite(R_LED, HIGH);
    }
    else if (received == 'D')
    {
      HeatOnControl = false;
      HeatStop = true;
      analogWrite(R_LED, LOW);
    }
    else if (received == 'E')
    {
      HumOnControl = true;
      HumStop = false;
      digitalWrite(relayPin, HIGH);
    }
    else if (received == 'F')
    {
      HumOnControl = false;
      HumStop = true;
      digitalWrite(relayPin, LOW);
    }
    else if (received == 'G')
    {
      AirOnControl = false;
      AirStop = false;
      HeatOnControl = false;
      HeatStop = false;
      HumOnControl = false;
      HumStop = false;
      motorRunning = false;
    }
  }
  
  // 조건문 체크 순서: 복잡한 조합부터 단순한 조합 순으로
  
  // === 3개 조합 (가장 우선) ===
  if ((AirOnControl || AirStop) && (HeatOnControl || HeatStop) && (HumOnControl || HumStop))
  {
    handleHumidityAndTemperatureNO();
  }
  
  // === 2개 조합 ===
  else if ((AirOnControl || AirStop) && (HeatOnControl || HeatStop))
  {
    handleHumidityAndTemperatureAIRHEAT();
  }
  else if ((AirOnControl || AirStop) && (HumOnControl || HumStop))
  {
    handleHumidityAndTemperatureAIRHUM();
  }
  else if ((HeatOnControl || HeatStop) && (HumOnControl || HumStop))
  {
    handleHumidityAndTemperatureHEATHUM();
  }
  
  // === 1개 조합 ===
  else if (AirOnControl || AirStop)
  {
    handleHumidityAndTemperatureAIR();
  }
  else if (HeatOnControl || HeatStop)
  {
    handleHumidityAndTemperatureHEAT();
  }
  else if (HumOnControl || HumStop)
  {
    handleHumidityAndTemperatureHUM();
  }
  
  // === 완전 자동 제어 (모든 수동 제어가 꺼져있을 때) ===
  else
  {
    handleHumidityAndTemperature();
  }

  // 모터 제어
  if (motorRunning)
  {
    stepper.step(STEPS);
  } 
}