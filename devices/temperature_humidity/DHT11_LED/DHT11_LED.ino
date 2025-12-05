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

bool motorRunning = false;

void handleHumidityAndTemperature()
{
  unsigned long currentMillis = millis();

  if (currentMillis - previousMillis >= interval)
  {
    if (dht.getData())
    {
      //온도 측정
      float tempDeg = dht.getTemperature();
      //습도 측정
      int hum = dht.getHumidity();
      Serial.println("---------");
      Serial.println(deviceId);
      //온도 결과
      Serial.print("온도:");
      Serial.print(tempDeg, 1);
      Serial.println("°C");
      //습도 결과
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

  handleHumidityAndTemperature();
  if (motorRunning)
  {
    stepper.step(STEPS);  // 한 스텝씩 계속 회전
  } 
}