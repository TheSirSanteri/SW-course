#include <WiFi.h>

// WiFi credentials
const char* ssid = "Santeri's Galaxy A53 5G";     // Replace with your WiFi SSID
const char* password = "santerisanteri"; // Replace with your WiFi password

// Server details (your computer's IP and port)
const char* serverIP = "10.40.18.206";  // Replace with your computer's local IP/ the IP after your computer connect to the hotspot
const int serverPort = 5001;  // Must match the server Python script

const int sensorPins[] = {D0, D1, D2, D3, D4, D5, D8, D9, D10};
const char* sensorNames[] = {"D0", "D1", "D2", "D3", "D4", "D5", "D8", "D9", "D10"};
const int sensorCount = sizeof(sensorPins) / sizeof(sensorPins[0]);

WiFiClient client;

void connectToServer() {
    Serial.print("Connecting to server...");
    while (!client.connect(serverIP, serverPort)) {
        Serial.print(".");
        delay(1000);
    }
    Serial.println("Connected to server!");
}

void setup() {
    Serial.begin(115200);

    Serial.print("Connecting to WiFi...");
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
    }

    Serial.println("");
    Serial.println("Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    // ESP32: analogRead toimii ilman pinModea, mutta tämä tekee tarkoituksen selväksi.
    for (int i = 0; i < sensorCount; i++) {
        pinMode(sensorPins[i], INPUT);
    }

    connectToServer();
}

void loop() {
    if (!client.connected()) {
        Serial.println("Disconnected, reconnecting...");
        client.stop();
        delay(2000);
        connectToServer();
        return;
    }

    String data = "";

    for (int i = 0; i < sensorCount; i++) {
        int rawValue = analogRead(sensorPins[i]);
        float voltage = rawValue * (3.3 / 4095.0);

        // Lähetetään raakadata; myöhemmin voit vaihtaa jännitteisiin, jos haluat.
        data += String(rawValue);
        if (i < sensorCount - 1) {
            data += ",";
        }

        Serial.print(sensorNames[i]);
        Serial.print(": raw=");
        Serial.print(rawValue);
        Serial.print(" voltage=");
        Serial.print(voltage, 3);
        Serial.print(" V\t");
    }
    Serial.println();

    data += "\n";
    client.print(data);
    Serial.print("Sent: ");
    Serial.print(data);

    delay(100);
}