#include <SPI.h>
#include <MFRC522.h>
#include <Stepper.h>

const int RST_PIN = 9;
const int SS_PIN = 10;
const int STEP_INT4 = 6;
const int STEP_INT2 = 3;
const int STEP_INT3 = 5;
const int STEP_INT1 = 2;
const int TRIG = A4;
const int ECHO = A5;

const int THRESHOLD = 30;

int MOTOR_STEPS = 2048;

unsigned long open_time;
bool is_detected;
bool is_valid;

MFRC522 rc522(SS_PIN, RST_PIN);
Stepper stepper(MOTOR_STEPS, STEP_INT4, STEP_INT2, STEP_INT3, STEP_INT1);


MFRC522::StatusCode checkAuth(int index, MFRC522::MIFARE_Key key);
MFRC522::StatusCode writeInteger(int index, MFRC522::MIFARE_Key key, int data);
void toBytes(byte* buffer, int data, int offset = 0);
int toInteger(byte* buffer, int offset = 0);
MFRC522::StatusCode readInteger(int index, MFRC522::MIFARE_Key key, int& data);
void waitForCard();
void closeDoor();
void checkTag(int index, MFRC522::MIFARE_Key key, int data);
long detectDistance();

void setup() {
	Serial.begin(9600);
	delay(1000);
	SPI.begin();
	rc522.PCD_Init();
	pinMode(TRIG, OUTPUT);
	pinMode(ECHO, INPUT);
	stepper.setSpeed(10);
    
	Serial.println(F("Entrance System Setup Done"));
}

void loop() {

	waitForCard();
	
	int index = 61;
	MFRC522::MIFARE_Key key;
	
	for (int i = 0; i < 6; i++)
	{
		key.keyByte[i] = 0xFF;
	}
	int i_data = 32767;
	is_valid = false;

	if (readInteger(index, key, i_data) == MFRC522::STATUS_OK)
	{
		is_valid = true;
		Serial.println("[DEBUG] Card is valid!");
	}
	else
	{
		Serial.println("[DEBUG] readInteger error");
	}

	rc522.PICC_HaltA();
	rc522.PCD_StopCrypto1();

	if (is_valid)
	{
		stepper.step(MOTOR_STEPS);
		open_time = millis();
		Serial.print("[DEBUG] {loop} open_time: ");
		Serial.println(open_time);
	}
	else
	{
		closeDoor();
	}

	while (open_time > 0 && (millis() - open_time) < 3000)
	{
			long dist = detectDistance();
			
			if (dist != 0 && dist < THRESHOLD)
			{
				is_detected = true;
				open_time = millis();
				Serial.println("[DEBUG] Object detected, door stays open");
			}
			else
			{
				is_detected = false;
			}
			
			delay(100);
	}

	if (!is_detected || (millis() - open_time) >= 3000)
	{
		closeDoor();
	}

}

long detectDistance()
{
	long duration, distance;
	int timeout = 23200;

	digitalWrite(TRIG, LOW);
	delayMicroseconds(2);

	digitalWrite(TRIG, HIGH);
	delayMicroseconds(10);
	digitalWrite(TRIG, LOW);
	
    
	duration = pulseIn(ECHO, HIGH, timeout);
	
	// 거리 계산: (시간 * 음속) / 2
	// 음속 = 340m/s = 0.034cm/us
	distance = duration * 0.034 / 2;

	if (distance == 0)
	{
		//Serial.println("[DEBUG] {detectDistance} distance = 0");
	}

	return distance;
}

void closeDoor()
{
	open_time = 0;
	is_detected = false;
	is_valid = false;
	stepper.step(-MOTOR_STEPS);
	Serial.println("[DEBUG] Door closed");
}

void waitForCard() 
{
  while (true) 
  {
    if (rc522.PICC_IsNewCardPresent() && rc522.PICC_ReadCardSerial()) 
    {
      Serial.println("[DEBUG] {waitForCard} Card detected!");

      // debug
      Serial.print("Card UID: ");
      for (byte i = 0; i < rc522.uid.size; i++) 
			{
        Serial.print(rc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
        Serial.print(rc522.uid.uidByte[i], HEX);
      }
      Serial.println();
      break;
    }
    delay(50);
  }
}

MFRC522::StatusCode checkAuth(int index, MFRC522::MIFARE_Key key)
{
	MFRC522::StatusCode status = rc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, index, &key, &(rc522.uid));

	if (status != MFRC522::STATUS_OK)
	{
		Serial.print("[DEBUG] {checkAuth} Authentication Failed: ");
		Serial.println(rc522.GetStatusCodeName(status));
	}

	return status;
}


void toBytes(byte* buffer, int data, int offset = 0)
{
	buffer[offset] = data & 0xFF;
	buffer[offset + 1] = (data >> 8) & 0xFF;
}

MFRC522::StatusCode writeInteger(int index, MFRC522::MIFARE_Key key, int data)
{
	MFRC522::StatusCode status = checkAuth(index, key);
	if (status != MFRC522::STATUS_OK)
	{
		return status;
	}

	byte buffer[16];
	memset(buffer, 0x00, sizeof(buffer));
	toBytes(buffer, data);

	status = rc522.MIFARE_Write(index, (byte*)&buffer, sizeof(buffer));
	if (status != MFRC522::STATUS_OK)
	{
			Serial.print("[DEBUG] {writeInteger} Write Failed: ");
			Serial.println(rc522.GetStatusCodeName(status));
	}

	return status;
}

int toInteger(byte* buffer, int offset = 0)
{
	return (buffer[offset + 1] << 8 | buffer[offset]);
}


MFRC522::StatusCode readInteger(int index, MFRC522::MIFARE_Key key, int& data)
{
	MFRC522::StatusCode status = checkAuth(index, key);
	if (status != MFRC522::STATUS_OK)
	{
		return status;
	}

	byte buffer[18];
	byte length = 18;

	status = rc522.MIFARE_Read(index, buffer, &length);
	
	if (status == MFRC522::STATUS_OK)
	{
		int cardData = toInteger(buffer);
		
		if (cardData == data)
		{
			return MFRC522::STATUS_OK;
		}
		else
		{
			return MFRC522::STATUS_CRC_WRONG;
		}
	}
	else
	{
		Serial.print("Read Failed: ");
		Serial.println(rc522.GetStatusCodeName(status));
		return status;
	}
}
