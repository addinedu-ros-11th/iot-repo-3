#include "entrance.h"

Entrance::Entrance() : rc522(SS_PIN, RST_PIN), stepper(MOTOR_STEPS, STEP_INT4, STEP_INT2, STEP_INT3, STEP_INT1) 
{
	open_time = 0;
	is_detected = false;
	is_valid = false;
}

void Entrance::setup() 
{
	Serial.begin(9600);
	delay(1000);
	SPI.begin();
	rc522.PCD_Init();
	pinMode(TRIG, OUTPUT);
	pinMode(ECHO, INPUT);
	stepper.setSpeed(10);
	Serial.println(F("Entrance System Setup Done"));
}


void Entrance::loop() 
{
	// ✅ 상태 1: 카드 대기 중
	if (open_time == 0)
	{
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
			is_valid = false;
			Serial.println("[DEBUG] Card is NOT valid");
		}

		rc522.PICC_HaltA();
		rc522.PCD_StopCrypto1();

		if (is_valid) 
		{
			stepper.step(MOTOR_STEPS);
			open_time = millis();
			Serial.print("[DEBUG] Door opened at: ");
			Serial.println(open_time);
		}
	}
	// ✅ 상태 2: 문이 열려있는 중 (거리 감지)
	else if (open_time > 0 && (millis() - open_time) < 3000)
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
	}
	// ✅ 상태 3: 3초 초과 또는 문이 닫혀있음
	else if ((millis() - open_time) >= 3000)
	{
		closeDoor();
	}
}

void Entrance::waitForCard() 
{
	while (true) 
	{
		if (rc522.PICC_IsNewCardPresent() && rc522.PICC_ReadCardSerial()) 
		{
			Serial.println("[DEBUG] {waitForCard} Card detected!");
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

void Entrance::closeDoor() 
{
	open_time = 0;
	is_detected = false;
	is_valid = false;
	stepper.step(-MOTOR_STEPS);
	Serial.println("[DEBUG] Door closed");
}

MFRC522::StatusCode Entrance::checkAuth(int index, MFRC522::MIFARE_Key key) 
{
	MFRC522::StatusCode status = rc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, index, &key, &(rc522.uid));

	if (status != MFRC522::STATUS_OK) 
	{
		Serial.print("[DEBUG] {checkAuth} Authentication Failed: ");
		Serial.println(rc522.GetStatusCodeName(status));
	}

	return status;
}

void Entrance::toBytes(byte* buffer, int data, int offset) 
{
	buffer[offset] = data & 0xFF;
	buffer[offset + 1] = (data >> 8) & 0xFF;
}

int Entrance::toInteger(byte* buffer, int offset) 
{
	return (buffer[offset + 1] << 8 | buffer[offset]);
}

long Entrance::detectDistance() 
{
	long duration, distance;
	int timeout = 23200;

	digitalWrite(TRIG, LOW);
	delayMicroseconds(2);

	digitalWrite(TRIG, HIGH);
	delayMicroseconds(10);
	digitalWrite(TRIG, LOW);
	
	duration = pulseIn(ECHO, HIGH, timeout);
	
	distance = duration * 0.034 / 2;

	if (distance == 0) 
	{	
		Serial.println("[DEBUG] distance is 0");
	}

	return distance;
}

MFRC522::StatusCode Entrance::readInteger(int index, MFRC522::MIFARE_Key key, int& data) 
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

MFRC522::StatusCode Entrance::writeInteger(int index, MFRC522::MIFARE_Key key, int data) 
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