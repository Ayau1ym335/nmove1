import 'package:flutter/material.dart';
import 'dart:math' as math;
import 'main.dart';
import 'gradient_text_field.dart';
import 'activity_progress_page.dart';
import 'user_data.dart';
import 'services/api_service.dart';
import 'package:url_launcher/url_launcher.dart'; 
import 'RadarDetailPage.dart';
import 'RadarDetailPage.dart' as radar;
import 'Radar_painter.dart';

const Color neonCyan = Colors.cyanAccent;
const Color darkCard = Color(0xFF1A1D21);
const Color darkBg = Color(0xFF0B0E11);

class PatientProfileScreen extends StatefulWidget {
  final UserData? patientData; 
  const PatientProfileScreen({super.key, this.patientData});

  @override
  State<PatientProfileScreen> createState() => _PatientProfileScreenState();
}

class _PatientProfileScreenState extends State<PatientProfileScreen> {
  int _selectedIndex = 0; 
  bool isWeekSelected = true;
  bool isTrendsWeekSelected = true;
  late SensorStreamService _sensorService;

  @override
  Widget build(BuildContext context) {
    final provider = UserDataProvider.of(context);
    final user = widget.patientData ?? provider?.userData;

    if (user == null) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(child: Text("Data not found", style: TextStyle(color: Colors.white))),
      );
    }

    return Scaffold(
      backgroundColor: darkBg,
      body: Row(
        children: [
          NavigationRail(
            backgroundColor: Colors.black,
            selectedIndex: _selectedIndex,
            onDestinationSelected: (int index) => setState(() => _selectedIndex = index),
            labelType: NavigationRailLabelType.none,
            selectedIconTheme: const IconThemeData(color: neonCyan, size: 30),
            unselectedIconTheme: const IconThemeData(color: Colors.white24),
            destinations: const [
              NavigationRailDestination(icon: Icon(Icons.grid_view_rounded), label: Text('Overview')),
              NavigationRailDestination(icon: Icon(Icons.auto_graph_rounded), label: Text('Trends')),
              NavigationRailDestination(icon: Icon(Icons.warning_amber_rounded), label: Text('Anomalies')),
            ],
          ),
          const VerticalDivider(thickness: 1, width: 1, color: Colors.white10),

          Expanded(
            child: _buildCurrentTab(user),
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentTab(UserData user) {
    switch (_selectedIndex) {
      case 0:
        return _buildFullOverviewTab(user); 
      case 1:
        return _buildTrendsTab(user);
      case 2:
        return _buildAnomaliesTab(user);
      default:
        return _buildFullOverviewTab(user);
    }
  }

Widget _buildFullOverviewTab(UserData user) {
  final session = user.lastSession;
  
  final String currentBioAge = user.biomechanicalAge ?? "—"; 
  final String baselineAge = user.age ?? "—";

final List<double> radarValues = [
  (session?.symmetryIndex ?? 0) / 100,
  ((session?.cadence ?? 0) / 180).clamp(0.0, 1.0),
  ((session?.kneeAngleMax ?? 0) / 170).clamp(0.0, 1.0),
  ((session?.hipAmplitude ?? 0) / 90).clamp(0.0, 1.0),
  ((session?.gvi ?? 0) / 100).clamp(0.0, 1.0),
];

final List<String> radarLabels = ["Sym", "Cad", "Knee", "Hip", "Stab"];

  return SingleChildScrollView(
    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildHeader(user),
        const SizedBox(height: 30),
        
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ЛЕВАЯ ПОЛОВИНА: Возраст, Радар и График
            Expanded(
              flex: 5,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildBiomechanicalAgeHeader(currentBioAge, baselineAge),
                  const SizedBox(height: 30),
                  
SizedBox(
  width: 350,
  height: 350,
  child: CustomPaint(
    painter: RadarChartPainter(
      values: radarValues, 
      labels: radarLabels, 
    ),
  ),
),

                  const SizedBox(height: 40),
                  
                  // ЛИНЕЙНЫЙ ГРАФИК ПРОГРЕССА
                  const Text("Progress History", 
                    style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  SizedBox(
                    height: 160,
                    child: CustomPaint(
                      painter: NeonLinePainter(
                        data: user.progressData,
                        isWeekSelected: isWeekSelected,
                        baseAge: double.tryParse(user.age) ?? 30.0,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(width: 20),

            // ПРАВАЯ ПОЛОВИНА: Ключевые метрики
            Expanded(
              flex: 3,
              child: Column(
                children: [
                  const SizedBox(height: 10), // Отступ для выравнивания с заголовком слева
                  _metricSmallCard("Symmetry", "${session?.symmetryIndex.toStringAsFixed(0) ?? 0}%", neonCyan),
                  _metricSmallCard("Cadence", "${session?.cadence.toStringAsFixed(0) ?? 0}", Colors.white),
                  _metricSmallCard("Knee Angle", "${session?.kneeAngleMax.toStringAsFixed(0) ?? 0}°", neonCyan),
                  _metricSmallCard("Hip Amp.", "${session?.hipAmplitude.toStringAsFixed(0) ?? 0}°", Colors.white),
                  // Добавил пятую карточку для симметрии с радаром
                  _metricSmallCard("Improvement", "${user.getImprovement().toStringAsFixed(1)}%", neonCyan),
                ],
              ),
            ),
          ],
        ),
        
        // Блок Hardware Status и нижний радар полностью удалены
      ],
    ),
  );
}
Widget _buildBiomechanicalAgeHeader(String current, String baseline) {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Text(
        "Biomechanical Age",
        style: TextStyle(
          color: Colors.white,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      const SizedBox(height: 4),
      RichText(
        text: TextSpan(
          style: const TextStyle(fontSize: 16, color: Colors.white),
          children: [
            const TextSpan(text: "Current Biomechanical Age: "),
            TextSpan(
              text: "${current}y",
              style: const TextStyle(color: neonCyan, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
      RichText(
        text: TextSpan(
          style: const TextStyle(fontSize: 14, color: Colors.white70),
          children: [
            const TextSpan(text: "Baseline Age: "),
            TextSpan(
              text: "${baseline}y",
              style: const TextStyle(color: neonCyan),
            ),
          ],
        ),
      ),
    ],
  );
}
  Widget _buildHeader(user) {
    return Row(
      children: [
        const CircleAvatar(radius: 30, backgroundColor: Colors.white12, child: Icon(Icons.person, color: neonCyan, size: 35)),
        const SizedBox(width: 15),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("${user.fullName}, ${user.age}y", style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              Row(
                children: [
                  _topStat("City", user.city.isEmpty ? "Not set" : user.city),
                  const SizedBox(width: 20),
                  _topStat("ID", user.userId),
                ],
              )
            ],
          ),
        ),
      ],
    );
  }

  Widget _topStat(String label, String value) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10)),
      Text(value, style: const TextStyle(color: neonCyan, fontSize: 14, fontWeight: FontWeight.bold)),
    ]);
  }

  Widget _metricSmallCard(String label, String value, Color color) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: darkCard, borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.white10)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(color: Colors.white54, fontSize: 10)),
        const SizedBox(height: 4),
        Text(value, style: TextStyle(color: color, fontSize: 16, fontWeight: FontWeight.bold)),
      ]),
    );
  }

  Widget _buildPeriodToggle() {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(8)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        _toggleBtn("Week", isWeekSelected),
        _toggleBtn("Month", !isWeekSelected),
      ]),
    );
  }

  Widget _toggleBtn(String text, bool active) {
    return GestureDetector(
      onTap: () => setState(() => isWeekSelected = (text == "Week")),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 6),
        decoration: BoxDecoration(color: active ? neonCyan : Colors.transparent, borderRadius: BorderRadius.circular(6)),
        child: Text(text, style: TextStyle(color: active ? Colors.black : Colors.white38, fontSize: 12, fontWeight: FontWeight.bold)),
      ),
    );
  }

