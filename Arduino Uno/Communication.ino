// enum CommandID {
//   // Speed
//   MOTOR_BOTH_SPEED   = 0x01,
//   MOTOR_LEFT_SPEED   = 0x02,
//   MOTOR_RIGHT_SPEED  = 0x03,

//   // Direction
//   MOTOR_DIRECTION    = 0x04,
//   CAM_SERVO_VALUE    = 0x05,

//   // Sensors
//   LINE_SENSOR_LEFT   = 0x0A,
//   LINE_SENSOR_MID    = 0x0B,
//   LINE_SENSOR_RIGHT  = 0x0C,
//   ULTRASONIC_SENSOR  = 0x0D,
//   OBSTACLE_DETECTION = 0x0E,
//   BATTERY_VOLTAGE    = 0x0F,

//   // Other
//   COMMAND_PING      = 0xFF
// };

void reciveDataFromESP() {
  if(mySerial.available() >= 4) {
    lastCommandTimestamp = millis();
    
    Serial.print("Data! ");
    Serial.println(mySerial.available());

    // digitalWrite(LEDpin, HIGH);
    // delay(100);
    // digitalWrite(LEDpin, LOW);
    // delay(100);
    // digitalWrite(LEDpin, HIGH);

    int startByte = mySerial.read();

    if (startByte != 0xCC){
      Serial.print("Bad first bit: 0x");
      Serial.print(startByte, HEX);
      Serial.print(" ");
      Serial.println(startByte, DEC);
      // digitalWrite(LEDpin, LOW);
      return;
    } else {
      Serial.println("OK first bit");
    }

    int commandInfo = mySerial.read();
    int commandData = mySerial.read();
    int lastByte    = mySerial.read();

    if (lastByte != 0x33) {
      Serial.print("Bad last bit 0x");
      Serial.print(lastByte, HEX);
      Serial.print(" ");
      Serial.println(lastByte, DEC);

      // digitalWrite(LEDpin, LOW);
      return;
    } else {
      Serial.println("OK last bit");
    }

    if (commandInfo != -1 && commandData != -1) {
      executeCommand(commandInfo, commandData);  
      
      // receivedCommand.info = commandInfo;
      // receivedCommand.data = commandData;

      // Serial.print("cmd info: 0x");

      // Serial.print(commandInfo & 0b01111111, HEX);
      // Serial.print(" ");
      // Serial.print(commandInfo & 0b01111111, BIN);
      // Serial.print(" ");
      // Serial.println(commandInfo & 0b01111111, DEC);

      // Serial.print(commandInfo, HEX);
      // Serial.print(" ");
      // Serial.print(commandInfo, BIN);
      // Serial.print(" ");
      // Serial.println(commandInfo, DEC);

      // Serial.print("cmd data: 0x");
      // Serial.print(commandData, HEX);
      // Serial.print(" ");
      // Serial.print(commandData, BIN);
      // Serial.print(" ");
      // Serial.println(commandData, DEC);
      // receivedCommand.executed = false;
    } else {
      Serial.println("Bad commands: -1");
    }

    delay(250);
    // digitalWrite(LEDpin, LOW);

    // Serial.println(commandInfo);
  } 
}

// #define infoObstacleDetected 15

void sendDataToESP(byte id, byte data) {
    // byte info = createValidCommandInfo(id, value);
  byte info = id;
  
  mySerial.write(0xCC);
  mySerial.write(info);
  mySerial.write(data);
  mySerial.write(0x33);
}

byte createValidFeedbackInfo(byte id, byte value) {
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

byte countOnes(byte variableToCount) {
  byte numberOfOnes = 0;

  while(variableToCount) {
    numberOfOnes += variableToCount & 0b00000001;
    variableToCount >>= 1;
  }

  return numberOfOnes;
}

void sendSpeed() {
  if (chassis.speedL == chassis.speedR) {
    sendDataToESP(MOTOR_BOTH_SPEED,  chassis.speedL);
  } else {
    sendDataToESP(MOTOR_LEFT_SPEED,  chassis.speedL);
    sendDataToESP(MOTOR_RIGHT_SPEED, chassis.speedR);
  }
}

void sendDirection() {
  sendDataToESP(MOTOR_DIRECTION, chassis.direction);
}

void sendCamServoValue(byte value) {
  sendDataToESP(CAM_SERVO_VALUE, value);
}

void sendLineSensors() {
  int* valuesArray = lineTrackingCheckAnalog();

  sendDataToESP(LINE_SENSOR_LEFT,  scaleAnalogToByte(valuesArray[0]));
  sendDataToESP(LINE_SENSOR_MID,   scaleAnalogToByte(valuesArray[1]));
  sendDataToESP(LINE_SENSOR_RIGHT, scaleAnalogToByte(valuesArray[2]));
}

void sendUltrasonicSensor() {
  // int distance = ultrasonicDistance()
  sendDataToESP(ULTRASONIC_SENSOR, byte(ultrasonicDistance()));
}

void sendBateryVoltage() {
  float voltage = readBateryVoltage();
  byte voltageByte = byte(round(voltage * 100) - 585); //0 = 5.85V, 255 = 8.40V

  if (voltageByte < 0) 
    voltageByte = 0;

  if (voltageByte > 255)
    voltageByte = 255;

  sendDataToESP(BATTERY_VOLTAGE, voltageByte);
}