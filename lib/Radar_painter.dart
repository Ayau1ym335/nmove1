import 'package:flutter/material.dart';
import 'dart:math' as math;

class RadarChartPainter extends CustomPainter {
  final List<double> values; 
  final List<String> labels; 

  RadarChartPainter({required this.values, required this.labels}); 

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    final angleStep = (2 * math.pi) / labels.length;

    // 1. Сетка
    final gridPaint = Paint()
      ..color = Colors.white.withOpacity(0.05)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    for (var i = 1; i <= 4; i++) {
      canvas.drawCircle(center, radius * (i / 4), gridPaint);
    }

    // 2. Оси
    final axisPaint = Paint()
      ..color = Colors.white10
      ..strokeWidth = 1;

    for (var i = 0; i < labels.length; i++) {
      final angle = i * angleStep - math.pi / 2;
      final endpoint = Offset(
        center.dx + radius * math.cos(angle),
        center.dy + radius * math.sin(angle),
      );
      canvas.drawLine(center, endpoint, axisPaint);
    }

    // 3. Данные (Красная паутинка)
    if (values.isNotEmpty && values.length == labels.length) {
      final dataPaint = Paint()
        ..color = Colors.redAccent.withOpacity(0.4)
        ..style = PaintingStyle.fill;

      final strokePaint = Paint()
        ..color = Colors.redAccent
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2.5;

      final path = Path();
      for (var i = 0; i < values.length; i++) {
        final angle = i * angleStep - math.pi / 2;
        final val = values[i].clamp(0.0, 1.0);
        final x = center.dx + radius * val * math.cos(angle);
        final y = center.dy + radius * val * math.sin(angle);

        if (i == 0) path.moveTo(x, y);
        else path.lineTo(x, y);
      }
      path.close();
      canvas.drawPath(path, dataPaint);
      canvas.drawPath(path, strokePaint);
    }
  }

  // ОСТАВЬ ТОЛЬКО ОДИН ЭТОТ МЕТОД:
  @override
  bool shouldRepaint(covariant RadarChartPainter oldDelegate) {
    return oldDelegate.values != values;
  }
}
