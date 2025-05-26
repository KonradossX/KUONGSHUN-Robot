# KUONGSHUN-Robot

# Current status: Robot Remote Control via Keyboard

This project enables remote control of a robot using a computer keyboard, built on a multi-layered communication system between a computer, ESP32, and Arduino Uno.

## Communication Architecture

- **Computer ↔ ESP32**:  
  Communication over **TCP/IP via Wi-Fi**, connected to an existing network (ESP32 acts as a Wi-Fi client).

- **ESP32 ↔ Arduino Uno**:  
  Communication over **UART**.

## Features

- ✅ Basic communication verification (simple handshake; start/stop byts, to be improved)  
- 🧭 Multiple predefined movement patterns:  
  - Sideways  
  - Diagonal  
  - Spin in place
  - etc

- ⚙️ Speed control:  
  - Separate control of left and right side (limited by hardware)  
  - Independent direction control for each motor via keyboard

- 💡 LED control  
- 🔧 Servo control  
- 📡 Sensor updates from Arduino:  
  - Ultrasonic distance sensor  
  - Line-following sensor  
  - Battery status from INA219 module

## To Do / Improvements

- [ ] Enhance communication reliability and error handling  
- [x] Add real battery monitoring module  
- [ ] Add simple autonomy (like stopping on obstacle)