Widget _buildTrendsTab(UserData user) {
  // Подготовка данных (Логика из вашего ActivityProgressPage)
  final List<double> currentData = isWeekSelected 
      ? (user.progressData.length >= 7 ? user.progressData.sublist(0, 7) : user.progressData)
      : user.progressData;

  final validData = currentData.where((v) => v > 0).toList();

  double avgAge = validData.isEmpty 
      ? (double.tryParse(user.age) ?? 0.0) 
      : validData.reduce((a, b) => a + b) / validData.length;

  double improvement = 0.0;
  if (validData.length >= 2) {
    double first = validData.first;
    double last = validData.last;
    improvement = ((first - last) / first) * 100;
  }

  double personalRecord = validData.isEmpty 
      ? avgAge 
      : validData.reduce((a, b) => a < b ? a : b);

    return Scaffold(
      backgroundColor: Colors.black,
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        child: Column(
          children: [
            const SizedBox(height: 40),
            const Text("NMove", style: TextStyle(color: Colors.cyanAccent, fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            const Text("Activity & Progress", style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 25),
            
            _buildPeriodToggle(), 
            
            const SizedBox(height: 30),
            const Text("Biomechanical Age", style: TextStyle(color: Colors.white70, fontSize: 16)),
            const SizedBox(height: 20), 

        Padding(
          padding: const EdgeInsets.only(left: 40, right: 20, bottom: 30), 
          child: SizedBox(
            height: 200,
            width: double.infinity,
            child: CustomPaint(
              painter: NeonLinePainter(
                data: currentData, 
                isWeekSelected: isWeekSelected,
                baseAge: double.tryParse(user.age) ?? 30.0,
              ),
            ),
          ),
        ),

        _buildImprovementText(improvement),
        const SizedBox(height: 20),
      ],
    ),
  )
    );
}

Widget _buildImprovementText(double improvement) {
  return RichText(
    textAlign: TextAlign.center,
    text: TextSpan(
      style: const TextStyle(color: Colors.white70, fontSize: 14),
      children: [
        const TextSpan(text: "Mobility "),
        TextSpan(
          text: improvement >= 0 ? "improved " : "declined ",
          style: const TextStyle(color: neonCyan, fontWeight: FontWeight.bold),
        ),
        TextSpan(
          text: "by ${improvement.abs().isNaN ? '0.0' : improvement.abs().toStringAsFixed(1)}% ",
          style: const TextStyle(color: neonCyan, fontWeight: FontWeight.bold),
        ),
        TextSpan(text: "this ${isWeekSelected ? 'week' : 'month'}!"),
      ],
    ),
  );
}

Widget _buildAnomaliesTab(UserData user) {
  return RefreshIndicator(
    onRefresh: () async => setState(() {}),
    child: SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 25),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Секция отчетов
          _buildPdfSection(user.userId),
          const SizedBox(height: 30),

          // Анализ от ИИ (Gemini)
          const Text("AI Clinical Analysis", 
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 15),
          
          FutureBuilder<Map<String, dynamic>>(
            future: ApiService.getDoctorGemini(user.userId),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator(color: neonCyan));
              }
              
              final data = snapshot.data;
              // Согласно вашему ApiService, данные могут быть в 'raw' или 'analysis'
              final geminiText = data?['analysis'] ?? data?['raw'] ?? "No AI analysis generated for this period.";

              return _buildAiMessageCard(
                "Gemini Insights",
                geminiText.toString(),
                Icons.auto_awesome,
              );
            },
          ),

          const SizedBox(height: 30),
          const Text("Detected Anomalies", 
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 15),

          // Список аномалий
          FutureBuilder<Map<String, dynamic>>(
            future: ApiService.getDoctorAnomalies(user.userId),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) return const SizedBox();
              
              final flagged = snapshot.data?['flagged_sessions'] as List? ?? [];

              if (flagged.isEmpty) {
                return _buildAiMessageCard(
                  "Movement Status",
                  "No significant gait anomalies or biomechanical deviations detected.",
                  Icons.check_circle_outline,
                  isPositive: true,
                );
              }

              return Column(
                children: flagged.map((item) => _buildAnomalyTile(item)).toList(),
              );
            },
          ),
        ],
      ),
    ),
  );
}

