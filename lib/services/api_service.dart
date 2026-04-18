import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/walking_session.dart';


class ApiService {
static String get baseUrl {
    const fromEnv = String.fromEnvironment('API_BASE_URL');
    if (fromEnv.isNotEmpty) return fromEnv;
    return 'https://api-production-5697.up.railway.app';
  }

static Map<String, String> get _jsonHeaders => {
      'Content-Type': 'application/json',
    };

static Future<Map<String, String>> _authHeaders() async {
  final token = await _token();
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $token',
  };
}

static Future<Map<String, String>> _authHeadersPlain() async {
  final token = await _token();
  return {
    'Authorization': 'Bearer $token',
  };
}

  static Future<String> _token() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token') ?? '';
  }


  /// POST /auth/register
  /// Returns the role string on success, throws on failure.
  static Future<void> register({
    required String email,
    required String password,
    required String fullName,
    String role = 'patient',
    String? city,
    String? gender,
    String? age,
    String? weight,
    String? height,
    String? dominantLeg,
    String? shoeSize,
    String? legLength,
  }) async {
    final payload = <String, dynamic>{
      'email': email.trim().toLowerCase(),
      'password': password,
      'role': role,
      'full_name': fullName.trim().isEmpty ? 'User' : fullName.trim(),
      'profile': {
        'age': int.tryParse((age ?? '').trim()) ?? 25,
        'gender': (gender?.toLowerCase() == 'male') ? 'male' : 'female',
        'weight': double.tryParse((weight ?? '').trim()) ?? 70.0,
        'height': double.tryParse((height ?? '').trim()) ?? 175.0,
        'nationality': 'Kazakh',
        'have_injury': false,
        'have_banomaly': false,
        'banomaly': null,
        'shoe_size': double.tryParse((shoeSize ?? '').trim()) ?? 38.0,
        'leg_length': double.tryParse((legLength ?? '').trim()) ?? 90.0,
        'dominant_leg': (dominantLeg?.toLowerCase() == 'left') ? 'left' : 'right',
        'lifestyle': 'active',
        'smoke': false,
        'alcohol': false,
        'notes': (city?.trim().isNotEmpty == true) ? city!.trim() : 'no notes',
      },
    };

final response = await http.post(
      Uri.parse('$baseUrl/auth/register'), // Убедись, что путь верен
      headers: _jsonHeaders, // БЕЗ токена для регистрации
      body: jsonEncode(payload),
    );

    if (response.statusCode == 200 || response.statusCode == 201) return;
    // 409 = already exists — treat as non-fatal
    if (response.statusCode == 409) return;
    final body = response.body.toLowerCase();
    if (response.statusCode == 400 &&
        (body.contains('already') || body.contains('exist') || body.contains('registered'))) {
      return;
    }
    throw Exception('Registration failed: ${response.statusCode} ${response.body}');
  }

  /// POST /auth/login
  /// Persists tokens + role. Returns the role string or throws on error.
  static Future<String> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'email': email.trim().toLowerCase(),
        'password': password,
      }),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final prefs = await SharedPreferences.getInstance();

      final accessToken = (data['access_token'] ?? '').toString();
      final refreshToken = (data['refresh_token'] ?? '').toString();
      final role = (data['role'] ?? 'patient').toString();

      if (accessToken.isNotEmpty) await prefs.setString('access_token', accessToken);
      if (refreshToken.isNotEmpty) await prefs.setString('refresh_token', refreshToken);
      await prefs.setString('user_role', role);
      await prefs.setString('user_email', email.trim().toLowerCase());

      return role;
    }
    throw Exception('Login failed: ${response.statusCode} ${response.body}');
  }

  /// GET /auth/me — returns the currently authenticated user.
  static Future<Map<String, dynamic>> getMe() async {
    final headers = await _authHeadersPlain();
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('GET /auth/me failed: ${response.statusCode}');
  }

  /// POST /auth/refresh — rotate refresh token, issue new access + refresh pair.
  /// No Authorization header needed — refresh token IS the credential.
  static Future<void> refreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    final refresh = prefs.getString('refresh_token') ?? '';
    if (refresh.isEmpty) throw Exception('No refresh token stored');

    final response = await http.post(
      Uri.parse('$baseUrl/auth/refresh'),
      headers: _jsonHeaders,
      body: jsonEncode({'refresh_token': refresh}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final newAccess = (data['access_token'] ?? '').toString();
      final newRefresh = (data['refresh_token'] ?? '').toString();
      if (newAccess.isNotEmpty) await prefs.setString('access_token', newAccess);
      if (newRefresh.isNotEmpty) await prefs.setString('refresh_token', newRefresh);
      return;
    }
    throw Exception('Token refresh failed: ${response.statusCode}');
  }

  /// POST /auth/logout — requires Bearer JWT + refresh token in body.
  /// Idempotent: calling twice both returns 200.
  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    final refresh = prefs.getString('refresh_token') ?? '';
    try {
      final headers = await _authHeaders();
      await http.post(
        Uri.parse('$baseUrl/auth/logout'),
        headers: headers,
        body: jsonEncode({'refresh_token': refresh}),
      );
    } catch (_) {
      // Always clear local tokens regardless of network result
    } finally {
      await prefs.remove('access_token');
      await prefs.remove('refresh_token');
      await prefs.remove('user_role');
      await prefs.remove('user_email');
    }
  }

  // ─────────────────────────────────────────────
  // Sessions
  // ─────────────────────────────────────────────

  /// POST /sessions/start
  /// Backend returns 201 with empty body {}.
  /// After starting, call [getMySessions] to get the new session_id.
