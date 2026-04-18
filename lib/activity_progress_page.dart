import 'package:flutter/material.dart';
import 'user_data.dart';
import 'services/api_service.dart';

class ActivityProgressPage extends StatefulWidget {
  const ActivityProgressPage({super.key});

  @override
  State<ActivityProgressPage> createState() => _ActivityProgressPageState();
}

class _ActivityProgressPageState extends State<ActivityProgressPage> {
  bool isWeekSelected = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadTrends();
    });
  }

  Future<void> _loadTrends() async {
    final userData = UserDataProvider.of(context)?.userData;
    if (userData == null) return;
    final userId = userData.userId;
    if (userId.isEmpty) return;

    try {
      final trends = await ApiService.getTrends(userId);
      final weekly = (trends['weekly'] as List?)?.cast<num>().map((e) => e.toDouble()).toList();
      final monthly = (trends['monthly'] as List?)?.cast<num>().map((e) => e.toDouble()).toList();
      if (!mounted) return;
      setState(() {
        if (weekly != null && weekly.isNotEmpty) {
          userData.progressData = weekly;
          userData.progressMonths = List.generate(weekly.length, (i) => 'W${i + 1}');
        } else if (monthly != null && monthly.isNotEmpty) {
          userData.progressData = monthly;
          userData.progressMonths = List.generate(monthly.length, (i) => 'M${i + 1}');
        }
      });
    } catch (_) {
      // Keep local fallback if trends endpoint is unavailable.
    }
  }

  @override
  Widget build(BuildContext context) {
    final userData = UserDataProvider.of(context)!.userData;

    final List<double> currentData = isWeekSelected 
        ? (userData.progressData.length >= 7 ? userData.progressData.sublist(0, 7) : userData.progressData)
        : userData.progressData;

    final validData = currentData.where((v) => v > 0).toList();

    double avgAge = validData.isEmpty 
        ? (double.tryParse(userData.age) ?? 0.0) 
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
                    baseAge: double.tryParse(userData.age) ?? 30.0,
                  ),
                ),
              ),
            ),

            const SizedBox(height: 30),
            _buildImprovementText(improvement),
            const SizedBox(height: 30),
            
            const Align(
              alignment: Alignment.centerLeft,
              child: Text("Recent Logs", style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 20),

            Row(
              children: [
                Expanded(child: _buildNeonCard("Avg. Age", "${avgAge.toStringAsFixed(0)}y")),
                const SizedBox(width: 15),
                Expanded(child: _buildNeonCard("Your Personal Record", "${personalRecord.toStringAsFixed(0)}y")),
              ],
            ),

            const SizedBox(height: 20),
            _buildStabilityPanel(96),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }


  Widget _buildImprovementText(double improvement) {
    return RichText(
      textAlign: TextAlign.center,
      text: TextSpan(
        style: const TextStyle(color: Colors.white70, fontSize: 14),
        children: [
          const TextSpan(text: "Your mobility "),
          TextSpan(
            text: improvement >= 0 ? "improved " : "declined ",
            style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold),
          ),
          TextSpan(
            text: "by ${improvement.abs().isNaN ? '0.0' : improvement.abs().toStringAsFixed(1)}% ",
            style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold),
          ),
          TextSpan(text: "this ${isWeekSelected ? 'week' : 'month'}!"),
        ],
      ),
    );
  }

  Widget _buildPeriodToggle() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyanAccent.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _toggleButton("Week", isWeekSelected),
          _toggleButton("Month", !isWeekSelected),
        ],
      ),
    );
  }

  Widget _toggleButton(String text, bool active) {
    return GestureDetector(
      onTap: () => setState(() => isWeekSelected = (text == "Week")),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 10),
        decoration: BoxDecoration(
          color: active ? Colors.cyanAccent : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: active ? Colors.black : Colors.white24, 
            fontWeight: FontWeight.bold
          ),
        ),
      ),
    );
  }

  Widget _buildNeonCard(String title, String value) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0A0A0A),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.cyanAccent.withOpacity(0.5), width: 2),
      ),
      child: Column(
        children: [
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 13)),
          const SizedBox(height: 10),
          Text(value, style: const TextStyle(color: Colors.cyanAccent, fontSize: 36, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildStabilityPanel(int stability) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.cyanAccent.withOpacity(0.5)),
      ),
      child: Center(
        child: Text("Stability: $stability%  •  Impact: Safe", 
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
      ),
    );
  }
}


class NeonLinePainter extends CustomPainter {
  final List<double> data;
  final bool isWeekSelected;
  final double baseAge;

  NeonLinePainter({required this.data, required this.isWeekSelected, required this.baseAge});

  @override
  void paint(Canvas canvas, Size size) {
    if (data.isEmpty) return;

    final linePaint = Paint()
      ..color = Colors.cyanAccent
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    const textStyle = TextStyle(color: Colors.white38, fontSize: 10);
    double minAge = baseAge - 10;
    double maxAge = baseAge + 10;
    double range = maxAge - minAge;

    double normalize(double value) {
      double val = value == 0 ? baseAge : value; 
      return size.height - ((val - minAge) / range) * size.height;
    }


    for (int i = 0; i <= 4; i++) {
      double yVal = minAge + (range / 4) * i;
      double yPos = normalize(yVal);
      _drawText(canvas, "${yVal.toInt()}y", Offset(-35, yPos - 5), textStyle);
      canvas.drawLine(Offset(0, yPos), Offset(size.width, yPos), Paint()..color = Colors.white10);
    }

    List<String> xLabels = isWeekSelected 
        ? ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'] 
        : ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']; 
    
    double xLabelStep = size.width / (xLabels.length - 1);
    for (int i = 0; i < xLabels.length; i++) {
      _drawText(canvas, xLabels[i], Offset(i * xLabelStep - 12, size.height + 15), textStyle);
    }

    if (data.length > 1) {
      final path = Path();
      double stepX = size.width / (data.length - 1);
      
      path.moveTo(0, normalize(data[0]));
      for (int i = 1; i < data.length; i++) {
        path.lineTo(i * stepX, normalize(data[i]));
      }
      
      canvas.drawPath(path, linePaint..maskFilter = const MaskFilter.blur(BlurStyle.normal, 2));
      canvas.drawPath(path, linePaint); // Основная линия

      final dotPaint = Paint()..color = Colors.cyanAccent;
      for (int i = 0; i < data.length; i++) {
        canvas.drawCircle(Offset(i * stepX, normalize(data[i])), 4, dotPaint);
      }
    }
  }

  void _drawText(Canvas canvas, String text, Offset offset, TextStyle style) {
    final tp = TextPainter(text: TextSpan(text: text, style: style), textDirection: TextDirection.ltr)..layout();
    tp.paint(canvas, offset);
  }

  @override
  bool shouldRepaint(covariant NeonLinePainter oldDelegate) => true;
}