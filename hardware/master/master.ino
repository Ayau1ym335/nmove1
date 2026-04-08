#include <WiFi.h>
#include <WebServer.h> 
#include <esp_now.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <MPU9250_asukiaaa.h>

#define SD_CS 5
#define UPDATE_INTERVAL 8 

const char* ssid = "NMove_Master_Knee"; 
const char* password = "";               
WebServer server(80); 
MPU9250_asukiaaa mpu;

typedef struct {
  float acc[3];
  float gyro[3];
} SlaveRawData;

SlaveRawData slaveData;

struct __attribute__((__packed__)) DataPacket {
  uint8_t header = 0x01;
  double timestamp;
  float acc1[3]; 
  float gyro1[3];
  float acc2[3]; 
  float gyro2[3];
};

DataPacket currentPacket;
File logFile;
unsigned long lastUpdate = 0;
bool isRecording = false;

// --- ОБРАБОТЧИКИ СЕРВЕРА ---

void handleStart() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  SD.remove("/data.bin");
  logFile = SD.open("/data.bin", FILE_WRITE);
  if (logFile) {
    isRecording = true;
    server.send(200, "text/plain", "RECORDING_STARTED");
    Serial.println("Recording started...");
  } else {
    server.send(500, "text/plain", "SD_ERROR");
    Serial.println("Failed to open file for writing");
  }
}

void handleStop() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  isRecording = false;
  if (logFile) {
    logFile.close();
  }
  server.send(200, "text/plain", "RECORDING_STOPPED");
  Serial.println("Recording stopped.");
}

void handleDownload() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "*");

  if (isRecording) {
    server.send(400, "text/plain", "STOP_RECORDING_FIRST");
    return;
  }
  
  File file = SD.open("/data.bin", FILE_READ);
  if (!file) {
    server.send(404, "text/plain", "FILE_NOT_FOUND");
    return;
  }

  server.streamFile(file, "application/octet-stream");
  file.close();
  Serial.println("File sent successfully");
}

void handleOptions() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "*");
  server.send(204);
}

void OnDataRecv(const esp_now_recv_info *info, const uint8_t *data, int len) {
  if (len >= sizeof(SlaveRawData)) {
    memcpy(&slaveData, data, sizeof(SlaveRawData));
  }
}

// --- SETUP ---

void setup() {
  Serial.begin(115200);

  // Инициализация I2C и MPU
  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  // Инициализация SD-карты
  SPI.begin(18, 19, 23, SD_CS);
  if (!SD.begin(SD_CS)) {
    Serial.println("CRITICAL: SD Card Error!");
  } else {
    Serial.println("SD Card OK.");
  }

  // Настройка Wi-Fi
  WiFi.softAP(ssid, password);
  Serial.print("AP IP address: ");
  Serial.println(WiFi.softAPIP()); 

  // Настройка ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
  }
  esp_now_register_recv_cb((esp_now_recv_cb_t)OnDataRecv);

  // Настройка путей сервера
  server.on("/start", HTTP_GET, handleStart);
  server.on("/stop", HTTP_GET, handleStop);
  server.on("/download", HTTP_GET, handleDownload);
  server.on("/download", HTTP_OPTIONS, handleOptions); // Важно для Flutter Web/Chrome

  server.begin();
  Serial.println("HTTP Server started");
}

// --- LOOP ---

void loop() {
  server.handleClient(); 

  unsigned long currentMillis = millis();
  
  // Чтение и запись данных каждые 8мс
  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    if (isRecording && logFile) {
      mpu.accelUpdate();
      mpu.gyroUpdate();

      currentPacket.timestamp = (double)currentMillis / 1000.0;
      
      // Данные с локального MPU
      currentPacket.acc1[0] = mpu.accelX();
      currentPacket.acc1[1] = mpu.accelY();
      currentPacket.acc1[2] = mpu.accelZ();
      currentPacket.gyro1[0] = mpu.gyroX();
      currentPacket.gyro1[1] = mpu.gyroY();
      currentPacket.gyro1[2] = mpu.gyroZ();

      // Данные со второго датчика (Slave) через ESP-NOW
      currentPacket.acc2[0] = slaveData.acc[0];
      currentPacket.acc2[1] = slaveData.acc[1];
      currentPacket.acc2[2] = slaveData.acc[2];
      currentPacket.gyro2[0] = slaveData.gyro[0];
      currentPacket.gyro2[1] = slaveData.gyro[1];
      currentPacket.gyro2[2] = slaveData.gyro[2];

      // Запись бинарного пакета
      logFile.write((uint8_t*)&currentPacket, sizeof(currentPacket));
      
      // Сброс данных на карту раз в секунду, чтобы не потерять при сбое
      if (currentMillis % 1000 < 10) {
        logFile.flush();
      }
    }
  }
}
