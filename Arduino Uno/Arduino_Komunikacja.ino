#include <Servo.h>
#include <SoftwareSerial.h>
#include <Wire.h> // Batery Monitoring Module
#include <Adafruit_INA219.h> // Batery Monitoring Module
#include "TM1651.h" // Battery Display

// Debug led pin
#define LEDpin          13
// Serial to ESP32
#define Serial_RX       11
#define Serial_TX       10
// Camera servo pin
#define servoPin        9
// PWM control pin
#define PWM_Left_PIN    5
#define PWM_Right_PIN   6      
// 74HCT595N chip pin
#define SHCP_PIN        2 // The displacement of the clock
#define EN_PIN          7 // Can make control
#define DATA_PIN        8 // Serial data
#define STCP_PIN        4 // Memory register clock     
// Ultrasonic pin
#define UltrasonicInput 13
#define UltrasonicOutput 12
// LineTrack Sensor
#define LineTrackLeft   A2
#define LineTrackCenter A1
#define LineTrackRight  A0
// Battery Display
#define BatteryCLK A1 
#define BatteryDIO A0

// TM1651 batteryDisplay(BatteryCLK, BatteryDIO);

unsigned long previousMillis[] = {1000, 1500, 1750};
const int numberOfEvents = 3;
const long interval = 5000;

unsigned long lastCommandTimestamp = 0;
const long emergencyStopInterval = 5000;
bool stopForEmergnecy = false;






// TODO use this maybe?????

class Command {
  private:
    byte parityBit;
    byte numberOfOnes;

  byte countOnes(byte variableToCount) {
    byte numberOfOnes = 0;

    while(variableToCount) {
      numberOfOnes += variableToCount & 0b00000001;
      variableToCount >>= 1;
    }

    return numberOfOnes;
  }

  public:
    int info;
    int data; 
    int type;
    bool executed;
    bool validCommand;

    Command() {
      executed = true;
      validCommand = false;
      info = 0;
      data = 0;
      type = 0;
    }

    void parse() {
      // type = info & 0b01111111;
      type = info;
    }

    bool commandvalidation() {
      // parityBit = (info & 0b10000000) >> 7;
      // numberOfOnes = countOnes(info & 0b01111111) + countOnes(data);

      // if((numberOfOnes % 2) == parityBit) {
      //   validCommand = true;
      //   return true;
      // } else {
      //   validCommand = false;
      //   return false;
      // }
      validCommand = true;
      return true;
    }
};

class BatteryMonitor {
  private:
    TM1651* display;
    int maxLevel = 7;
    int currentLevel = 0;
    int currentBrightness = 0;
    unsigned long delay = 500;
    unsigned long timestamp = 0;
                                    // null  red  o1   o2   o3   g1   g2   blue
    const float voltageThresholds[8] = {0.0, 6.0, 6.4, 6.8, 7.2, 7.6, 8.0, 8.4};

  public:
    BatteryMonitor(TM1651* _display, int brightnessLevel) {
      this->display = _display;
      this->currentLevel = 0;
      this->currentBrightness = constrain(brightnessLevel, 0, maxLevel);
      this->timestamp = millis();

      display->init();
      display->set(currentBrightness);
      display->frame(FRAME_OFF);
      display->displayLevel(0);
    }

    void setLevelFromVoltage(float voltage) {
      int batteryLevel = 0;
      for (int i = 0; i < (maxLevel + 1); i++) {
        if (voltage >= voltageThresholds[i]) {
          // Serial.print(i);
          // Serial.print("\t");
          // Serial.print(voltage);
          // Serial.print("\t");
          // Serial.println(voltageThresholds[i]);
          batteryLevel = i;
        } else {
          break;
        }
      }
      setLevel(batteryLevel);
      // Serial.println();
    }

    void setLevel(int batteryLevel) {
      batteryLevel = constrain(batteryLevel, 0, maxLevel);
      display->displayLevel(batteryLevel);
      currentLevel = batteryLevel;
    }

    void setBrightness(int brightnessLevel) {
      display->set(constrain(brightnessLevel, 0, maxLevel));
    }

    void turnON() {
      display->frame(FRAME_ON);
    }

    void turnOFF() {
      display->frame(FRAME_OFF);
    }

