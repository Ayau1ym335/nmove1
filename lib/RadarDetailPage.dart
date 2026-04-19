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
    

final metrics = [
  {'L': 'Step Count', 'V': '${session.stepCount}'},
  {'L': 'Cadence', 'V': val(session.cadence, 'steps/min')},
  {'L': 'Avg Speed', 'V': val(session.avgSpeed, 'm/s')},

  {'L': 'Avg Stance Time', 'V': val(session.avgStanceTime, 'ms')},
  {'L': 'Avg Swing Time', 'V': val(session.avgSwingTime, 'ms')},
  {'L': 'Stance/Swing Ratio', 'V': val(session.stanceSwingRatio, '')},

  {'L': 'Knee Angle Mean', 'V': val(session.kneeAngleMean, '°')},
  {'L': 'Knee Angle Std', 'V': val(session.kneeAngleStd, '°')},
  {'L': 'Knee Angle Max', 'V': val(session.kneeAngleMax, '°')},
  {'L': 'Knee Angle Min', 'V': val(session.kneeAngleMin, '°')},
  {'L': 'Knee Amplitude', 'V': val(session.kneeAmplitude, '°')},

  {'L': 'Hip Angle Mean', 'V': val(session.hipAngleMean, '°')},
  {'L': 'Hip Angle Std', 'V': val(session.hipAngleStd, '°')},
  {'L': 'Hip Angle Max', 'V': val(session.hipAngleMax, '°')},
  {'L': 'Hip Angle Min', 'V': val(session.hipAngleMin, '°')},
  {'L': 'Hip Amplitude', 'V': val(session.hipAmplitude, '°')},

  {'L': 'Avg Roll', 'V': val(session.avgRoll, '°')},
  {'L': 'Avg Pitch', 'V': val(session.avgPitch, '°')},
  {'L': 'Avg Yaw', 'V': val(session.avgYaw, '°')},

  {'L': 'Knee Angle', 'V': val(session.kneeAngle, '°')},
  {'L': 'Hip Angle', 'V': val(session.hipAngle, '°')},
  {'L': 'Ankle Angle', 'V': val(session.ankleAngle, '°')},

  {'L': 'GVI Index', 'V': val(session.gvi, '%')},
  {'L': 'Symmetry Index', 'V': val(session.symmetryIndex, '%')},
  {'L': 'Step Time Var.', 'V': val(session.stepTimeVariability, '%')},
  {'L': 'Stride Length Var.', 'V': val(session.stepLengthVariability, '%')},
  {'L': 'Knee Angle Var.', 'V': val(session.kneeAngleVariability, '%')},
  {'L': 'Stance Time Var.', 'V': val(session.stanceTimeVariability, '%')},

  {'L': 'Avg GVI', 'V': val(session.avgGvi, '%')},
  {'L': 'Avg Knee Angle', 'V': val(session.avgKneeAngle, '°')},
  {'L': 'Avg Hip Angle', 'V': val(session.avgHipAngle, '°')},
  {'L': 'Cadence vs Baseline', 'V': val(session.cadenceVsBaseline, '%')},
  {'L': 'GVI vs Baseline', 'V': val(session.gviVsBaseline, '%')},
  {'L': 'Improvement Score', 'V': val(session.improvementScore, '/100')},
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

          const SizedBox(height: 35), 

          const SizedBox(height: 50), 


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
                _baselineStatus = "Recording baseline...";
              });
              _toggleTimer(true);
            } else {
              _toggleTimer(false);
              setState(() => _isRecording = false);
              
              try {
                await ApiService.recordBaseline(
  userId: user.userId,
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