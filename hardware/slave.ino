#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>
#include <esp_wifi.h>

#define UPDATE_INTERVAL 8 

MPU9250_asukiaaa mpu;

// Структура данных (должна быть такая же как на Мастере)
typedef struct {
  float acc[3]; 
  float gyro[3];
} SlaveRawData;

SlaveRawData dataToSend;

// MAC-адрес твоего Мастера (уже вписан твой)
uint8_t masterAddress[] = {0xA4, 0xF0, 0x0F, 0x73, 0x92, 0x0C};

unsigned long lastUpdate = 0;

// Исправленный коллбэк для статуса отправки
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Ok" : "Fail");
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Инициализация I2C (MPU6050)
  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  // Настройка WiFi
  WiFi.mode(WIFI_STA);
  
  // ВНИМАНИЕ: Если Мастер в мониторе порта напишет Channel, отличный от 1, 
  // измени эту цифру здесь!
  int32_t channel = 1; 
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous(false);

  if (esp_now_init() != ESP_OK) {
    Serial.println("Error ESP-NOW");
    return;
  }

  // Регистрация коллбэка с приведением типа
  esp_now_register_send_cb((esp_now_send_cb_t)OnDataSent);

  // Добавляем Мастера в список пиров
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, masterAddress, 6);
  peerInfo.channel = channel; 
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Peer Error");
    return;
  }

  Serial.println("Slave Ready!");
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    // Считываем данные с датчика
    mpu.accelUpdate();
    mpu.gyroUpdate();

    dataToSend.acc[0] = mpu.accelX();
    dataToSend.acc[1] = mpu.accelY();
    dataToSend.acc[2] = mpu.accelZ();

    dataToSend.gyro[0] = mpu.gyroX();
    dataToSend.gyro[1] = mpu.gyroY();
    dataToSend.gyro[2] = mpu.gyroZ();

    // Отправляем
    esp_now_send(masterAddress, (uint8_t *)&dataToSend, sizeof(dataToSend));
  }
}