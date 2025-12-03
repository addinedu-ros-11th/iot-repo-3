// pin Setting
const int DATA_PIN = 2;   // DS (Serial Data Input)
const int CLOCK_PIN = 3;  // SHCP (Shift Register Clock)
const int LATCH_PIN = 4;  // STCP (Storage Register Clock/Latch)

const int LEDFIRST_PIN = 7;
const int LEDSECOND_PIN = 8;
const int LEDTHIRD_PIN = 9;
const int BUTTONFIRST_PIN = 10;
const int BUTTONSECOND_PIN = 11;
const int BUTTONTHIRD_PIN = 12;

// time/count control
unsigned long previous_time = 0;
unsigned long current_time = 0;
int current_button_state[] = {LOW, LOW, LOW};
int last_button_state[] = {LOW, LOW, LOW};
unsigned long wait_time = 0;

// variables
const int button_pin_arr[] = {BUTTONFIRST_PIN, BUTTONSECOND_PIN, BUTTONTHIRD_PIN};
const int LED_pin_arr[] = {LEDFIRST_PIN, LEDSECOND_PIN, LEDTHIRD_PIN};
const byte ele_LED_pin_arr[] = 
{
  B00000001, 
  B00000010, 
  B00000100, 
  B00001000, 
  B00010000, 
  B00100000, 
  B01000000
};
bool LED_stat[] = {false, false, false};

enum class ElevatorMode {WAIT, UP, DOWN};
ElevatorMode ele_mode = ElevatorMode::WAIT;
int ele_dst[] = {0, 0};
int ele_pos = 0;
byte seven_seg_data_to_display;

void sendElevatorModeToPC(ElevatorMode mode) {
  Serial.print("SEN,ele_dir,");
  if (mode == ElevatorMode::WAIT) {
    Serial.println("0");
  } else if (mode == ElevatorMode::UP) {
    Serial.println("1");
  } else if (mode == ElevatorMode::DOWN) {
    Serial.println("2");
  }
}

// 7-segment display data for numbers 1, 2, 3 (common anode, DP gfedcba)
const byte seven_seg_digits[] = {
  B11111001, // 1 (0층)
  B10100100, // 2 (1층)
  B10110000, // 3 (2층)
};

void updateDisplays(byte ele_led_data, byte seven_seg_data) {
  digitalWrite(LATCH_PIN, LOW);
  // Data for the second register (7-segment) is shifted out first.
  shiftOut(DATA_PIN, CLOCK_PIN, MSBFIRST, seven_seg_data);
  // Data for the first register (elevator LEDs) is shifted out second.
  shiftOut(DATA_PIN, CLOCK_PIN, MSBFIRST, ele_led_data);
  digitalWrite(LATCH_PIN, HIGH);
}

// 변환 함수

int fromFloorToElepos(int floor)
{
  int elepos;
  elepos = floor*3;
  return elepos;
}

int fromEleposeToFloor(int elepos)
{
  int floor;
  floor = elepos/3;
  return floor;
}

