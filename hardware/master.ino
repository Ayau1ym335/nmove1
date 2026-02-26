#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <MPU9250_asukiaaa.h>

#define SD_CS 5
#define UPDATE_INTERVAL 8 // 125 Hz (1000/125)

MPU9250_asukiaaa mpu;

typedef struct {
  float acc[3];
  float gyro[3];
} SlaveRawData;

SlaveRawData slaveData;
bool newDataFromSlave = false;

struct __attribute__((__packed__)) DataPacket {
  uint8_t header = 0x01;       // Тип калибровки (обычная)
  double timestamp;            // f8 (8 bytes)
  float acc1[3];               // f4, (3,) - Бедро (Thigh)
  float gyro1[3];              // f4, (3,)
  float acc2[3];               // f4, (3,) - Голень (Shin)
  float gyro2[3];              // f4, (3,)
};

DataPacket currentPacket;
File logFile;
unsigned long lastUpdate = 0;

void OnDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  if (len == sizeof(SlaveRawData)) {
    memcpy(&slaveData, data, sizeof(SlaveRawData));
    newDataFromSlave = true;
  }
}

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
  esp_now_register_recv_cb(OnDataRecv);

  SPI.begin(18, 19, 23, SD_CS);
  if (SD.begin(SD_CS)) {
    logFile = SD.open("/data.bin", FILE_APPEND); // Запись в бинарном виде
    if (logFile) Serial.println("SD READY (Binary Log)");
  } else {
    Serial.println("SD NOT FOUND");
  }

  Serial.println("Master System Started (125Hz)");
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    mpu.accelUpdate();
    mpu.gyroUpdate();

    currentPacket.timestamp = (double)currentMillis / 1000.0;
    

    currentPacket.acc2[0] = slaveData.acc[0];
    currentPacket.acc2[1] = slaveData.acc[1];
    currentPacket.acc2[2] = slaveData.acc[2];
    currentPacket.gyro2[0] = slaveData.gyro[0];
    currentPacket.gyro2[1] = slaveData.gyro[1];
    currentPacket.gyro2[2] = slaveData.gyro[2];

    Serial.write((uint8_t*)&currentPacket, sizeof(currentPacket));
    
    if (logFile) {
      logFile.write((uint8_t*)&currentPacket, sizeof(currentPacket));
      if (currentMillis % 1000 < 10) logFile.flush();
    }
  }
}