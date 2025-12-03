// 28BYJ-48 스텝모터와 LDR(조도센서) 기반 자동 커튼 제어
#include <Stepper.h>

class CurtainController {
public:
  CurtainController(
    int motorPin1,
    int motorPin2,
    int motorPin3,
    int motorPin4,
    int lightSensorPin,
    int lightThreshold,
    long fullOpenSteps,
    int motorRpm
  )
    : stepsPerRevolution(2048),
      stepper(stepsPerRevolution, motorPin1, motorPin2, motorPin3, motorPin4),
      ldrPin(lightSensorPin),
      threshold(lightThreshold),
      curtainMaxSteps(fullOpenSteps),
      currentStep(0),
      motorDirection(0),
      lastTelemetryTime(0),
      motorSpeedRpm(motorRpm),
        controlMode(MODE_AUTO),
      commandIndex(0) {
  }

  void begin() {
    Serial.begin(9600);
    pinMode(ldrPin, INPUT);
    stepper.setSpeed(motorSpeedRpm);
  }

  void update() {
    processSerialInput();

    unsigned long now = millis();
    if (now - lastTelemetryTime >= 3000) {
      int lightValue = analogRead(ldrPin);
      lastTelemetryTime = now;
      emitTelemetry(lightValue);
      if (controlMode == MODE_AUTO) {
        applyAutoLogic(lightValue);
      }
    }

    if (motorDirection == 1 && currentStep < curtainMaxSteps) {
      stepper.setSpeed(motorSpeedRpm);
      stepper.step(1);
      currentStep++;
    } else if (motorDirection == -1 && currentStep > 0) {
      stepper.setSpeed(motorSpeedRpm);
      stepper.step(-1);
      currentStep--;
    }

    if ((motorDirection == 1 && currentStep >= curtainMaxSteps) ||
        (motorDirection == -1 && currentStep <= 0)) {
      sendError("LIMIT");
      motorDirection = 0;
    }

    delay(5);
  }

private:
  enum ControlMode { MODE_AUTO, MODE_MANUAL };

  void processSerialInput() {
    while (Serial.available()) {
      char incoming = Serial.read();
      if (incoming == '\r') {
        continue;
      }
      if (incoming == '\n') {
        if (commandIndex > 0) {
          commandBuffer[commandIndex] = '\0';
          handleFrame(String(commandBuffer));
          commandIndex = 0;
        }
        continue;
      }

      if (commandIndex < sizeof(commandBuffer) - 1) {
        commandBuffer[commandIndex++] = incoming;
      }
    }
  }

  void handleFrame(const String& frameRaw) {
    String frame = frameRaw;
    frame.trim();
    int firstComma = frame.indexOf(',');
    if (firstComma == -1) {
      sendError("FORMAT");
      return;
    }

    String typeToken = frame.substring(0, firstComma);
    typeToken.trim();
    typeToken.toUpperCase();
    if (typeToken != "CMO") {
      return;  // only handle PC-originated commands
    }

    int secondComma = frame.indexOf(',', firstComma + 1);
    if (secondComma == -1) {
      sendError("FORMAT");
      return;
    }

    String metric = frame.substring(firstComma + 1, secondComma);
    metric.trim();
    String value = frame.substring(secondComma + 1);
    value.trim();
    if (metric.length() == 0 || value.length() == 0) {
      sendError("FORMAT");
      return;
    }

    String metricUpper = metric;
    metricUpper.toUpperCase();
    String valueUpper = value;
    valueUpper.toUpperCase();

    if (metricUpper == "MOTOR") {
      handleMotorCommand(valueUpper);
    } else if (metricUpper == "MODE") {
      handleModeCommand(valueUpper);
    } else {
      sendError("UNKNOWN");
    }
  }

  void handleMotorCommand(const String& valueUpper) {
    controlMode = MODE_MANUAL;

    if (valueUpper == "OPEN") {
      if (setMotorDirection(1)) {
        sendAck("MOTOR", "OPEN");
      }
    } else if (valueUpper == "CLOSE") {
      if (setMotorDirection(-1)) {
        sendAck("MOTOR", "CLOSE");
      }
    } else if (valueUpper == "STOP") {
      setMotorDirection(0);
      sendAck("MOTOR", "STOP");
    } else {
      sendError("UNKNOWN");
    }
  }

  void handleModeCommand(const String& valueUpper) {
    if (valueUpper == "AUTO") {
      controlMode = MODE_AUTO;
      setMotorDirection(0);
    } else if (valueUpper == "MANUAL") {
      controlMode = MODE_MANUAL;
      setMotorDirection(0);
    } else {
      sendError("UNKNOWN");
    }
  }

  void emitTelemetry(int lightValue) {
    sendFrame("SEN", "LIGHT", String(lightValue));
    sendFrame("SEN", "CUR_STEP", currentStep);
    sendFrame("SEN", "MOTOR_DIR", motorDirection);
  }

  void applyAutoLogic(int lightValue) {
    if (lightValue > threshold && currentStep < curtainMaxSteps) {
      motorDirection = 1;
    } else if (lightValue < threshold && currentStep > 0) {
      motorDirection = -1;
    } else {
      motorDirection = 0;
    }
  }

  bool setMotorDirection(int direction) {
    if (direction > 0 && currentStep >= curtainMaxSteps) {
      motorDirection = 0;
      sendError("LIMIT");
      return false;
    }
    if (direction < 0 && currentStep <= 0) {
      motorDirection = 0;
      sendError("LIMIT");
      return false;
    }

    motorDirection = direction;
    return true;
  }

  void sendFrame(const char* dataType, const char* metric, const String& value) {
    Serial.print(dataType);
    Serial.print(",");
    Serial.print(metric);
    Serial.print(",");
    Serial.println(value);
  }

  void sendFrame(const char* dataType, const char* metric, long value) {
    Serial.print(dataType);
    Serial.print(",");
    Serial.print(metric);
    Serial.print(",");
    Serial.println(value);
  }

  void sendAck(const char* metric, const String& value) {
    sendFrame("ACK", metric, value);
  }

  void sendError(const char* code) {
    sendFrame("ACK", "ERROR", String(code));
  }

  const int stepsPerRevolution;
  Stepper stepper;

  const int ldrPin;
  int threshold;
  const long curtainMaxSteps;

  long currentStep;
  int motorDirection;
  unsigned long lastTelemetryTime;
  int motorSpeedRpm;

  ControlMode controlMode;

  char commandBuffer[64];
  size_t commandIndex;
};

CurtainController curtainController(
  8,
  10,
  9,
  11,
  A0,
  500,
  1.3L * 2048,
  20
);

void setup() {
  curtainController.begin();
}

void loop() {
  curtainController.update();
}