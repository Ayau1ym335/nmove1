#include <WiFi.h>
#include <WebServer.h> 
#include <esp_now.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <MPU9250_asukiaaa.h>
#include <time.h>

#define SD_CS 5
#define UPDATE_INTERVAL 8 

const char* ssid = "Ayau"; 
const char* password = "XYZQWERTY";  

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

// If unix time is less than this, assume NTP did not sync yet.
// 1600000000 ~= 2020-09-13T12:26:40Z
const long MIN_UNIX_TIME = 1600000000;

void syncNtpTime() {
  // Use system timezone offset = 0 (UTC) since backend expects UTC timestamps.
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");

  time_t now = time(nullptr);
  Serial.print("Syncing NTP");
  int retries = 0;
  while (now < MIN_UNIX_TIME && retries < 30) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
    retries++;
  }
  Serial.println();

  if (now >= MIN_UNIX_TIME) {
    Serial.print("Unix time: ");
    Serial.println((long)now);
  } else {
    Serial.println("NTP sync failed: time not set");
  }
}

// --- ОБРАБОТЧИКИ СЕРВЕРА ---

void handleStart() {
  server.sendHeader("Access-Control-Allow-Origin", "*");

  // Ensure we have a real unix timestamp before we start logging.
  time_t now = time(nullptr);
  if (now < MIN_UNIX_TIME) {
    Serial.println("Time not synced yet; running NTP sync on /start");
    syncNtpTime();
  }

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

  // *** ПОДКЛЮЧЕНИЕ К ХОТСПОТУ ТЕЛЕФОНА (вместо softAP) ***
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Подключаюсь к хотспоту");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nПодключено!");
    Serial.print("IP адрес ESP32: ");
    Serial.println(WiFi.localIP()); // <-- этот IP вводишь в приложении

    // NTP sync over the phone hotspot connection.
    syncNtpTime();
  } else {
    Serial.println("\nНе удалось подключиться к хотспоту!");
  }

  // Настройка ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
  }
  esp_now_register_recv_cb((esp_now_recv_cb_t)OnDataRecv);

  // Настройка путей сервера
  server.on("/start", HTTP_GET, handleStart);
  server.on("/stop", HTTP_GET, handleStop);
  server.on("/download", HTTP_GET, handleDownload);
  server.on("/download", HTTP_OPTIONS, handleOptions);

  server.begin();
  Serial.println("HTTP Server started");
}

// --- LOOP ---

void loop() {
  server.handleClient(); 

  unsigned long currentMillis = millis();
 
  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    if (isRecording && logFile) {
      mpu.accelUpdate();
      mpu.gyroUpdate();

      // Timestamp is unix epoch seconds (UTC) so backend ingestion can validate it.
      currentPacket.timestamp = (double)time(nullptr);
      
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

      logFile.write((uint8_t*)&currentPacket, sizeof(currentPacket));
      
      if (currentMillis % 1000 < 10) {
        logFile.flush();
      }
    }
  }
}

