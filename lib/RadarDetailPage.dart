import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'user_data.dart';
import 'walking_session.dart';
import 'dart:math' as math;
import 'dart:async';

class RadarDetailPage extends StatefulWidget {
  final PageController? homeController; // Добавь это поле
  const RadarDetailPage({super.key, this.homeController}); // И сюда

  @override
  State<RadarDetailPage> createState() => _RadarDetailPageState();
}
class _RadarDetailPageState extends State<RadarDetailPage> with SingleTickerProviderStateMixin {
  final PageController _pageController = PageController();
  
  // Переменные для Baseline
  String _baselineStatus = "No baseline recorded";
  bool _isRecording = false; 
  String selectedLeg = "left"; 
  int _seconds = 0;
  Timer? _timer;
  
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    // Контроллер для вращения дуг
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();
  }

  @override
  void dispose() {
    _animationController.dispose();
    _timer?.cancel();
    _pageController.dispose();
    super.dispose();
  }

  void _toggleTimer(bool start) {
    if (start) {
      _seconds = 0;
      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        setState(() => _seconds++);
      });
    } else {
      _timer?.cancel();
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = UserDataProvider.of(context);
    final user = provider?.userData;
    final session = user?.lastSession ?? WalkingSession();

    return Scaffold(
      backgroundColor: const Color(0xFF0B0E11),
      body: PageView(
        controller: _pageController,
        children: [
          // ПЕРВАЯ СТРАНИЦА: Твоя детальная аналитика
          _buildMainAnalysis(context, session),
          
          // ВТОРАЯ СТРАНИЦА: Твой новый Baseline
          _buildBaselineScreen(user),
        ],
      ),
    );
  }


