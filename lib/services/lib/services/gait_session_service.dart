import 'dart:io';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:path_provider/path_provider.dart';

import '../../api_service.dart';

class GaitSessionService {
  /// Same origin as [ApiService.baseUrl] (remote backend, dart-define, etc.).
  String get backendUrl => ApiService.baseUrl;
  final String esp32Url = 'http://192.168.4.1'; // Default ESP32 AP IP

  static const Map<String, String> _backendJsonHeaders = {
    'ngrok-skip-browser-warning': 'true',
    'Content-Type': 'application/json',
  };
  
  // JWT access token from /api/auth/login-secure
  final String authToken;

  GaitSessionService({required this.authToken});

  /// STEP 1: Tell Python we are starting a new session
  Future<String?> startSessionOnBackend() async {
    final response = await http.post(
      Uri.parse('$backendUrl/sessions/start'),
      headers: {
        ..._backendJsonHeaders,
        'Authorization': 'Bearer $authToken',
      },
      body: jsonEncode({
        'is_baseline': false,
        'notes': 'Uploaded from Flutter app',
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = jsonDecode(response.body);
      return data['session_id']; // Save this!
    }
    print('Failed to start session on backend: ${response.body}');
    return null;
  }

  /// STEP 2: Tell the ESP32 to start recording
  /// (Phone must be connected to ESP32 Wi-Fi for this to work)
  Future<void> startEsp32Recording() async {
    await http.get(Uri.parse('$esp32Url/start'));
  }

  /// STEP 3: Tell the ESP32 to stop recording
  Future<void> stopEsp32Recording() async {
    await http.get(Uri.parse('$esp32Url/stop'));
  }

  /// STEP 4: Download the binary file from ESP32 to the phone
  Future<File?> downloadBinFromEsp32() async {
    final response = await http.get(Uri.parse('$esp32Url/download'));
    
    if (response.statusCode == 200) {
      // Get the phone's temporary directory to store the file
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}/data.bin');
      
      // Write the raw bytes to the phone's storage
      await file.writeAsBytes(response.bodyBytes);
      return file;
    }
    return null;
  }

  /// STEP 5: Upload data file to backend.
  /// Backend contract: POST /api/sessions/{session_id}/upload with multipart field "file"
  Future<bool> uploadBinToBackend({
    required String sessionId,
    required File binFile,
    required String legSide,
    required int sensorSlot,
    String? deviceId,
  }) async {
    final uri = Uri.parse('$backendUrl/api/sessions/$sessionId/upload');
    
    // We use a MultipartRequest to send files in Dart
    final request = http.MultipartRequest('POST', uri)
      ..headers['Authorization'] = 'Bearer $authToken'
      ..headers['ngrok-skip-browser-warning'] = 'true'
      ..files.add(
        await http.MultipartFile.fromPath(
          'file',
          binFile.path,
          filename: 'data.bin',
        ),
      );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200 || response.statusCode == 201 || response.statusCode == 202) {
      print('Upload successful: ${response.body}');
      return true;
    } else {
      print('Upload failed: ${response.body}');
      return false;
    }
  }

  Future<Map<String, dynamic>?> getSession(String sessionId) async {
    final uri = Uri.parse('$backendUrl/api/sessions/$sessionId');
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
  }

  Future<Map<String, dynamic>?> waitForSessionDone(
    String sessionId, {
    int maxAttempts = 12,
    Duration interval = const Duration(seconds: 5),
  }) async {
    for (int i = 0; i < maxAttempts; i++) {
      final session = await getSession(sessionId);
      if (session == null) {
        await Future.delayed(interval);
        continue;
      }

      final status = (session['status'] ?? '').toString().toLowerCase();
      if (status == 'done' || status == 'completed') {
        return session;
      }
      await Future.delayed(interval);
    }
    return null;
  }
}