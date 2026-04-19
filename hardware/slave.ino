#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>
#include <esp_wifi.h> // Важно для настройки канала

#define UPDATE_INTERVAL 8 

MPU9250_asukiaaa mpu;

// Структура данных (один-в-один как у Мастера)
typedef struct {
  float acc[3]; 
  float gyro[3];
} SlaveRawData;

SlaveRawData dataToSend;

// MAC-адрес твоего Мастера (уже проверенный)
uint8_t masterAddress[] = {0xA4, 0xF0, 0x0F, 0x73, 0x92, 0x0C};

unsigned long lastUpdate = 0;

// Исправленная функция обратного вызова
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Доставлено" : "Ошибка");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Инициализация датчика MPU6050/9250
  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  // Настройка WiFi
  WiFi.mode(WIFI_STA);
  
  // --- УСТАНОВКА КАНАЛА (6) ---
  // Твой Мастер выдал Channel 6, поэтому настраиваем Слейв на него
  int32_t channel = 6; 
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);
  // ----------------------------

  if (esp_now_init() != ESP_OK) {
    Serial.println("Ошибка ESP-NOW");
    return;
  }

  // Регистрация функции отправки с исправлением типа (cast)
  esp_now_register_send_cb((esp_now_send_cb_t)OnDataSent);

  // Настройка связи с Мастером
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, masterAddress, 6);
  peerInfo.channel = channel; 
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Ошибка добавления пира");
    return;
  }

  Serial.println("Slave готов! Канал связи: 6");
}

void loop() {
  unsigned long currentMillis = millis();

  // Опрос датчика 125 раз в секунду
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

    // Отправка данных Мастеру по ESP-NOW
    esp_now_send(masterAddress, (uint8_t *)&dataToSend, sizeof(dataToSend));
  }
}