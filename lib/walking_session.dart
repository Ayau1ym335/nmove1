import 'dart:convert';

class WalkingSession {
  // Основные
  final int stepCount;
  final double cadence;
  final double avgSpeed;

  final double avgStanceTime;
  final double avgSwingTime;
  final double stanceSwingRatio;

  // Углы колена
  final double kneeAngleMean;
  final double kneeAngleStd;
  final double kneeAngleMax;
  final double kneeAngleMin;
  final double kneeAmplitude;

  // Углы бедра
  final double hipAngleMean;
  final double hipAngleStd;
  final double hipAngleMax;
  final double hipAngleMin;
  final double hipAmplitude;

  final double avgRoll;
  final double avgPitch;
  final double avgYaw;

  // Углы стопы
  final double kneeAngle;
  final double hipAngle;
  final double ankleAngle;

  // Вариабельность
  final double gvi;
  final double symmetryIndex;
  final double stepTimeVariability;
  final double stepLengthVariability;
  final double kneeAngleVariability;
  final double stanceTimeVariability;

  // Прогресс (из UserProgress)
  final double avgGvi;
  final double avgKneeAngle;
  final double avgHipAngle;
  final double cadenceVsBaseline;
  final double gviVsBaseline;
  final double kneeAmplitudeVsBaseline;
  final String trend;
  final double improvementScore;

  WalkingSession({
    this.stepCount = 0,
    this.cadence = 0.0,
    this.avgSpeed = 0.0,
    this.avgStanceTime = 0.0,
    this.avgSwingTime = 0.0,
    this.stanceSwingRatio = 0.0,
    this.kneeAngleMean = 0.0,
    this.kneeAngleStd = 0.0,
    this.kneeAngleMax = 0.0,
    this.kneeAngleMin = 0.0,
    this.kneeAmplitude = 0.0,
    this.hipAngleMean = 0.0,
    this.hipAngleStd = 0.0,
    this.hipAngleMax = 0.0,
    this.hipAngleMin = 0.0,
    this.hipAmplitude = 0.0,
    this.avgRoll = 0.0,
    this.avgPitch = 0.0,
    this.avgYaw = 0.0,
    this.kneeAngle = 0.0,
    this.hipAngle = 0.0,
    this.ankleAngle = 0.0,
    this.gvi = 0.0,
    this.symmetryIndex = 0.0,
    this.stepTimeVariability = 0.0,
    this.stepLengthVariability = 0.0,
    this.kneeAngleVariability = 0.0,
    this.stanceTimeVariability = 0.0,
    this.avgGvi = 0.0,
    this.avgKneeAngle = 0.0,
    this.avgHipAngle = 0.0,
    this.cadenceVsBaseline = 0.0,
    this.gviVsBaseline = 0.0,
    this.kneeAmplitudeVsBaseline = 0.0,
    this.trend = 'stable',
    this.improvementScore = 0.0,
  });

  factory WalkingSession.fromJson(Map<String, dynamic> json) {
    double d(dynamic v) => (v is num) ? v.toDouble() : 0.0;
    String s(dynamic v) => v?.toString() ?? 'stable';

    return WalkingSession(
      stepCount: json['step_count'] ?? 0,
      cadence: d(json['cadence']),
      avgSpeed: d(json['avg_speed']),

      avgStanceTime: d(json['avg_stance_time']),
      avgSwingTime: d(json['avg_swing_time']),
      stanceSwingRatio: d(json['stance_swing_ratio']),

      kneeAngleMean: d(json['knee_angle_mean']),
      kneeAngleStd: d(json['knee_angle_std']),
      kneeAngleMax: d(json['knee_angle_max']),
      kneeAngleMin: d(json['knee_angle_min']),
      kneeAmplitude: d(json['knee_amplitude']),

      hipAngleMean: d(json['hip_angle_mean']),
      hipAngleStd: d(json['hip_angle_std']),
      hipAngleMax: d(json['hip_angle_max']),
      hipAngleMin: d(json['hip_angle_min']),
      hipAmplitude: d(json['hip_amplitude']),

      avgRoll: d(json['avg_roll']),
      avgPitch: d(json['avg_pitch']),
      avgYaw: d(json['avg_yaw']),

      kneeAngle: d(json['knee_angle']),
      hipAngle: d(json['hip_angle']),
      ankleAngle: d(json['ankle_angle']),

      gvi: d(json['gvi']),
      symmetryIndex: d(json['symmetry_index']),
      stepTimeVariability: d(json['step_time_variability']),
      stepLengthVariability: d(json['stride_length_variability']),
      kneeAngleVariability: d(json['knee_angle_variability']),
      stanceTimeVariability: d(json['stance_time_variability']),

      avgGvi: d(json['avg_gvi']),
      avgKneeAngle: d(json['avg_knee_angle']),
      avgHipAngle: d(json['avg_hip_angle']),
      cadenceVsBaseline: d(json['cadence_vs_baseline']),
      gviVsBaseline: d(json['gvi_vs_baseline']),
      kneeAmplitudeVsBaseline: d(json['knee_amplitude_vs_baseline']),
      trend: s(json['trend']),
      improvementScore: d(json['improvement_score']),
    );
  }
}