    void resetTimestamp() {
      timestamp = millis();
    }

    void chargingAnimation(int minLevel) {
      if ((millis() - timestamp) >= delay) {
        timestamp = millis();
        currentLevel++;

        if (currentLevel > maxLevel) {
          currentLevel = minLevel;
        }

        display->displayLevel(currentLevel);
      }
    }

    void deadbatteryAnimation() {
      if ((millis() - timestamp) >= delay) {
        timestamp = millis();

        if (currentLevel > 0) {
          currentLevel = 0;
        } else {
          currentLevel = 1;
        }

        display->displayLevel(currentLevel);
      }
    }

    void blinkAnimation() {
      if ((millis() - timestamp) >= delay) {
        timestamp = millis();

        if (currentLevel > 0) {
          currentLevel = 0;
        } else {
          currentLevel = maxLevel;
        }

        display->displayLevel(currentLevel);
      }
    }
};

class Chassis {
  private:
    static constexpr int Stop          = 0;   // Stop
    static constexpr int Forward       = 163; // Forward
    static constexpr int Backward      = 92;  // Back
    static constexpr int Left          = 106; // Left translation
    static constexpr int Right         = 149; // Right translation 
    static constexpr int Top_Left      = 34;  // Upper left move
    static constexpr int Bottom_Left   = 72;  // Lower left move
    static constexpr int Top_Right     = 129; // Upper right move
    static constexpr int Bottom_Right  = 20;  // Lower right move
    static constexpr int Turn_Left     = 83;  // Counterclockwise rotation
    static constexpr int Turn_Right    = 172; // Clockwise rotation
    // const int Tank_Left     = -1;  // Counterclockwise tank rotation
    // const int Tank_Right    = -1   // Clockwise tank rotation

    static constexpr int moves[11] = {Stop, Forward, Backward, Left, Right, Top_Left, Bottom_Left, Top_Right, Bottom_Right, Turn_Left, Turn_Right};

  public:
    byte direction;
    byte speedL;
    byte speedR;

  Chassis() {
    direction = 0;
    speedL = 0;
    speedR = 0;
  }

  void setupPins() {
    pinMode(SHCP_PIN, OUTPUT);
    pinMode(EN_PIN, OUTPUT);
    pinMode(DATA_PIN, OUTPUT);
    pinMode(STCP_PIN, OUTPUT);
    pinMode(PWM_Left_PIN, OUTPUT);
    pinMode(PWM_Right_PIN, OUTPUT);
  }

  bool isGoingForward() {
    switch(direction) {
      case Forward:
      case Top_Left:
      case Top_Right:
        return ((speedL > 0) || (speedR > 0));

      case Turn_Left:
        return (speedL > 0);

      case Turn_Right:
        return (speedR > 0);

      default:
        return false;
    };
  }

  void setSpeedM(int newSpeed) {
    speedL = speedR = newSpeed;
  }

  void setSpeedL(int newSpeed) {
    speedL = newSpeed;
  }

  void setSpeedR(int newSpeed) {
    speedR = newSpeed;
  }

  void setDirection(int newDirection) {
    direction = newDirection;
  }

  void MotorsWrite() { 
    digitalWrite(EN_PIN, LOW);
    analogWrite(PWM_Left_PIN,  speedL);
    analogWrite(PWM_Right_PIN, speedR);

    digitalWrite(STCP_PIN, LOW);
    shiftOut(DATA_PIN, SHCP_PIN, MSBFIRST, direction);
    digitalWrite(STCP_PIN, HIGH);
  }

  void MotorsStop() { 
    digitalWrite(EN_PIN, LOW);
    analogWrite(PWM_Left_PIN,  0);
    analogWrite(PWM_Right_PIN, 0);

    digitalWrite(STCP_PIN, LOW);
    shiftOut(DATA_PIN, SHCP_PIN, MSBFIRST, 0);
    digitalWrite(STCP_PIN, HIGH);

    speedL = 0;
    speedR = 0;
    direction = 0;
  }
};

SoftwareSerial mySerial(Serial_RX, Serial_TX); // RX, TX

Servo camServo;

Command receivedCommand;
Chassis chassis;

Adafruit_INA219 batteryMonitoringModule; // I2C adress 40