void assignEleDst()
{
    int min_req = -1; 
    int max_req = -1; 
    
    for (int i = 0; i < sizeof(LED_stat)/sizeof(LED_stat[0]); i++) 
    {
      if (LED_stat[i] == true) 
      {
        min_req = i;
        break; 
      }
    }

    for (int i = sizeof(LED_stat)/sizeof(LED_stat[0])-1; i >= 0; i--) 
    {
      if (LED_stat[i] == true) 
      {
        max_req = i;
        break; 
      }
    }
    
    if (min_req != -1) // 켜진 LED가 존재 -> destination 설정
    {
      switch (ele_mode)
      {
        case ElevatorMode::UP:
          if (ele_pos <= fromFloorToElepos(max_req))
          {
            ele_dst[1] = max_req;
            ele_dst[0] = min_req;
          }
          else
          {
            if (ele_pos % 3 == 0) max_req = fromEleposeToFloor(ele_pos);
            else max_req = fromEleposeToFloor(ele_pos) + 1;
            ele_dst[1] = max_req;
            ele_dst[0] = min_req;
          }
          break;
        case ElevatorMode::DOWN:
          if (ele_pos >= fromFloorToElepos(min_req))
          {
            ele_dst[0] = min_req;
            ele_dst[1] = max_req;
          }
          else
          {
            min_req = fromEleposeToFloor(ele_pos);
            ele_dst[0] = min_req;
            ele_dst[1] = max_req;
          }
          break;
        case ElevatorMode::WAIT:
          ele_dst[0] = min_req;
          ele_dst[1] = max_req;
          if (ele_pos > fromFloorToElepos(min_req))
          {
            ele_mode = ElevatorMode::DOWN;
            sendElevatorModeToPC(ElevatorMode::DOWN);
          }
          else if (ele_pos < fromFloorToElepos(min_req))
          {
            ele_mode = ElevatorMode::UP;
            sendElevatorModeToPC(ElevatorMode::UP);
          }
          else
            Serial.println("The elevator is already on the floor!");
      }
    } 
    else //다 꺼진 상태 -> 가장 가까운데로 가야됨
    {
      switch (ele_mode)
      {
        case ElevatorMode::UP:
          if (ele_pos % 3 == 0)
          {
            min_req = fromEleposeToFloor(ele_pos);
            max_req = fromEleposeToFloor(ele_pos);
          }
          else
          {
            min_req = fromEleposeToFloor(ele_pos) + 1;
            max_req = fromEleposeToFloor(ele_pos) + 1;
          }
          break;
        case ElevatorMode::DOWN:
          if (ele_pos % 3 == 0)
          {
            min_req = fromEleposeToFloor(ele_pos);
            max_req = fromEleposeToFloor(ele_pos);
          }
          else
          {
            min_req = fromEleposeToFloor(ele_pos) - 1;
            max_req = fromEleposeToFloor(ele_pos) - 1;
          }
          break;
      }
      ele_dst[0] = min_req;
      ele_dst[1] = max_req;
    }
}

void buttonEvent(byte floor)
{
  if (LED_stat[floor] == false)
  {
    digitalWrite(LED_pin_arr[floor], HIGH);
    LED_stat[floor] = true;
    Serial.print("Call at Floor "); Serial.println(floor+1);
  }
  else
  {
    digitalWrite(LED_pin_arr[floor], LOW);
    LED_stat[floor] = false;
    Serial.print("Cancel the Floor "); Serial.println(floor+1);
  }

  assignEleDst();

}

void arriveAtDstUpdateMode()
{

  if (ele_pos % 3 == 0)
  {
    int ele_cur_floor= fromEleposeToFloor(ele_pos);
    if (LED_stat[ele_cur_floor] == true)
    {
      digitalWrite(LED_pin_arr[ele_cur_floor], LOW);
      LED_stat[ele_cur_floor] = false;
      Serial.print("This is floor "); Serial.println(ele_cur_floor+1);
      Serial.println("Door is Opend");
      wait_time = millis() + 5000; 
      Serial.print("ACK,floor,0");
      Serial.println(ele_cur_floor+1);
    }
    
    seven_seg_data_to_display = seven_seg_digits[ele_cur_floor];
    updateDisplays(ele_LED_pin_arr[ele_pos], seven_seg_data_to_display);

    assignEleDst();


    switch (ele_mode)
    {
      case ElevatorMode::WAIT:
        break;

      case ElevatorMode::UP:
        if (ele_cur_floor ==  ele_dst[1])
        {
          if (ele_cur_floor == ele_dst[0])
          {
            ele_mode = ElevatorMode::WAIT;
            Serial.println("Switch Mode : UP -> WAIT");
            sendElevatorModeToPC(ElevatorMode::WAIT);
          }
          else
          {
            ele_mode = ElevatorMode::DOWN;
            Serial.println("Switch Mode : UP -> DOWN");
            sendElevatorModeToPC(ElevatorMode::DOWN);
          }
        }
        break;

      case ElevatorMode::DOWN:
        if (ele_cur_floor ==  ele_dst[0])
        {
          if (ele_cur_floor == ele_dst[1])
          {
            ele_mode = ElevatorMode::WAIT;
            Serial.println("Switch Mode : DOWN -> WAIT");
            sendElevatorModeToPC(ElevatorMode::WAIT);
          }
          else
          {
            ele_mode = ElevatorMode::UP;
            Serial.println("Switch Mode : DOWN -> UP");
            sendElevatorModeToPC(ElevatorMode::UP);
          }
        }
        break;

      default:
        Serial.println("Something wrong: cannot convert elevator mode");
        break;      
    }
  }
}

