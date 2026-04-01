#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <WebServer.h>
#include <MPU9250_asukiaaa.h>

// Настройки
#define SD_CS 5
#define UPDATE_INTERVAL 8 // 125 Гц
#define RECORD_DURATION 600000 // 10 минут в миллисекундах (10 * 60 * 1000)

// Структуры
typedef struct {
  float acc[3];
  float gyro[3];
} SlaveRawData;

struct __attribute__((__packed__)) DataPacket {
  uint8_t header = 0x01;
  double timestamp;
  float acc1[3]; // Master (Thigh)
  float gyro1[3];
  float acc2[3]; // Slave (Shin)
  float gyro2[3];
};

// Переменные
MPU9250_asukiaaa mpu;
SlaveRawData slaveData;
DataPacket currentPacket;
File logFile;
WebServer server(80);

unsigned long lastUpdate = 0;
unsigned long startTime = 0;
bool isRecording = true;

// Callback при получении данных от Slave
void OnDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  if (len == sizeof(SlaveRawData)) {
    memcpy(&slaveData, data, sizeof(SlaveRawData));
  }
}

void startWiFiServer() {
  WiFi.softAP("ESP32_DATA_NODE", "12345678");
  Serial.println("WiFi AP Started: ESP32_DATA_NODE");
  
  server.on("/download", []() {
    File downloadFile = SD.open("/data.bin");
    if (downloadFile) {
      server.streamFile(downloadFile, "application/octet-stream");
      downloadFile.close();
    } else {
      server.send(404, "text/plain", "File Not Found");
    }
  });

  // Маршрут для очистки памяти
  server.on("/delete", []() {
    SD.remove("/data.bin");
    server.send(200, "text/plain", "File Deleted. Restart ESP to record again.");
  });

  server.begin();
}

void setup() {
  Serial.begin(115200);

  // Датчик
  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  // SD карта
  SPI.begin(18, 19, 23, SD_CS);
  if (!SD.begin(SD_CS)) {
    Serial.println("SD FAIL!");
    while(1); 
  }
  SD.remove("/data.bin"); // Удаляем старый файл перед записью
  logFile = SD.open("/data.bin", FILE_WRITE);

  // ESP-NOW
  WiFi.mode(WIFI_AP_STA); // Комбинированный режим
  if (esp_now_init() != ESP_OK) return;
  esp_now_register_recv_cb(OnDataRecv);

  startTime = millis();
  Serial.println("Recording started...");
}

void loop() {
  if (isRecording) {
    unsigned long currentMillis = millis();

    if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
      lastUpdate = currentMillis;

      // Читаем свой датчик
      mpu.accelUpdate();
      mpu.gyroUpdate();

      // Пакуем
      currentPacket.timestamp = (double)currentMillis / 1000.0;
      currentPacket.acc1[0] = mpu.accelX();
      currentPacket.acc1[1] = mpu.accelY();
      currentPacket.acc1[2] = mpu.accelZ();
      currentPacket.gyro1[0] = mpu.gyroX();
      currentPacket.gyro1[1] = mpu.gyroY();
      currentPacket.gyro1[2] = mpu.gyroZ();

      currentPacket.acc2[0] = slaveData.acc[0];
      currentPacket.acc2[1] = slaveData.acc[1];
      currentPacket.acc2[2] = slaveData.acc[2];
      currentPacket.gyro2[0] = slaveData.gyro[0];
      currentPacket.gyro2[1] = slaveData.gyro[1];
      currentPacket.gyro2[2] = slaveData.gyro[2];

      // Пишем на SD
      if (logFile) {
        logFile.write((uint8_t*)&currentPacket, sizeof(currentPacket));
      }

      // Проверка таймера
      if (currentMillis - startTime >= RECORD_DURATION) {
        logFile.close();
        isRecording = false;
        Serial.println("Recording Finished!");
        startWiFiServer();
      }
    }
  } else {
    // В режиме сервера просто слушаем запросы от Flutter
    server.handleClient();
  }
}