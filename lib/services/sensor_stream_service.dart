import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';

/// Service for handling real-time data from ESP32 sensors via WebSocket.
class KneeSensorService {
  WebSocketChannel? _channel;
  bool isConnected = false;

  // The IP address of your ESP32 from the Serial Monitor.
  // Ensure your phone and ESP32 are on the same Wi-Fi network.
  final String _url = 'ws://10.172.70.180:81'; 

  // Notifier to update the UI in real-time without calling setState.
  final ValueNotifier<String> sensorDataNotifier = ValueNotifier("Waiting for data...");
double masterBattery = 100.0;
  double slaveBattery = 100.0;
  /// Establishes connection to the ESP32 WebSocket server.
  void connect() {
    try {
      debugPrint("Connecting to WebSocket: $_url");
      _channel = IOWebSocketChannel.connect(Uri.parse(_url));
      isConnected = true;

      // Start listening to the incoming stream from ESP32.
      _channel!.stream.listen(
        (message) {
          _parseData(message.toString());
        },
        onError: (error) {
          isConnected = false;
          sensorDataNotifier.value = "Connection Error: $error";
          debugPrint("WebSocket Error: $error");
        },
        onDone: () {
          isConnected = false;
          sensorDataNotifier.value = "Disconnected";
          debugPrint("WebSocket connection closed.");
        },
      );
    } catch (e) {
      isConnected = false;
      sensorDataNotifier.value = "Failed to connect";
      debugPrint("Connection exception: $e");
    }
  }

  /// Parses the raw string data from ESP32.
  /// Format expected: "M:ax,ay,az|S:ax,ay,az"
  void _parseData(String data) {
    // 1. Update the notifier with raw data for UI display.
    sensorDataNotifier.value = data; 

    try {
      // Basic validation: ensure the message contains expected delimiters.
      if (!data.contains('|') || !data.contains(':')) return;

      List<String> parts = data.split('|');
      
      // Parse Master (Thigh) data - removing "M:" prefix.
      String masterClean = parts[0].replaceAll('M:', '');
      List<double> masterValues = masterClean.split(',').map((e) => double.tryParse(e.trim()) ?? 0.0).toList();
      masterBattery = masterValues.length > 3 ? masterValues[3] : 99.0;
      // Parse Slave (Shank) data - removing "S:" prefix.
      String slaveClean = parts[1].replaceAll('S:', '');
      List<double> slaveValues = slaveClean.split(',').map((e) => double.tryParse(e.trim()) ?? 0.0).toList();
slaveBattery = slaveValues.length > 3 ? slaveValues[3] : 98.0;

      // Для отладки в консоли
      debugPrint("Master Battery: $masterBattery%, Slave Battery: $slaveBattery%");
      // Debug output for calculations.
      debugPrint("Thigh Accel: $masterValues");
      debugPrint("Shank Accel: $slaveValues");
      
      // TODO: Integrate Madgwick Filter here.
      // madgwickFilter.update(masterAcc, slaveAcc);
      
    } catch (e) {
      debugPrint("Parsing Error: $e | Raw Data: $data");
    }
  }

  /// Closes the WebSocket connection.
  void disconnect() {
    _channel?.sink.close();
    isConnected = false;
    sensorDataNotifier.value = "Status: Disconnected";
    debugPrint("Disconnected from sensor.");
  }
}