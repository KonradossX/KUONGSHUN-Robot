#include <WiFi.h>

#define ledPin 4
#define RXD2 14
#define TXD2 13

// #define RXD2 16
// #define TXD2 17

// TCP/IP server port
WiFiServer server(12345);
WiFiClient activeClient;

void setup() {
  Serial.begin(115200); //Komputer
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2); //Arduino
  
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH);
  delay(200);
  digitalWrite(ledPin, LOW);

  Serial.println("Start");

  connectToWiFi();
  server.begin();
  Serial.println("Serwer TCP uruchomiony!");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Utracono połączenie WiFi. Próba ponownego połączenia...");
    connectToWiFi();

    if (WiFi.status() == WL_CONNECTED) {
      server.begin();
      activeClient.stop();
      Serial.println("Serwer TCP uruchomiony!");
    }

    return;  
  }

  if (checkIfTCPIPisAlive() == false) {
    openTCPIPConnection();
  }

  checkForDataFromTCPIP();

  receiveDataFromArduino();








  delay(10);
}









