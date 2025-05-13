byte scaleAnalogToByte(int analogValue) {
  // Przeskalowanie z zakresu 0-1023 na 0-255
  byte scaledValue = map(analogValue, 0, 1023, 0, 255);
  return scaledValue;
}

int obstacleDetection(int threshold) {
  if (chassis.isGoingForward() == false) 
    return 1111;
  
  int distance = ultrasonicDistance();

  if (distance <= threshold)
    return distance;

  return 1111;
}
