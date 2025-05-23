enum CommandID {
  // Speed
  MOTOR_BOTH_SPEED   = 0x01,
  MOTOR_LEFT_SPEED   = 0x02,
  MOTOR_RIGHT_SPEED  = 0x03,

  // Direction
  MOTOR_DIRECTION    = 0x04,
  CAM_SERVO_VALUE    = 0x05,

  // Sensors
  LINE_SENSOR_LEFT   = 0x0A,
  LINE_SENSOR_MID    = 0x0B,
  LINE_SENSOR_RIGHT  = 0x0C,
  ULTRASONIC_SENSOR  = 0x0D,
  OBSTACLE_DETECTION = 0x0E,

    // Power
  BATTERY_VOLTAGE    = 0x10,
  BATTERY_POWER      = 0x11,
  BATTERY_CURRENT    = 0x12,

  // Other
  TORCH_VALUE       = 0x20,
  EMERGENCY_STOP    = 0xF0,
  COMMAND_PING      = 0xFF
};

void handleTcpipCommand(byte id, byte value) {
  // Serial2.write(0xCC);
  // byte info = createValidCommandInfo(id, value);
  // byte info = id;
  Serial.println(id, HEX);
  // Serial.print(" ");
  
  switch (id) {
    case MOTOR_BOTH_SPEED:
    case MOTOR_LEFT_SPEED:
    case MOTOR_RIGHT_SPEED:
      commandSendSpeed(id, value);
      break;

    case MOTOR_DIRECTION:
      commandSendDir(value);
      break;

    case CAM_SERVO_VALUE:
      commandSendCamServoValue(value);
      break;
    
    case TORCH_VALUE:
      commandSetTorch(value);
      break;

    case COMMAND_PING:
      commandPing();
      break;

    default:
      Serial.print("Nieznane ID komendy: ");
      Serial.println(id);
      return;
}

  // Serial2.write(0x33);
}

void commandSendSpeed(int type, int speed) {
  switch (type) {
    case 0x01:
      sendDataToArduino(type, speed);
      Serial.print("Prędkość M ustawiona na: ");
      // sendBytesToTCPIP(type, speed);
      break;
    case 0x02:
      sendDataToArduino(type, speed);
      Serial.print("Prędkość L ustawiona na: ");
      break;
    case 0x03:
      sendDataToArduino(type, speed);
      Serial.print("Prędkość R ustawiona na: ");
      break;
    default:
      Serial.println("Zła komenda!");
      return;
  }

  Serial.print(speed, BIN);
  Serial.print(" ");
  Serial.println(speed);
}

void commandSendDir(int value) {
  sendDataToArduino(MOTOR_DIRECTION, value);

  Serial.print("Kierunek ustawiony na: ");
  Serial.print(value, BIN);
  Serial.print(" ");
  Serial.println(value);
}

void commandSendCamServoValue(byte value) {
  sendDataToArduino(CAM_SERVO_VALUE, value);

  Serial.print("Kierunek kamery ustawiony na: ");
  Serial.println(value);
}

void commandSetTorch(byte value) {
  Serial.print("Set torch: ");
  Serial.println(value);

  analogWrite(ledPin, value);
  sendBytesToTCPIP(TORCH_VALUE, value);
}

//TODO PIX IT
void commandPing() {
  sendBytesToTCPIP(0xFF, 0x6F);
  Serial.println("PING odebrany – robot działa.");
  Serial.println("FINISH THIS");
}

void sendDataToArduino(byte id, byte data) {
  // byte info = createValidCommandInfo(id, value);
  byte info = id;
  
  Serial2.write(0xCC);
  Serial2.write(info);
  Serial2.write(data);
  Serial2.write(0x33);
}

byte createValidCommandInfo(byte id, byte value) {
  if((id <= 0) || (id >= 128)) {
    Serial.print("Invalid");
    return 0;
  }

  byte numberOfOnes = countOnes(id) + countOnes(value);

  if((numberOfOnes % 2) == 1) {
    id |= 0b10000000;
  } else {
    id &= 0b01111111;
  }

  return id;
}

void receiveDataFromArduino() {
  if (Serial2.available() >= 4) {
    Serial.println("Data! ");

    int startByte = Serial2.read();

    if (startByte != 0xCC){
      Serial.print("Bad first bit: 0x");
      Serial.println(startByte, HEX);
      // Serial.print(" ");
      // Serial.println(startByte, DEC);
      return;
    } else {
      Serial.println("OK first bit");
    }

    int feedbackInfo = Serial2.read();
    int feedbackData = Serial2.read();
    int lastByte     = Serial2.read();

    if (lastByte != 0x33) {
      Serial.print("Bad last bit 0x");
      Serial.println(lastByte, HEX);
      // Serial.print(" ");
      // Serial.println(lastByte, DEC);
      return;
    } else {
      Serial.println("OK last bit");
      handleDataFromArduino(feedbackInfo, feedbackData);
    }
  }
}

void handleDataFromArduino(int idByte, int dataByte) {
  switch(idByte) {
    case EMERGENCY_STOP:
    case MOTOR_BOTH_SPEED:
    case MOTOR_LEFT_SPEED:
    case MOTOR_RIGHT_SPEED:
    case MOTOR_DIRECTION:
    case LINE_SENSOR_LEFT:
    case LINE_SENSOR_MID:
    case LINE_SENSOR_RIGHT:
    case ULTRASONIC_SENSOR:
    case OBSTACLE_DETECTION:
    case BATTERY_VOLTAGE:
    case BATTERY_POWER:
    case BATTERY_CURRENT:
    case CAM_SERVO_VALUE:
    // case COMMAND_PING:
      Serial.print("Arduino zgłasza funckję: ");
      Serial.print(idByte, HEX);
      Serial.print(" [");
      Serial.print(dataByte);
      Serial.println("]");
      
      sendBytesToTCPIP(idByte, dataByte);
      break;

    default:
      Serial.println("Nieznana funkcja");
      break;
  }
}

