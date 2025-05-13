void setup() {
  Serial.begin(115200);
  Serial.println("Hello World");
  mySerial.begin(9600);

  // pinMode(LEDpin, OUTPUT);
  // digitalWrite(LEDpin, LOW);
  camServo.attach(servoPin);
  chassis.setupPins();
  // ulstrasonicSetupPins();
  // lineTrackSensorSetupPins();

  setAngleOfCamera(90);


  delay(interval);
}

void loop() {
  // Serial.println("Hello ESP!");
  // delay(1000);
  reciveDataFromESP();

  // if(receivedCommand.executed == false) {
  //   receivedCommand.commandvalidation();

  //   if(receivedCommand.validCommand == true) {
  //     Serial.println("Valid data");
  //     receivedCommand.parse();
  //     executeCommand();
  //   } else {
  //     Serial.println("Inalid data");
  //     receivedCommand.executed = true;
  //   }
  // }

  // int distance = obstacleDetection(10);
  // if (distance != 1111 ) {
  //   chassis.MotorsStop();
  //   Serial.println("Obstacle!");
  //   sendDataToESP(OBSTACLE_DETECTION, byte(distance));
  // }

  unsigned long currentMillis = millis();

  for (int n = 0; n < numberOfEvents; n++) {
    if (currentMillis - lastCommandTimestamp >= emergnecyStopInterval) {
      stopRobot();
      sendSpeed();
      Serial.println("EMERGENCY STOP - NO COMMANDS!");
    }

    if (currentMillis - previousMillis[n] >= interval) {
      // Serial.print("Times: ");
      // Serial.print(currentMillis);
      // Serial.print(" ");
      // Serial.print(previousMillis[n]);
      previousMillis[n] += interval;
      // Serial.print(" ");
      // Serial.println(previousMillis[n]);

      switch(n) {
        case 0:
          // Serial.println("Send line sensors");
          sendLineSensors();
          break;
        
        case 1:
          // Serial.println("Send ultrasonic sensor");
          sendUltrasonicSensor();
          break;

        case 2:
          // Serial.println("Send batery voltage");
          sendBateryVoltage();
          break;

        default:
          Serial.print("Bad event number");
          break;
      }
    }
  }
}