static Future<String> startSession({String legSide = 'left', String? deviceId}) async {
    final params = {'leg_side': legSide};
    if (deviceId != null) params['device_id'] = deviceId;
    
    final uri = Uri.parse('$baseUrl/sessions/start').replace(queryParameters: params);
    final response = await http.post(uri, headers: await _authHeadersPlain());

    if (response.statusCode == 201 || response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['id'] ?? data['session_id']).toString();
    }
    throw Exception('Failed to start session');
  }

  static Future<void> closeSession(String sessionId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/sessions/$sessionId/close'),
      headers: await _authHeadersPlain(),
    );
    if (response.statusCode != 200) throw Exception('Failed to close session');
  }
  /// POST /sessions/start — convenience wrapper that also fetches the created session.
  /// Returns the most recent session from /sessions/me after starting.
  static Future<Map<String, dynamic>> startSessionAndFetch({
    String legSide = 'left',
    String? deviceId,
  }) async {
    await startSession(legSide: legSide, deviceId: deviceId);
    final sessions = await getMySessions();
    if (sessions.isNotEmpty) return sessions.first as Map<String, dynamic>;
    throw Exception('Session started but no session found in /sessions/me');
  }

  /// POST /sessions/{session_id}/close
  /// Returns 200 with empty body {}.

  /// GET /sessions/me
  /// Returns full paginated response:
  /// { patient_id, sessions[], total, page, page_size, has_more }
  static Future<Map<String, dynamic>> getMySessionsPaginated({
    int page = 1,
    int pageSize = 20,
  }) async {
    final headers = await _authHeadersPlain();
    final uri = Uri.parse('$baseUrl/sessions/me').replace(queryParameters: {
      'page': '$page',
      'page_size': '$pageSize',
    });
    final response = await http.get(uri, headers: headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('GET /sessions/me failed: ${response.statusCode}');
  }

  /// Convenience wrapper — returns only the sessions list.
  static Future<List<dynamic>> getMySessions() async {
    final data = await getMySessionsPaginated();
    return (data['sessions'] as List<dynamic>?) ?? [];
  }

  /// GET /sessions/{session_id}
static Future<Map<String, dynamic>> getSessionById(String sessionId) async {
    final headers = await _authHeadersPlain();
    final response = await http.get(
      Uri.parse('$baseUrl/api/sessions/$sessionId'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('GET /api/sessions/$sessionId failed: ${response.statusCode}');
  }

  /// GET /sessions/doctor/patients/{patient_id}
  /// Returns full paginated response.
  static Future<Map<String, dynamic>> getDoctorPatientSessions(
    String patientId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    final headers = await _authHeadersPlain();
    final uri = Uri.parse('$baseUrl/sessions/doctor/patients/$patientId')
        .replace(queryParameters: {'page': '$page', 'page_size': '$pageSize'});
    final response = await http.get(uri, headers: headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('GET /sessions/doctor/patients/$patientId failed: ${response.statusCode}');
  }

  /// PATCH /sessions/{session_id}/status
  /// Returns { session_id, previous_status, new_status, updated_at, message }.
  static Future<Map<String, dynamic>> updateSessionStatus(
    String sessionId,
    String status, {
    String? errorMessage,
  }) async {
    final headers = await _authHeaders();
    final body = <String, dynamic>{'status': status};
    if (errorMessage != null && errorMessage.isNotEmpty) {
      body['error_message'] = errorMessage;
    }
    final response = await http.patch(
      Uri.parse('$baseUrl/sessions/$sessionId/status'),
      headers: headers,
      body: jsonEncode(body),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('PATCH /sessions/$sessionId/status failed: ${response.statusCode}');
  }

  /// POST /sessions/{session_id}/assign-doctor
  /// No body needed — assigns the current doctor from JWT.
  /// Returns the updated session object.
  static Future<Map<String, dynamic>> assignDoctorToSession(String sessionId) async {
    if (sessionId.isEmpty) throw ArgumentError('sessionId must not be empty');
    final headers = await _authHeadersPlain();
    final response = await http.post(
      Uri.parse('$baseUrl/sessions/$sessionId/assign-doctor'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('POST /sessions/$sessionId/assign-doctor failed: ${response.statusCode}');
  }

  /// POST /sessions/ingest — ingest JSON readings.
  /// Payload: { session_id, device_id, readings: [{timestamp, ax, ay, az, gx, gy, gz, ...}] }
  static Future<Map<String, dynamic>> ingestSessionJson(
    Map<String, dynamic> payload,
  ) async {
    final headers = await _authHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/sessions/ingest'),
      headers: headers,
      body: jsonEncode(payload),
    );
    if (response.statusCode == 200 || response.statusCode == 202) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('POST /sessions/ingest failed: ${response.statusCode} ${response.body}');
  }

  /// POST /sessions/ingest/bin — upload binary IMU file.
  /// Returns 202 with { accepted, session_id, first_timestamp, last_timestamp, warnings, ingested_at, task_id }.
static Future<Map<String, dynamic>> uploadSessionBin(
    String sessionId,
    List<int> bytes, {
    String legSide = 'left',
    int sensorSlot = 1,
    String? deviceId,
  }) async {
    final token = await _token();
    
    // Используем MultipartRequest для передачи файла и полей
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/sessions/ingest/bin'),
    );

    // Заголовки
    request.headers.addAll({
      'Authorization': 'Bearer $token',
    });

    // Текстовые поля формы
    request.fields['session_id'] = sessionId;
    request.fields['leg_side'] = legSide;
    request.fields['sensor_slot'] = '$sensorSlot';
    if (deviceId != null && deviceId.trim().isNotEmpty) {
      request.fields['device_id'] = deviceId.trim();
    }

    // Сам файл (важно: имя 'imu_file' должно совпадать с названием в FastAPI)
    request.files.add(
      http.MultipartFile.fromBytes(
        'imu_file', 
        bytes, 
        filename: 'data_${DateTime.now().millisecondsSinceEpoch}.bin',
      ),
    );

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode == 202 || response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('POST /api/sessions/ingest/bin failed: ${response.statusCode} ${response.body}');
  }
static Future<Map<String, dynamic>> getDashboardSummary(String userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/$userId/summary'),
      headers: await _authHeadersPlain(),
    );
    if (response.statusCode == 200) return jsonDecode(response.body);
    throw Exception('Failed to get dashboard summary');
  }

  /// GET /trends/{user_id}
  /// [days] must be one of: 7, 30, 90 (default 30).
  /// [metrics] defaults to ['movement_age', 'symmetry_score', 'stability_score'].
static Future<Map<String, dynamic>> getTrends(
  String userId, {
  int days = 30,
  List<String> metrics = const ['movement_age', 'symmetry_score', 'stability_score'],
}) async {
  final headers = await _authHeadersPlain();
  
  // Создаем базовый URI
  final baseUrlUri = Uri.parse('$baseUrl/trends/$userId');
  
  // FastAPI требует повторения ключа для списков: ?metrics=age&metrics=symmetry
  // Поэтому мы создаем строку запроса вручную или через вспомогательный метод
  final queryParams = <String, String>{'days': '$days'};
  
  // Добавляем метрики вручную в строку, так как стандартный .replace не дублирует ключи так, как нужно FastAPI
  String queryString = Uri(queryParameters: queryParams).query;
  for (var metric in metrics) {
    queryString += '&metrics=$metric';
  }

  final finalUri = Uri.parse('$baseUrl/trends/$userId?$queryString');

  final response = await http.get(finalUri, headers: headers);
  if (response.statusCode == 200) {
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
  throw Exception('GET /trends/$userId failed: ${response.statusCode}');
}

  /// GET /doctor/patients
  /// Returns full response: { doctor_id, patients[], total, page, page_size, has_more,
  ///   cached, total_concern, total_attention, total_normal, total_no_data }
static Future<Map<String, dynamic>> getDoctorPatients({
  String sort = 'last_seen',
  String order = 'desc',
  int page = 1,
  int pageSize = 20,
  String? status,
  String? search,
}) async {
  final headers = await _authHeadersPlain();
  final params = <String, String>{
    'sort': sort,
    'order': order,
    'page': '$page',
    'page_size': '$pageSize',
  };
  
  if (status != null && status.isNotEmpty) params['status'] = status;
  if (search != null && search.isNotEmpty) params['search'] = search;

  final uri = Uri.parse('$baseUrl/doctor/patients').replace(queryParameters: params);
  final response = await http.get(uri, headers: headers);
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
  throw Exception('GET /doctor/patients failed: ${response.statusCode}');
}
  /// Convenience wrapper — returns only the patients list.
  static Future<List<dynamic>> getDoctorPatientList({
    String sort = 'last_seen',
    String order = 'desc',
    int page = 1,
    int pageSize = 20,
    String? status,
    String? search,
  }) async {
    final data = await getDoctorPatients(
      sort: sort, order: order, page: page,
      pageSize: pageSize, status: status, search: search,
    );
    return (data['patients'] as List<dynamic>?) ?? [];
  }

  /// GET /doctor/patients/{patient_id}
  /// [trendDays] one of: 7, 30, 90 (default 30).
static Future<Map<String, dynamic>> getDoctorPatientById(
  String patientId, {
  int trendDays = 30,
  int sessionsPage = 1,
  int sessionsLimit = 10,
}) async {
  final headers = await _authHeadersPlain();
  final uri = Uri.parse('$baseUrl/doctor/patients/$patientId').replace(
    queryParameters: {
      'trend_days': '$trendDays',
      'sessions_page': '$sessionsPage',
      'sessions_limit': '$sessionsLimit',
    },
  );
  
  final response = await http.get(uri, headers: headers);
  if (response.statusCode == 200) {
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
  throw Exception('GET /doctor/patients/$patientId failed: ${response.statusCode}');
}

  /// GET /doctor/patients/{patient_id}/trends
  /// [days] one of: 7, 30, 90 (default 30).
  static Future<Map<String, dynamic>> getDoctorPatientTrends(
    String patientId, {
    int days = 30,
    List<String> metrics = const ['movement_age', 'symmetry_score', 'stability_score'],
  }) async {
    final headers = await _authHeadersPlain();
    final uri = Uri.parse('$baseUrl/doctor/patients/$patientId/trends').replace(
      queryParameters: {
        'days': '$days',
        ...{for (var i = 0; i < metrics.length; i++) 'metrics': metrics[i]},
      },
    );
    final response = await http.get(uri, headers: headers);
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('GET /doctor/patients/$patientId/trends failed: ${response.statusCode}');
  }

  /// GET /doctor/patients/{patient_id}/anomalies
  /// Returns { patient_id, flagged_sessions[], total_flagged }.
static Future<Map<String, dynamic>> getDoctorAnomalies(String patientId) async {
    final headers = await _authHeadersPlain();
    final response = await http.get(
      Uri.parse('$baseUrl/doctor/patients/$patientId/anomalies'),
      headers: headers,
    );
    if (response.statusCode == 200) return jsonDecode(response.body);
    return {'flagged_sessions': []};
  }

  /// Анализ Gemini (Вкладка в профиле)
  static Future<Map<String, dynamic>> getDoctorGemini(String patientId) async {
    final headers = await _authHeadersPlain();
    final response = await http.get(
      Uri.parse('$baseUrl/doctor/patients/$patientId/gemini'),
      headers: headers,
    );
    if (response.statusCode == 200) return jsonDecode(response.body);
    return {'analysis': 'No AI analysis available yet.'};
  }

  // ─────────────────────────────────────────────
  // Doctor — Reports
  // ─────────────────────────────────────────────

  /// POST /doctor/patients/{patient_id}/report
  /// Returns 202 with { task_id, patient_id, status, message, estimated_seconds }.
  /// Use [getDoctorReportStatus] to poll for completion.
static Future<Map<String, dynamic>> createDoctorPatientReport(
  String patientId, {
  int days = 30,
  bool includeCharts = true,
}) async {
  final headers = await _authHeaders(); // Здесь нужен Content-Type: application/json
  final response = await http.post(
    Uri.parse('$baseUrl/doctor/patients/$patientId/report'),
    headers: headers,
    body: jsonEncode({
      'days': days, 
      'include_charts': includeCharts
    }),
  );
  
  // Код 202 (Accepted) означает, что генерация началась успешно
  if (response.statusCode == 202 || response.statusCode == 200) {
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
  throw Exception('POST /doctor/patients/$patientId/report failed: ${response.statusCode}');
}

  /// GET /doctor/patients/{patient_id}/report/status/{task_id}
  /// Returns { task_id, status, url, expires_at, error }.
  static Future<Map<String, dynamic>> getDoctorReportStatus(
    String patientId,
    String taskId,
  ) async {
    final headers = await _authHeadersPlain();
    final response = await http.get(
      Uri.parse('$baseUrl/doctor/patients/$patientId/report/status/$taskId'),
      headers: headers,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('GET report status failed: ${response.statusCode}');
  }

  /// GET /doctor/patients/{patient_id}/report/history
  /// Returns a list of report objects (array at top level).
static Future<List<dynamic>> getDoctorReportHistory(String patientId) async {
    final headers = await _authHeadersPlain();
    final response = await http.get(
      Uri.parse('$baseUrl/doctor/patients/$patientId/report/history'),
      headers: headers,
    );
    if (response.statusCode == 200) return jsonDecode(response.body) as List<dynamic>;
    return [];
  }

  /// POST /api/contact
  /// Backend returns a plain string (not a JSON object).
  static Future<String> contact(Map<String, dynamic> payload) async {
    // Required fields: name, email, form_type, message, organization
    final response = await http.post(
      Uri.parse('$baseUrl/api/contact'),
      headers: _jsonHeaders,
      body: jsonEncode(payload),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      final decoded = jsonDecode(response.body);
      return decoded is String ? decoded : decoded.toString();
    }
    throw Exception('POST /api/contact failed: ${response.statusCode}');
  }

  /// POST /api/baseline/record
  /// Payload: { user_id, gait_session_id }
  /// Backend returns a plain string.
  static Future<String> recordBaseline({
    required String userId,
    required String gaitSessionId,
  }) async {
    final headers = await _authHeaders();
    final response = await http.post(
      Uri.parse('$baseUrl/api/baseline/record'),
      headers: headers,
      body: jsonEncode({'user_id': userId, 'gait_session_id': gaitSessionId}),
    );
    if (response.statusCode == 200 || response.statusCode == 201) {
      final decoded = jsonDecode(response.body);
      return decoded is String ? decoded : decoded.toString();
    }
    throw Exception('POST /api/baseline/record failed: ${response.statusCode}');
  }

  /// GET /api/baseline/{user_id}
  /// Backend returns a plain string. No auth header required per spec.
  static Future<String> getBaseline(String userId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/baseline/$userId'),
      headers: {},
    );
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      return decoded is String ? decoded : decoded.toString();
    }
    throw Exception('GET /api/baseline/$userId failed: ${response.statusCode}');
  }


  /// GET /health — 200 = OK, 503 = degraded.
  static Future<bool> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
        headers: {},
      );
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Register a new patient (doctor-facing convenience wrapper).
  static Future<void> createNewPatient({
    required String email,
    required String password,
    required String fullName,
  }) async {
    await register(
      email: email,
      password: password,
      fullName: fullName,
      role: 'patient',
    );
  }
}
