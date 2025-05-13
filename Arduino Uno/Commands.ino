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
  BATTERY_VOLTAGE    = 0x0F,

  // Other
  COMMAND_PING      = 0xFF
};

void executeCommand(int commandInfo, int commandData) {  
  bool executed = false;
  Serial.print("Command: ");
  // Serial.println(receivedCommand.type);
  Serial.println(commandInfo);

  // switch(receivedCommand.type) {
  switch (commandInfo) {
    case MOTOR_BOTH_SPEED:
      // executed = setSpeed(0, receivedCommand.data);
      executed = setSpeed(0, commandData);
      break;

    case MOTOR_LEFT_SPEED:
      // executed = setSpeed(1, receivedCommand.data);
      executed = setSpeed(1, commandData);
      break;

    case MOTOR_RIGHT_SPEED:
      // executed = setSpeed(2, receivedCommand.data);
      executed = setSpeed(2, commandData);
      break;

    case CAM_SERVO_VALUE:
      executed = setAngleOfCamera(commandData);
      // executed = setAngleOfCamera(90);
      // delay(500);
      // executed = setAngleOfCamera(45);
      break;

    // case 11:
    //   executed = cameraSwing();
    //   break;

    case MOTOR_DIRECTION:
      // executed = setDirection(receivedCommand.data);
      executed = setDirection(commandData);
      break;

    // case 14:
    //   executed = stopRobot();
    //   break;

    default:
      executed = commandUnknown();
      break;
  }

  if (executed == false) {
    commandUnknown();
  }

  // receivedCommand.executed = executed;
  // receivedCommand.executed = true;
}

bool commandUnknown() {
  // for(int i = 0; i < 5; i++) {
  //   digitalWrite(LEDpin, HIGH);
  //   delay(100);
  //   digitalWrite(LEDpin, LOW);
  //   delay(100);
  // }

  Serial.print("Command unknow");
  return true;
}

bool setAngleOfCamera(int angle) {
  camServo.write(angle);
  sendCamServoValue(angle);
  return true;
}

bool cameraSwing() {
  camServo.write(0);
  delay(1000);
  camServo.write(180);
  delay(1000);
  camServo.write(90);
  return true;
}

bool setDirection(byte direction) {
  //TODO valid direction
  chassis.direction = direction;
  chassis.MotorsWrite();
  return true;
}

bool setSpeed(byte n, byte speed) {
  if((speed < 0) || (speed > 255)) 
    return false;

  if (n == 0)
    chassis.setSpeedM(speed);
  else if (n == 1) 
    chassis.setSpeedL(speed);
  else if (n == 2)
    chassis.setSpeedR(speed);
  else
    return false;

  chassis.MotorsWrite();
  return true;
}

bool stopRobot() {
  chassis.MotorsStop();
  return true;
}

