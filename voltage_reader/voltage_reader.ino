#include <WiFi.h>

// WiFi credentials
const char* ssid = "Santeri's Galaxy A53 5G";     // Replace with your WiFi SSID
const char* password = "santerisanteri"; // Replace with your WiFi password

// Server details (your computer's IP and port)
const char* serverIP = "10.225.28.206";  // Replace with your computer's local IP/ the IP after your computer connect to the hotspot
const int serverPort = 5001;  // Must match the server Python script

int sensorPin1 = A5;
int sensorValue1 = 0;
//const int buttonPin = 2;

WiFiClient client;

void setup() {
    Serial.begin(115200);
    // comment when no serial
    // while (!Serial); 

    // 1. start connection
    Serial.print("Connecting to WiFi...");
    WiFi.begin(ssid, password); 

    // 2. check status
    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
    }
    
    Serial.println("");
    Serial.println("Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    // Connect to the server
    Serial.print("Connecting to server...");
    while (!client.connect(serverIP, serverPort)) {
        Serial.print(".");
        delay(1000);
    }
    Serial.println("Connected to server!");
}

void loop() {
    if (client.connected()) {
        sensorValue1 = analogRead(sensorPin1);  // Read from a sensor (adjust as needed)
        // int test_value = digitalRead(buttonPin);
        
        /*
        String data = String(sensorValue1) + ",";  // Convert to string，typo in previous version code
        client.print(data);  // Send data
        Serial.print("Sent: ");
        Serial.println(data);
        */
        float voltage = sensorValue1 * (3.3 / 4095.0);


        Serial.print("Raw Reading: ");
        Serial.print(sensorValue1);
        Serial.print("\t Voltage: ");
        Serial.print(voltage); 
        Serial.println(" V");
        delay(100);  // Adjust sending rate/frequency
    } else {
        Serial.println("Disconnected, reconnecting...");
        client.stop();
        delay(2000);
        client.connect(serverIP, serverPort);
    }
}