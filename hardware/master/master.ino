#include <WiFi.h>
#include <WebServer.h> 
#include <esp_now.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <MPU9250_asukiaaa.h>
#include <time.h> 
#include <WebSocketsServer.h>

#define SD_CS 5
#define UPDATE_INTERVAL 8 
#define LED_PIN 2

const char* ssid = "Ayau"; 
const char* password = "XYZQWERTY";  

WebServer server(80); 
WebSocketsServer webSocket = WebSocketsServer(81);
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

// --- ОБРАБОТЧИКИ SD ---
void handleStart() { 
  SD.remove("/data.bin"); 
  logFile = SD.open("/data.bin", FILE_WRITE); 
  if (!logFile) { server.send(500, "text/plain", "SD ERROR"); return; }
  isRecording = true; 
  server.send(200, "text/plain", "STARTED"); 
}

void handleStop() { 
  isRecording = false; 
  if (logFile) { logFile.flush(); logFile.close(); }
  server.send(200, "text/plain", "STOPPED"); 
}

void handleDownload() { 
  File file = SD.open("/data.bin", FILE_READ);
  if (!file || file.size() == 0) { server.send(404, "text/plain", "NO FILE"); return; }
  server.streamFile(file, "application/octet-stream");
  file.close();
}

void OnDataRecv(const uint8_t * mac, const uint8_t *data, int len) {
  if (len >= sizeof(SlaveRawData)) {
    memcpy(&slaveData, data, sizeof(SlaveRawData));
    digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Мигаем при приеме от Слейва
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  SPI.begin(18, 19, 23, SD_CS);
  SD.begin(SD_CS);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  
  // Синхронизация времени
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  struct tm timeinfo;
  while (!getLocalTime(&timeinfo)) { delay(500); Serial.print("."); }
  Serial.println("\nTime Synced!");

  if (esp_now_init() != ESP_OK) Serial.println("ESP-NOW Error");
  esp_now_register_recv_cb((esp_now_recv_cb_t)OnDataRecv);

  server.on("/start", handleStart);
  server.on("/stop", handleStop);
  server.on("/download", handleDownload);
  server.begin();
  webSocket.begin();
}

void loop() {
  server.handleClient();
  webSocket.loop();

  unsigned long currentMillis = millis();
  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    mpu.accelUpdate();
    mpu.gyroUpdate();

    // ЗАПОЛНЯЕМ ВСЕ ДАННЫЕ
    currentPacket.timestamp = (double)time(NULL); 
    
    // Данные Мастера (Бедро)
    currentPacket.acc1[0] = mpu.accelX();
    currentPacket.acc1[1] = mpu.accelY();
    currentPacket.acc1[2] = mpu.accelZ();
    currentPacket.gyro1[0] = mpu.gyroX();
    currentPacket.gyro1[1] = mpu.gyroY();
    currentPacket.gyro1[2] = mpu.gyroZ();

    // Данные Слейва (Голень)
    currentPacket.acc2[0] = slaveData.acc[0];
    currentPacket.acc2[1] = slaveData.acc[1];
    currentPacket.acc2[2] = slaveData.acc[2];
    currentPacket.gyro2[0] = slaveData.gyro[0];
    currentPacket.gyro2[1] = slaveData.gyro[1];
    currentPacket.gyro2[2] = slaveData.gyro[2];

    // Запись на SD для бэкенда
    if (isRecording && logFile) {
      logFile.write((uint8_t*)&currentPacket, sizeof(currentPacket));
    }

    // Отправка во Flutter для графиков
    String dataStr = String(currentPacket.acc1[0], 2) + "," + String(currentPacket.acc1[1], 2) + "," + String(currentPacket.acc1[2], 2) + "|" +
                     String(currentPacket.acc2[0], 2) + "," + String(currentPacket.acc2[1], 2) + "," + String(currentPacket.acc2[2], 2);
    webSocket.broadcastTXT(dataStr);
  }
}