Widget _buildMainAnalysis(BuildContext context, WalkingSession session) {
final hasData = session.stepCount > 0 || session.cadence > 0;

  // Вспомогательная функция для форматирования
  String val(dynamic value, String unit, {int decimals = 1}) {
    if (!hasData) return '-- $unit';
    if (value is double) return '${value.toStringAsFixed(decimals)} $unit';
    return '$value $unit';
  }

  // Функция для парных параметров (Лево/Право)
  String dual(dynamic left, dynamic right, String unit) {
    if (!hasData) return '--/-- $unit';
    return '${left.toStringAsFixed(0)}/${right.toStringAsFixed(0)} $unit';
  }
    

final metrics = [{'L': 'Stance Time (L/R)', 'V': dual(session.stanceTimeLeft, session.stanceTimeRight, 'ms')},
    {'L': 'Swing Time (L/R)', 'V': dual(session.swingTimeLeft, session.swingTimeRight, 'ms')},
    {'L': 'Step Time (L/R)', 'V': dual(session.stepTimeLeft, session.stepTimeRight, 'ms')},
    {'L': 'Stride Time (L/R)', 'V': dual(session.strideTimeLeft, session.strideTimeRight, 'ms')},
    {'L': 'Double Support', 'V': val(session.doubleSupportTime, 'ms')},
    {'L': 'Single Support', 'V': val(session.singleSupportTime, 'ms')},
    {'L': 'Loading Response', 'V': val(session.loadingResponseTime, 'ms')},
    {'L': 'Pre-Swing Time', 'V': val(session.preSwingTime, 'ms')},

    // Геометрия и Кинематика (10 параметров)
    {'L': 'Stride Length', 'V': val(session.strideLength, 'cm')},
    {'L': 'Step Width', 'V': val(session.stepWidth, 'cm')},
    {'L': 'Vertical Oscillation', 'V': val(session.verticalOscillation, 'cm')},
    {'L': 'Knee Amplitude (L/R)', 'V': dual(session.kneeAmplitudeLeft, session.kneeAmplitudeRight, '°')},
    {'L': 'Hip Amplitude (L/R)', 'V': dual(session.hipAmplitudeLeft, session.hipAmplitudeRight, '°')},
    {'L': 'Knee Angle Mean/Max', 'V': '${val(session.kneeAngleMean, '°')} / ${val(session.kneeAngleMax, '°')}'},
    {'L': 'Hip Angle Mean/Min', 'V': '${val(session.hipAngleMean, '°')} / ${val(session.hipAngleMin, '°')}'},
    {'L': 'Ankle ROM', 'V': val(session.ankleRangeOfMotion, '°')},
    {'L': 'Trunk Sway', 'V': val(session.trunkSway, '°')},

    // Стопа и углы (6 параметров)
    {'L': 'Foot Strike Angle', 'V': val(session.footStrikeAngle, '°')},
    {'L': 'Toe Off Angle', 'V': val(session.toeOffAngle, '°')},
    {'L': 'Avg Roll / Pitch', 'V': '${session.avgRoll.toInt()}° / ${session.avgPitch.toInt()}°'},
    {'L': 'Avg Yaw', 'V': val(session.avgYaw, '°')},
    {'L': 'Peak Angular Vel.', 'V': val(session.avgPeakAngularVelocity, '°/s')},

    // Индексы, Вариабельность и Силы (6 параметров)
    {'L': 'GVI Index', 'V': val(session.gvi, '%')},
    {'L': 'Symmetry Index', 'V': val(session.symmetryIndex, '%')},
    {'L': 'Step Time Var.', 'V': val(session.stepTimeVariability, '%')},
    {'L': 'Impact Force', 'V': val(session.groundImpactForce, 'N', decimals: 0)},
    {'L': 'Propulsion Force', 'V': val(session.propulsionForce, 'N', decimals: 0)},
    {'L': 'Energy Cost', 'V': val(session.energyCost, 'kcal/m', decimals: 2)},
  ];

return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
      child: Column(children: [
        // КНОПКА ВОЗВРАТА (теперь не красная)
        IconButton(
          icon: const Icon(Icons.keyboard_arrow_up, color: Colors.cyanAccent, size: 40),
          onPressed: () {
            widget.homeController?.animateToPage(0,
                duration: const Duration(milliseconds: 500), curve: Curves.easeOut);
          },
        ),
        
        const Text('Detailed Analysis', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        const Text('Swipe right for Baseline →', style: TextStyle(color: Colors.cyanAccent, fontSize: 12)),
        const SizedBox(height: 30),
        
        Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
          _MetricCircle(label: 'Steps', value: hasData ? '${session.stepCount}' : '0', color: Colors.cyanAccent),
          _MetricCircle(label: 'Speed', value: hasData ? session.avgSpeed.toStringAsFixed(1) : '0.0', color: Colors.pinkAccent),
          _MetricCircle(label: 'Cadence', value: hasData ? '${session.cadence.toInt()}' : '0', color: Colors.purpleAccent),
        ]),
        
        const SizedBox(height: 40),
        
        Container(
          decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.03),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white10)),
          child: ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: metrics.length,
            separatorBuilder: (_, __) => Divider(color: Colors.white.withOpacity(0.05), height: 1),
            itemBuilder: (_, i) => Padding(
              padding: const EdgeInsets.all(16),
              child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                Text(metrics[i]['L'] ?? '', style: const TextStyle(color: Colors.white70, fontSize: 14)),
                Text(metrics[i]['V'] ?? '', style: TextStyle(color: hasData ? Colors.cyanAccent : Colors.white24, fontWeight: FontWeight.bold, fontSize: 14)),
              ]),
            ),
          ),
        ),
      ]),
    );
  }

