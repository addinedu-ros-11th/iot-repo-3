#include "entrance.h"
#include <EEPROM.h>
#include <AccelStepper.h>

bool Entrance::getIsValid()
{
	return m_is_valid;
}
enum DoorState { DOOR_IDLE, DOOR_OPENING, DOOR_OPEN, DOOR_CLOSING };
DoorState doorState = DOOR_IDLE;

Entrance::Entrance() : rc522(SS_PIN, RST_PIN), stepper(AccelStepper::FULL4WIRE, STEP_INT1, STEP_INT3, STEP_INT2, STEP_INT4) 
{
	m_open_time = 0;
	m_is_detected = false;
	m_is_valid = false;
	doorState = DOOR_IDLE;
}

void Entrance::setup() 
{
	Serial.begin(9600);
	delay(1000);
	SPI.begin();
	rc522.PCD_Init();
	pinMode(TRIG, OUTPUT);
	pinMode(ECHO, INPUT);
	stepper.setMaxSpeed(700);
	stepper.setAcceleration(1000);
	stepper.setPinsInverted(false, false, true);

	Serial.println(F("Entrance System Setup Done"));
	set_device_id();
}

void Entrance::loop() 
{
	while (Serial.available() > 0) 
	{
		char incomingChar = Serial.read();
		
		if (incomingChar == '\n') 
		{
			if (m_serial_buffer.length() > 0) 
			{
				Serial.print("[DEBUG] Received: ");
				Serial.println(m_serial_buffer);
				parseSerialCommand(m_serial_buffer);
				m_serial_buffer = "";
			}
		}
		else if (incomingChar == '\r') 
		{
			// 무시
		}
		else if (m_serial_buffer.length() < BUFFER_SIZE) 
		{
			m_serial_buffer += incomingChar;
		}
	}

	// ✅ 상태 1: 카드 대기 중
	if (doorState == DOOR_IDLE)
	{
		if (rc522.PICC_IsNewCardPresent() && rc522.PICC_ReadCardSerial()) 
		{
			Serial.println("[DEBUG] Card detected!");
			m_card_uid_size = rc522.uid.size;
			for (byte i = 0; i < m_card_uid_size; i++) 
			{
				m_card_uid[i] = rc522.uid.uidByte[i];
			}

			Serial.print("Card UID: ");
			for (byte i = 0; i < rc522.uid.size; i++) 
			{
				Serial.print(rc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
				Serial.print(rc522.uid.uidByte[i], HEX);
			}
			Serial.println();

			int index = 61;
			MFRC522::MIFARE_Key key;
			
			for (int i = 0; i < 6; i++) 
			{
				key.keyByte[i] = 0xFF;
			}
			int i_data = 32767;
			
			// RFID 자동 제어
			if (readInteger(index, key, i_data) == MFRC522::STATUS_OK) 
			{
				m_is_valid = true;
				Serial.println("[DEBUG] Card is valid!");

				char uidBuffer[20] = {0};
				int offset = 0;
				for (byte i = 0; i < m_card_uid_size; i++) 
				{
					offset += sprintf(uidBuffer + offset, "%02X", m_card_uid[i]);
				}
				createLog("SEN", "RFID_ACCESS", String(uidBuffer));
			} 
			else 
			{
				m_is_valid = false;
				Serial.println("[DEBUG] Card is NOT valid");
				char uidBuffer[20] = {0};
				int offset = 0;
				for (byte i = 0; i < m_card_uid_size; i++) 
				{
					offset += sprintf(uidBuffer + offset, "%02X", m_card_uid[i]);
				}
				createLog("SEN", "RFID_DENY", String(uidBuffer));
			}

			rc522.PICC_HaltA();
			rc522.PCD_StopCrypto1();
		}
		
		// ✅ 카드가 유효하면 문 열기 시작
		if (m_is_valid) 
		{ 
			stepper.moveTo(MOTOR_STEPS * 2);
			doorState = DOOR_OPENING;
			m_open_time = millis();

			Serial.print("[DEBUG] Door opened at: ");
			Serial.println(m_open_time);
			createLog("SEN", "MOTOR", String(1));
			createLog("CMD", "FLOOR", String(1));
			m_is_valid = false;
		}
	}
	// ✅ 상태 2: 문이 열리는 중
	else if (doorState == DOOR_OPENING)
	{
		stepper.run();

		if (!stepper.isRunning()) 
		{
			doorState = DOOR_OPEN;
			m_open_time = millis();
			Serial.println("[DEBUG] Door fully opened");
		}
	}
	// ✅ 상태 3: 문이 열려있는 중 (거리 감지)
	else if (doorState == DOOR_OPEN && (millis() - m_open_time) < 3000)
	{
		long dist = detectDistance();
		
		if (dist != 0 && dist < THRESHOLD) 
		{
			m_is_detected = true;
			m_open_time = millis();  // 타이머 리셋
			Serial.println("[DEBUG] Object detected, door stays open");
			createLog("SEN", "DISTANCE", (String)dist);
		} 
		else 
		{
			m_is_detected = false;
		}
	}
	// ✅ 상태 4: 3초 초과 또는 문 닫기 필요
	else if (doorState == DOOR_OPEN && (millis() - m_open_time) >= 3000)
	{
		Serial.println("[DEBUG] 3 seconds passed, closing door");
		closeDoor();
	}
	// ✅ 상태 5: 문이 닫히는 중
	else if (doorState == DOOR_CLOSING)
	{
		stepper.run();
		
		if (!stepper.isRunning()) 
		{
			doorState = DOOR_IDLE;
			Serial.println("[DEBUG] Door fully closed");
			digitalWrite(STEP_INT4, LOW);
			digitalWrite(STEP_INT2, LOW);
			digitalWrite(STEP_INT3, LOW);
			digitalWrite(STEP_INT1, LOW);
		}
	}

	stepper.run();
}

void Entrance::waitForCard() 
{
	while (true) 
	{
		if (rc522.PICC_IsNewCardPresent() && rc522.PICC_ReadCardSerial()) 
		{
			Serial.println("[DEBUG] {waitForCard} Card detected!");
			m_card_uid_size = rc522.uid.size;
			for (byte i = 0; i < m_card_uid_size; i++) 
			{
				m_card_uid[i] = rc522.uid.uidByte[i];
			}

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
	stepper.moveTo(0);
	doorState = DOOR_CLOSING;

	m_is_detected = false;
	m_is_valid = false;
	
	Serial.println("[DEBUG] Door closing...");
	createLog("SEN", "MOTOR", String(-1));
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

void Entrance::createLog(String dataType, String metricName, String value)
{
	Serial.print(dataType);
	Serial.print(DELIMITER);
	
	Serial.print(metricName);
	Serial.print(DELIMITER);
	Serial.println(value);
}

void Entrance::set_device_id()
{
	uint32_t chipId = 0;
	for (int i = 0; i < 4; i++) {
		chipId |= ((EEPROM.read(i) & 0xFF) << (8 * i));
	}
	
	// 칩 ID가 없으면 생성
	if (chipId == 0 || chipId == 0xFFFFFFFF) {
		chipId = millis() % 1000;
		for (int i = 0; i < 4; i++) {
			EEPROM.write(i, (chipId >> (8 * i)) & 0xFF);
		}
	}
	
	sprintf(m_entrance_device_id, "entrance_device_%03d", chipId % 1000);
}

void Entrance::parseSerialCommand(String command)
{
	int firstDelimiter = command.indexOf(DELIMITER);
	if (firstDelimiter == -1) 
	{
		//Serial.println("[ERROR] Invalid command format");
		return;
	}

	String dataType = command.substring(0, firstDelimiter);
	
	int secondDelimiter = command.indexOf(DELIMITER, firstDelimiter + 1);
	if (secondDelimiter == -1) 
	{
		//Serial.println("[ERROR] Invalid command format");
		return;
	}

	String metricName = command.substring(firstDelimiter + 1, secondDelimiter);
	String value = command.substring(secondDelimiter + 1);

	if (dataType == "CMO") 
	{
		if (metricName == "MOTOR") 
		{
			int action = value.toInt();
			handleMotorCommand(action);
		}
		else 
		{
			//Serial.println("[ERROR] Unknown metric name");
		}
	}
	else 
	{
		//Serial.print("[ERROR] Unknown data type: ");
		//Serial.println(dataType);
	}
}

void Entrance::handleMotorCommand(int action)
{
	if (action == 1) 
	{
		m_is_valid = true;

		Serial.println("ACK,FLOOR,1");
	}
	else if (action == -1)
	{
		m_is_valid = false;

		Serial.println("ACK,FLOOR,-1");
	}
	{
		Serial.print("[ERROR] Invalid action value: ");
		Serial.println(action);
	}
}