#ifndef ENTRANCE_H
#define ENTRANCE_H

#include <SPI.h>
#include <MFRC522.h>
#include <Stepper.h>

class Entrance 
{
public:
	enum class EVENT_TYPE
	{
		OPENED, VALID, FAILED, UNKNOWN
	};

private:
	char m_entrance_device_id[50];

	const int RST_PIN = 9;
	const int SS_PIN = 10;
	const int STEP_INT4 = 6;
	const int STEP_INT2 = 3;
	const int STEP_INT3 = 5;
	const int STEP_INT1 = 2;
	const int TRIG = A4;
	const int ECHO = A5;
	const int THRESHOLD = 30;
	const int MOTOR_STEPS = 2048;
	const char DELIMITER = ',';
	const int BUFFER_SIZE = 64;

	MFRC522 rc522;
	Stepper stepper;
	unsigned long m_open_time;
	bool m_is_detected;
	bool m_is_valid;
	byte m_card_uid[10];
	byte m_card_uid_size;
	String m_serial_buffer;

	MFRC522::StatusCode checkAuth(int index, MFRC522::MIFARE_Key key);
	void toBytes(byte* buffer, int data, int offset = 0);
	int toInteger(byte* buffer, int offset = 0);
	long detectDistance();
	const char* eventTypeToString(EVENT_TYPE type);
	void set_device_id();
	void parseSerialCommand(String command);
	void handleMotorCommand(int action);

public:
	Entrance();
	void setup();
	void loop();
	void waitForCard();
	void closeDoor();
	bool getIsValid();
	MFRC522::StatusCode readInteger(int index, MFRC522::MIFARE_Key key, int& data);
	MFRC522::StatusCode writeInteger(int index, MFRC522::MIFARE_Key key, int data);

	void createLog(String dataType, String metricName, float value);
};

#endif