Widget _buildBaselineScreen(UserData? user) {
  return SafeArea(
    child: SingleChildScrollView( // 1. Добавляем скролл
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
      child: Column(
        children: [
          const SizedBox(height: 20),
          
          // Блок инфо
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1D21),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.cyanAccent.withOpacity(0.1)),
            ),
            child: Column(
              children: [
                const Icon(Icons.info_outline, color: Colors.cyanAccent, size: 30),
                const SizedBox(height: 10),
                const Text("WHAT IS A BASELINE?",
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 8),
                const Text(
                  "This is your 'healthy' reference point. We will compare future sessions with this data.",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
          ),

          const SizedBox(height: 35), // Заменили Spacer на фиксированный отступ

          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _legToggle("left", "LEFT LEG"),
              const SizedBox(width: 15),
              _legToggle("right", "RIGHT LEG"),
            ],
          ),

          const SizedBox(height: 50), // Заменили Spacer на фиксированный отступ

          // Графика с анимацией
          Stack(
            alignment: Alignment.center,
            children: [
              AnimatedBuilder(
                animation: _animationController,
                builder: (context, child) {
                  return CustomPaint(
                    size: const Size(220, 220), // Немного увеличили для красоты
                    painter: BaselineArcPainter(
                      animationValue: _animationController.value,
                      isRecording: _isRecording,
                    ),
                  );
                },
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.directions_walk,
                    size: 80,
                    color: _isRecording ? Colors.white : Colors.white24,
                  ),
                  if (_isRecording) ...[
                    const SizedBox(height: 8),
                    Text(
                      "${_seconds ~/ 60}:${(_seconds % 60).toString().padLeft(2, '0')}",
                      style: const TextStyle(
                        color: Colors.white, 
                        fontSize: 22, 
                        fontWeight: FontWeight.bold,
                        fontFamily: 'monospace'
                      ),
                    ),
                  ]
                ],
              ),
            ],
          ),

          const SizedBox(height: 50), // Заменили Spacer на фиксированный отступ

          // Кнопка
          _neonButton(_isRecording ? "STOP & SAVE" : "START BASELINE", () async {
            if (user == null) return;

            if (!_isRecording) {
              setState(() {
                _isRecording = true;
                _baselineStatus = "Recording $selectedLeg leg...";
              });
              _toggleTimer(true);
            } else {
              _toggleTimer(false);
              setState(() => _isRecording = false);
              
              try {
                await ApiService.recordBaseline(
                  userId: user.userId,
                  gaitSessionId: "latest", 
                );
                setState(() => _baselineStatus = "Success! Baseline saved.");
              } catch (e) {
                setState(() => _baselineStatus = "Connection Error: Check Wi-Fi");
              }
            }
          }),
          
          const SizedBox(height: 15),
          Text(_baselineStatus, 
            style: TextStyle(
              color: _baselineStatus.contains("Error") ? Colors.redAccent : Colors.white30, 
              fontSize: 12
            )
          ),
          const SizedBox(height: 40), // Отступ снизу, чтобы кнопка не прилипала к краю
        ],
      ),
    ),
  );
}

Widget _legToggle(String leg, String label) {
  bool isSelected = selectedLeg == leg;
  return GestureDetector(
    onTap: () => setState(() => selectedLeg = leg),
    child: Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      decoration: BoxDecoration(
        color: isSelected ? Colors.cyanAccent : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyanAccent),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: isSelected ? Colors.black : Colors.cyanAccent,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    ),
  );
}

Widget _neonButton(String text, VoidCallback onPressed) {
  return Container(
    width: double.infinity,
    height: 55,
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(30),
      boxShadow: [
        BoxShadow(
          color: _isRecording ? Colors.redAccent.withOpacity(0.3) : Colors.cyanAccent.withOpacity(0.3),
          blurRadius: 15,
          spreadRadius: 1,
        ),
      ],
    ),
    child: ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF1A1D21), // Темный фон кнопки
        foregroundColor: _isRecording ? Colors.redAccent : Colors.cyanAccent, // Цвет текста
        side: BorderSide(
          color: _isRecording ? Colors.redAccent : Colors.cyanAccent, 
          width: 2
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
        elevation: 0,
      ),
      child: Text(
        text,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1.2),
      ),
    ),
  );
}
}
class BaselineArcPainter extends CustomPainter {
  final double animationValue;
  final bool isRecording;

  BaselineArcPainter({required this.animationValue, required this.isRecording});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    // Угол поворота зависит от анимации
    final double sweepAngle = math.pi * 0.7; 
    final double startAngle = animationValue * 2 * math.pi;

    final paintBlue = Paint()
      ..color = Colors.blueAccent.withOpacity(isRecording ? 1.0 : 0.2)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;

    final paintRed = Paint()
      ..color = Colors.redAccent.withOpacity(isRecording ? 1.0 : 0.2)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;

    // Синяя неполная дуга
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), startAngle, sweepAngle, false, paintBlue);

    // Красная неполная дуга (напротив)
    canvas.drawArc(Rect.fromCircle(center: center, radius: radius), startAngle + math.pi, sweepAngle, false, paintRed);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class _MetricCircle extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final double size;

  const _MetricCircle({
    required this.label,
    required this.value,
    required this.color,
    this.size = 80,
  });

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: color.withOpacity(0.5), width: 2),
          boxShadow: [BoxShadow(color: color.withOpacity(0.2), blurRadius: 10, spreadRadius: 2)],
        ),
        child: Center(
          child: Text(value,
              style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 18)),
        ),
      ),
      const SizedBox(height: 8),
      Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12)),
    ]);
  }
}