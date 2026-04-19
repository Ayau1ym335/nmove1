import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http_parser/http_parser.dart';

import '../../api_service.dart';

class GaitSessionService {
  /// Same origin as [ApiService.baseUrl] (remote backend, dart-define, etc.).
  String get backendUrl => ApiService.baseUrl;

  static const Map<String, String> _backendJsonHeaders = {
    'ngrok-skip-browser-warning': 'true',
    'Content-Type': 'application/json',
  };

  // JWT access token from /auth/login
  final String authToken;

  GaitSessionService({required this.authToken});

  // ---------------------------------------------------------------------------
  // ESP32 IP resolution
  // ---------------------------------------------------------------------------

  /// Returns the ESP32 IP saved in SharedPreferences.
  /// Falls back to '192.168.43.1' (common Android hotspot range) if not set.
  /// NOTE: 192.168.4.1 was the old SoftAP (access-point) address. Now that
  /// the master connects to the phone hotspot (STA mode) it gets a dynamic IP
  /// assigned by the phone's DHCP — check the Serial Monitor output.
  static Future<String> getEsp32Ip() async {
    final prefs = await SharedPreferences.getInstance();
    return (prefs.getString('esp32_ip') ?? '').trim().isEmpty
        ? '10.172.70.180'
        : prefs.getString('esp32_ip')!.trim();
  }

  static Future<void> saveEsp32Ip(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('esp32_ip', ip.trim());
  }

  // ---------------------------------------------------------------------------
  // STEP 1: Open a new gait session on the backend
  // ---------------------------------------------------------------------------

  /// POST /sessions/start — uses query parameters, NOT a JSON body.
  /// Returns the new session_id string, or null on failure.
Future<String?> startSessionOnBackend({
  String legSide = 'left',
  String? deviceId,
}) async {
  final params = <String, String>{'leg_side': legSide};
  if (deviceId != null && deviceId.trim().isNotEmpty) {
    params['device_id'] = deviceId.trim();
  }

  final uri = Uri.parse('$backendUrl/sessions/start')
      .replace(queryParameters: params);

  try {
    final response = await http.post(
      uri,
      headers: {
        'Authorization': 'Bearer $authToken',
      },
    ).timeout(const Duration(seconds: 15));

    print('=== START SESSION ===');
    print('Status: ${response.statusCode}');
    print('Body: ${response.body}');

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return (data['session_id'] ?? data['id'])?.toString();
    }
    return null;
  } catch (e) {
    print('=== START SESSION EXCEPTION: $e ===');
    return null;
  }
}

  // ---------------------------------------------------------------------------
  // STEP 2: Tell the ESP32 to start recording
  // ---------------------------------------------------------------------------

  /// GET http://<esp32_ip>/start
  /// The phone must be on the same network as the ESP32 (phone hotspot).
  Future<bool> startEsp32Recording() async {
    final ip = await getEsp32Ip();
    try {
      final response = await http
          .get(Uri.parse('http://$ip/start'))
          .timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (e) {
      print('startEsp32Recording error: $e');
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // STEP 3: Tell the ESP32 to stop recording
  // ---------------------------------------------------------------------------

  /// GET http://<esp32_ip>/stop
  Future<bool> stopEsp32Recording() async {
    final ip = await getEsp32Ip();
    try {
      final response = await http
          .get(Uri.parse('http://$ip/stop'))
          .timeout(const Duration(seconds: 8));
      return response.statusCode == 200;
    } catch (e) {
      print('stopEsp32Recording error: $e');
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // STEP 4: Download the binary file from ESP32 to phone storage
  // ---------------------------------------------------------------------------

  /// GET http://<esp32_ip>/download → returns the raw .bin file bytes.
  Future<File?> downloadBinFromEsp32() async {
    final ip = await getEsp32Ip();
    try {
      final response = await http
          .get(Uri.parse('http://$ip/download'))
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200 && response.bodyBytes.isNotEmpty) {
        final dir = await getTemporaryDirectory();
        final file = File('${dir.path}/data.bin');
        await file.writeAsBytes(response.bodyBytes);
        return file;
      }
      print('downloadBinFromEsp32: unexpected response ${response.statusCode}');
      return null;
    } catch (e) {
      print('downloadBinFromEsp32 error: $e');
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // STEP 5: Upload .bin file to the backend
  // ---------------------------------------------------------------------------

  /// POST /api/sessions/ingest/bin — multipart upload.
  /// Field names must match the FastAPI endpoint exactly:
  ///   session_id, leg_side, sensor_slot, device_id, imu_file
Future<bool> uploadBinToBackend({
    required String sessionId,
    required File binFile,
    String legSide = 'left',
    int sensorSlot = 1,
    String? deviceId,
  }) async {
    final uri = Uri.parse('$backendUrl/sessions/ingest/bin');

    final request = http.MultipartRequest('POST', uri)
      ..headers['Authorization'] = 'Bearer $authToken'
      ..headers['ngrok-skip-browser-warning'] = 'true'
      ..fields['session_id'] = sessionId
      ..fields['leg_side'] = legSide

      ..files.add(
        await http.MultipartFile.fromPath(
          'imu_file',
          binFile.path,
          filename: 'data.bin',
        ),
      );

    if (deviceId != null && deviceId.trim().isNotEmpty) {
      request.fields['device_id'] = deviceId.trim();
    }

    try {
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print('=== UPLOAD RESPONSE ===');
      print('Status: ${response.statusCode}');
      print('Body: ${response.body}');
      print('URL: $uri');
      print('Session ID: $sessionId');
      print('File size: ${await binFile.length()} bytes');

      if (response.statusCode == 200 ||
          response.statusCode == 201 ||
          response.statusCode == 202) {
        return true;
      }
      return false;
    } catch (e) {
      print('=== UPLOAD EXCEPTION: $e ===');
      return false;
    }
  } 

  // ---------------------------------------------------------------------------
  // Polling helpers
  // ---------------------------------------------------------------------------

  Future<Map<String, dynamic>?> getSession(String sessionId) async {
  final uri = Uri.parse('$backendUrl/sessions/$sessionId');
    try {
      final response = await http.get(
        uri,
        headers: {
          ..._backendJsonHeaders,
          'Authorization': 'Bearer $authToken',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      print('Failed to fetch session: ${response.statusCode} ${response.body}');
      return null;
    } catch (e) {
      print('getSession error: $e');
      return null;
    }
  }

Future<Map<String, dynamic>?> waitForSessionDone(
  String sessionId, {
  int maxAttempts = 12,
  Duration interval = const Duration(seconds: 5),
}) async {
  for (int i = 0; i < maxAttempts; i++) {
    final session = await getSession(sessionId);
    if (session != null) {
      final status = (session['status'] ?? '').toString().toLowerCase();
      print('=== POLL $i: status=$status ==='); // ← ДОБАВЬ
      print('Keys: ${session.keys.toList()}');   // ← ДОБАВЬ
      if (status == 'done' || status == 'completed') return session;
    }
    await Future.delayed(interval);
  }
  return null;
}
}