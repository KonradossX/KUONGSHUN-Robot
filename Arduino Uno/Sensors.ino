void ulstrasonicSetupPins() {
  pinMode(UltrasonicInput,  INPUT);
  pinMode(UltrasonicOutput, OUTPUT);
}

int ultrasonicDistance() {
  digitalWrite(UltrasonicOutput, LOW);
  delayMicroseconds(2);
  digitalWrite(UltrasonicOutput, HIGH);
  delayMicroseconds(10);
  digitalWrite(UltrasonicOutput, LOW);

  // float distance = pulseIn(UltrasonicIn, HIGH) / 58.00;
  float distance = pulseIn(UltrasonicInput, HIGH) * 0.01715;

  Serial.print("Distance: ");
  Serial.println(distance);

  if ((distance < 2) || (distance > 200)) {
    Serial.println("UBD");
  }
  
  return int(round(distance));
}

void lineTrackSensorSetupPins() {
  pinMode(LineTrackLeft,   INPUT);
  pinMode(LineTrackCenter, INPUT);
  pinMode(LineTrackRight,  INPUT);
}

int* lineTrackingCheckAnalog() {
  static int valuesArray[3];

  valuesArray[0] = analogRead(LineTrackLeft);
  valuesArray[1] = analogRead(LineTrackCenter);
  valuesArray[2] = analogRead(LineTrackRight);

  return valuesArray; 
}

byte lineTrackSensorDigital() {
  int threshold = 128;
  int* analogValuesArray = lineTrackingCheckAnalog();
  // bool boolValuesArray[3];
  byte byteValue = 0;

  for (byte i = 0; i < 3; i++) {
    // boolValuesArray[i] = (analogValuesArray[i] > threshold);
    // byteValue |= (boolValuesArray[i] << i);
    byteValue |= ((analogValuesArray[i] > threshold) << i);
  }

  // return boolValuesArray;
  return byteValue;
}

float readBateryVoltage() { 
  //Pamietaj ze analogRead() daje liczbe z zakresu 0-1023
  // float voltage = 7.6;
  float shuntVoltage  = batteryMonitoringModule.getShuntVoltage_mV();
  float busVoltage = batteryMonitoringModule.getBusVoltage_V();

  return busVoltage + (shuntVoltage * 0.001);
}

float readBatteryPower() {
  return batteryMonitoringModule.getPower_mW();
}

float readBatteryCurrent() {
  return batteryMonitoringModule.getCurrent_mA();
}




