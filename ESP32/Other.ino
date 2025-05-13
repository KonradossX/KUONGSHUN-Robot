byte countOnes(byte variableToCount) {
  byte numberOfOnes = 0;

  while(variableToCount) {
    numberOfOnes += variableToCount & 0b00000001;
    variableToCount >>= 1;
  }

  return numberOfOnes;
}