void updateElePos()
{
  switch (ele_mode)
  {
    case ElevatorMode::WAIT:
      break;
    case ElevatorMode::UP:
      if (ele_pos == 6) // 안전장치
      {
        Serial.println("Arrive at the upper limit but still on the mode of UP");
      }
      else
      {
        ele_pos += 1;
      }
      break;
    case ElevatorMode::DOWN:
      if (ele_pos == 0) // 안전장치
      {
        Serial.println("Arrive at the lower limit but still on the mode of DOWN");
      }
      else
      {
        ele_pos -= 1;
      }
      break;
    default:
      break;
  }
  updateDisplays(ele_LED_pin_arr[ele_pos], seven_seg_data_to_display);
}

void handleSerialCommand() 
{
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    // Split the command string by commas
    int firstComma = command.indexOf(',');
    if (firstComma == -1) return; 

    int secondComma = command.indexOf(',', firstComma + 1);
    if (secondComma == -1) return;

    String cmdType = command.substring(0, firstComma);
    String cmdTarget = command.substring(firstComma + 1, secondComma);
    String cmdValue = command.substring(secondComma + 1);

    if (cmdType == "CMO" && cmdTarget == "floor") 
    {
      int floorNum = cmdValue.toInt();
      if (floorNum >= 1 && floorNum <= 3) 
      {
        int targetFloor = floorNum - 1;
        int currentFloor = fromEleposeToFloor(ele_pos);

        // if the door is open and the call is for the current floor, reset the timer
        if (wait_time != 0 && ele_pos % 3 == 0 && currentFloor == targetFloor) 
        {
          wait_time = millis() + 5000;
          Serial.println("Door wait time has been reset.");
        } 
        // otherwise, if the request light is off, turn it on and assign destination
        else if (LED_stat[targetFloor] == false) 
        {
          digitalWrite(LED_pin_arr[targetFloor], HIGH);
          LED_stat[targetFloor] = true;
          Serial.print("Remote call at Floor "); Serial.println(targetFloor + 1);
          assignEleDst();
        }
      }
    }
  }
}


void setup() {
  Serial.begin(9600);
  pinMode(DATA_PIN, OUTPUT);
  pinMode(CLOCK_PIN, OUTPUT);
  pinMode(LATCH_PIN, OUTPUT);

  pinMode(LEDFIRST_PIN, OUTPUT);
  pinMode(LEDSECOND_PIN, OUTPUT);
  pinMode(LEDTHIRD_PIN, OUTPUT);
  pinMode(BUTTONFIRST_PIN, INPUT);
  pinMode(BUTTONSECOND_PIN, INPUT);
  pinMode(BUTTONTHIRD_PIN, INPUT);

  updateDisplays(ele_LED_pin_arr[ele_pos], seven_seg_digits[fromEleposeToFloor(ele_pos)]);
}

void loop() {
  handleSerialCommand();

  byte button;

  for (int i = 0; i < sizeof(button_pin_arr)/sizeof(button_pin_arr[0]); i++)
  {
    button = digitalRead(button_pin_arr[i]);
    if (button != last_button_state[i])
    {
      if (button == HIGH)
      {
        buttonEvent(i);
        last_button_state[i] = button;
      }
      else
        last_button_state[i] = button;
    }
  }
  
  arriveAtDstUpdateMode();

  current_time = millis();
  if (wait_time != 0) {
    if (current_time >= wait_time) {
      Serial.println("Door is closed");
      wait_time = 0;
    }
  }

  if (wait_time == 0) {
    if (current_time - previous_time > 1000) // 1초마다 엘리베이터 이동
    {
      if (ele_mode != ElevatorMode::WAIT)
      {
        Serial.print("Upper Dst: "); Serial.print(ele_dst[1]+1); Serial.print(" Lower Dst: "); Serial.println(ele_dst[0]+1);
      }
      updateElePos();
      previous_time = current_time;
    }
  }
}