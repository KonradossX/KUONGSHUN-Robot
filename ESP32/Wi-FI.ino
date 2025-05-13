void connectToWiFi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(900);
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    Serial.print(".");
  }

  Serial.println("\nPołączono z Wi-Fi!");
  Serial.print("Adres IP ESP32: ");
  Serial.println(WiFi.localIP());
}

bool openTCPIPConnection() {
  activeClient = server.accept();

  if (activeClient) {
    Serial.println("Klient połączony!");
    return true;
  } else {
    Serial.println("Problem z połączeniem");
    return false;
  }
}

bool checkIfTCPIPisAlive() {
  if (!activeClient || !activeClient.connected()) {
    closeTCPConnection();
    return false;
  } else {
    return true;
  }
}

void closeTCPConnection() {
  if (activeClient) {
    activeClient.stop();
    Serial.println("Klient rozłączony.");
  }
}

void checkForDataFromTCPIP() {
  if (checkIfTCPIPisAlive() == false) return;

  if (activeClient.available() >= 4) { 
    // Serial.println("New data");
    digitalWrite(ledPin, HIGH);

    byte firstByte = activeClient.read();
    if (firstByte != 0xCC) {
      digitalWrite(ledPin, LOW);
      return;
    }

    byte commandID    = activeClient.read(); 
    byte commandValue = activeClient.read(); 
    byte lastByte     = activeClient.read();

    if (lastByte == 0x33) {
      digitalWrite(ledPin, LOW);
      handleTcpipCommand(commandID, commandValue);
      return;
    }

    // sendTextToTCPIP("ACK");
    digitalWrite(ledPin, LOW);
  }
}

void sendBytesToTCPIP(byte firstByte, byte secondByte) {
  if (checkIfTCPIPisAlive() == false) return;
  
  activeClient.write(0xCC);
  activeClient.write(firstByte);
  activeClient.write(secondByte);
  activeClient.write(0x33);
}

void sendTextToTCPIP(const String& text) {
  if (checkIfTCPIPisAlive() == false) return;

  activeClient.println(text);
}
