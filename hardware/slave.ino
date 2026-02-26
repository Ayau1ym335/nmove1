#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>

#define UPDATE_INTERVAL 8 // 125 Гц (1000мс / 125)

MPU9250_asukiaaa mpu;

typedef struct {
  float acc[3];  // x, y, z
  float gyro[3]; // x, y, z
} SlaveRawData;

SlaveRawData dataToSend;

uint8_t masterAddress[] = {0xA4, 0xF0, 0x0F, 0x73, 0x92, 0x0C};

unsigned long lastUpdate = 0;

void setup() {
  Serial.begin(115200);

  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, masterAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }

  Serial.println("Slave Ready: Sending Raw IMU data...");
  delay(2000); 
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    mpu.accelUpdate();
    mpu.gyroUpdate();
    dataToSend.acc[0] = mpu.accelX();
    dataToSend.acc[1] = mpu.accelY();
    dataToSend.acc[2] = mpu.accelZ();

    dataToSend.gyro[0] = mpu.gyroX();
    dataToSend.gyro[1] = mpu.gyroY();
    dataToSend.gyro[2] = mpu.gyroZ();

    esp_err_t result = esp_now_send(masterAddress, (uint8_t *)&dataToSend, sizeof(dataToSend));
    
        if (result != ESP_OK) {
      // Serial.println("Error sending data");
    }
  }
}