// Виджет для PDF
Widget _buildPdfSection(String userId) {
  return Container(
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: const Color(0xFF1A1D21),
      borderRadius: BorderRadius.circular(15),
      border: Border.all(color: Colors.redAccent.withOpacity(0.3)),
    ),
    child: Row(
      children: [
        const Icon(Icons.picture_as_pdf, color: Colors.redAccent, size: 35),
        const SizedBox(width: 15),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("Gait Analysis Report", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              Text("Generate PDF summary", style: TextStyle(color: Colors.white54, fontSize: 12)),
            ],
          ),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
          onPressed: () => _generateAndOpenReport(userId),
          child: const Text("Generate"),
        ),
      ],
    ),
  );
}

// Карточка сообщения от ИИ
Widget _buildAiMessageCard(String title, String content, IconData icon, {bool isPositive = false}) {
  final color = isPositive ? Colors.greenAccent : neonCyan;
  return Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: const Color(0xFF0A0A0A),
      borderRadius: BorderRadius.circular(15),
      border: Border.all(color: color.withOpacity(0.2)),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(width: 10),
            Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 10),
        Text(content, style: const TextStyle(color: Colors.white70, height: 1.5, fontSize: 14)),
      ],
    ),
  );
}

// Плитка аномалии
Widget _buildAnomalyTile(Map<String, dynamic> item) {
  return Container(
    margin: const EdgeInsets.only(bottom: 10),
    decoration: BoxDecoration(
      color: Colors.redAccent.withOpacity(0.05),
      borderRadius: BorderRadius.circular(12),
    ),
    child: ListTile(
      leading: const Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
      title: Text("Session #${item['session_id'] ?? '?'}", style: const TextStyle(color: Colors.white, fontSize: 14)),
      subtitle: Text(item['reason'] ?? "Symmetry deviation", style: const TextStyle(color: Colors.white54, fontSize: 12)),
    ),
  );
} 
Future<void> _generateAndOpenReport(String userId) async {
  try {
    // 1. Создаем запрос на отчет
    await ApiService.createDoctorPatientReport(userId);
    
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Processing report..."), backgroundColor: Colors.redAccent),
    );

    // 2. Небольшая задержка, чтобы бэкенд успел создать запись в истории
    await Future.delayed(const Duration(seconds: 2));

    // 3. Получаем историю и открываем последнюю ссылку
    final history = await ApiService.getDoctorReportHistory(userId);
    if (history.isNotEmpty) {
      final latestUrl = history.first['url']; // Проверьте имя поля в вашем JSON
      if (latestUrl != null) {
        final uri = Uri.parse(latestUrl);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
      }
    }
  } catch (e) {
    debugPrint("Error: $e");
  }
}
}