#include <WiFi.h>
#include <esp_now.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>

// Частота опроса 125 Гц (1000мс / 125 = 8мс)
#define UPDATE_INTERVAL 8 

MPU9250_asukiaaa mpu;

// Структура данных для отправки (должна быть идентична той, что в Мастере)
typedef struct {
  float acc[3];  // x, y, z
  float gyro[3]; // x, y, z
} SlaveRawData;

SlaveRawData dataToSend;

// Твой проверенный MAC-адрес Мастер-модуля
uint8_t masterAddress[] = {0xA4, 0xF0, 0x0F, 0x73, 0x92, 0x0C};

unsigned long lastUpdate = 0;

// Callback для проверки статуса отправки (опционально, для отладки)
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Если хочешь видеть в мониторе порта, доходят ли данные:
  // Serial.print("Send status: ");
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Fail");
}

void setup() {
  Serial.begin(115200);

  // Инициализация I2C для датчика MPU9250
  Wire.begin(21, 22);
  mpu.setWire(&Wire);
  mpu.beginAccel();
  mpu.beginGyro();

  // Настройка Wi-Fi в режиме станции
  WiFi.mode(WIFI_STA);
  
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error ESP-NOW Init");
    return;
  }

  // Регистрируем функцию обратного вызова для статуса отправки
  esp_now_register_send_cb(OnDataSent);

  // Добавляем Мастера в список пиров (получателей)
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, masterAddress, 6);
  peerInfo.channel = 0; // Использовать текущий канал Wi-Fi
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }

  Serial.println("Slave Ready: Sending Raw IMU to Master A4:F0:0F:73:92:0C");
}

void loop() {
  unsigned long currentMillis = millis();

  // Основной цикл сбора и отправки данных (125 Гц)
  if (currentMillis - lastUpdate >= UPDATE_INTERVAL) {
    lastUpdate = currentMillis;

    // Считываем свежие данные с MPU9250
    mpu.accelUpdate();
    mpu.gyroUpdate();

    // Записываем данные акселерометра
    dataToSend.acc[0] = mpu.accelX();
    dataToSend.acc[1] = mpu.accelY();
    dataToSend.acc[2] = mpu.accelZ();

    // Записываем данные гироскопа
    dataToSend.gyro[0] = mpu.gyroX();
    dataToSend.gyro[1] = mpu.gyroY();
    dataToSend.gyro[2] = mpu.gyroZ();

    // Отправляем структуру Мастеру
    esp_now_send(masterAddress, (uint8_t *)&dataToSend, sizeof(dataToSend));
  }
}