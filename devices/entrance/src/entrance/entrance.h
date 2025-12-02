#ifndef ENTRANCE_H
#define ENTRANCE_H

#include <SPI.h>
#include <MFRC522.h>
#include <Stepper.h>

class Entrance 
{
private:
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

	MFRC522 rc522;
	Stepper stepper;
	unsigned long open_time;
	bool is_detected;
	bool is_valid;

	MFRC522::StatusCode checkAuth(int index, MFRC522::MIFARE_Key key);
	void toBytes(byte* buffer, int data, int offset = 0);
	int toInteger(byte* buffer, int offset = 0);
	long detectDistance();

public:
	Entrance();
	void setup();
	void loop();
	void waitForCard();
	void closeDoor();
	MFRC522::StatusCode readInteger(int index, MFRC522::MIFARE_Key key, int& data);
	MFRC522::StatusCode writeInteger(int index, MFRC522::MIFARE_Key key, int data);
};

#endif