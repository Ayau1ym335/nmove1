import 'dart:convert';

class WalkingSession {
  final int stepCount;
  final double avgSpeed;
  final double cadence;
  final double avgPeakAngularVelocity;

  final double stanceTimeLeft;
  final double stanceTimeRight;
  final double swingTimeLeft;
  final double swingTimeRight;
  final double stepTimeLeft;
  final double stepTimeRight;
  final double strideTimeLeft;
  final double strideTimeRight;
  final double doubleSupportTime;
  final double singleSupportTime;
  final double loadingResponseTime;
  final double preSwingTime;

  final double strideLength;
  final double stepWidth;
  final double verticalOscillation;
  final double kneeAmplitudeLeft;
  final double kneeAmplitudeRight;
  final double hipAmplitudeLeft;
  final double hipAmplitudeRight;
  final double kneeAngleMean;
  final double kneeAngleMax;
  final double hipAngleMean;
  final double hipAngleMin;
  final double ankleRangeOfMotion;
  final double trunkSway;
  final double footStrikeAngle;
  final double toeOffAngle;
  final double avgRoll;
  final double avgPitch;
  final double avgYaw;

  final double gvi;
  final double symmetryIndex;
  final double stepTimeVariability;
  final double strideLengthVariability;
  final double kneeAngleVariability;
  final double stanceTimeVariability;
  final double groundImpactForce;
  final double propulsionForce;
  final double energyCost;

  WalkingSession({
    this.stepCount = 0,
    this.avgSpeed = 0.0,
    this.cadence = 0.0,
    this.avgPeakAngularVelocity = 0.0,
    this.stanceTimeLeft = 0.0,
    this.stanceTimeRight = 0.0,
    this.swingTimeLeft = 0.0,
    this.swingTimeRight = 0.0,
    this.stepTimeLeft = 0.0,
    this.stepTimeRight = 0.0,
    this.strideTimeLeft = 0.0,
    this.strideTimeRight = 0.0,
    this.doubleSupportTime = 0.0,
    this.singleSupportTime = 0.0,
    this.loadingResponseTime = 0.0,
    this.preSwingTime = 0.0,
    this.strideLength = 0.0,
    this.stepWidth = 0.0,
    this.verticalOscillation = 0.0,
    this.kneeAmplitudeLeft = 0.0,
    this.kneeAmplitudeRight = 0.0,
    this.hipAmplitudeLeft = 0.0,
    this.hipAmplitudeRight = 0.0,
    this.kneeAngleMean = 0.0,
    this.kneeAngleMax = 0.0,
    this.hipAngleMean = 0.0,
    this.hipAngleMin = 0.0,
    this.ankleRangeOfMotion = 0.0,
    this.trunkSway = 0.0,
    this.footStrikeAngle = 0.0,
    this.toeOffAngle = 0.0,
    this.avgRoll = 0.0,
    this.avgPitch = 0.0,
    this.avgYaw = 0.0,
    this.gvi = 0.0,
    this.symmetryIndex = 0.0,
    this.stepTimeVariability = 0.0,
    this.strideLengthVariability = 0.0,
    this.kneeAngleVariability = 0.0,
    this.stanceTimeVariability = 0.0,
    this.groundImpactForce = 0.0,
    this.propulsionForce = 0.0,
    this.energyCost = 0.0,
  });

  factory WalkingSession.fromJson(Map<String, dynamic> json) {
    double d(dynamic v) => (v ?? 0.0).toDouble();

    return WalkingSession(
      stepCount: json['step_count'] ?? 0,
      avgSpeed: d(json['avg_speed']),
      cadence: d(json['cadence']),
      avgPeakAngularVelocity: d(json['avg_peak_angular_velocity']),

      stanceTimeLeft: d(json['stance_time_left']),
      stanceTimeRight: d(json['stance_time_right']),
      swingTimeLeft: d(json['swing_time_left']),
      swingTimeRight: d(json['swing_time_right']),
      stepTimeLeft: d(json['step_time_left']),
      stepTimeRight: d(json['step_time_right']),
      strideTimeLeft: d(json['stride_time_left']),
      strideTimeRight: d(json['stride_time_right']),
      doubleSupportTime: d(json['double_support_time']),
      singleSupportTime: d(json['single_support_time']),
      loadingResponseTime: d(json['loading_response_time']),
      preSwingTime: d(json['pre_swing_time']),

      strideLength: d(json['stride_length']),
      stepWidth: d(json['step_width']),
      verticalOscillation: d(json['vertical_oscillation']),
      kneeAmplitudeLeft: d(json['knee_amplitude_left']),
      kneeAmplitudeRight: d(json['knee_amplitude_right']),
      hipAmplitudeLeft: d(json['hip_amplitude_left']),
      hipAmplitudeRight: d(json['hip_amplitude_right']),
      kneeAngleMean: d(json['knee_angle_mean']),
      kneeAngleMax: d(json['knee_angle_max']),
      hipAngleMean: d(json['hip_angle_mean']),
      hipAngleMin: d(json['hip_angle_min']),
      ankleRangeOfMotion: d(json['ankle_range_of_motion']),
      trunkSway: d(json['trunk_sway']),
      footStrikeAngle: d(json['foot_strike_angle']),
      toeOffAngle: d(json['toe_off_angle']),
      avgRoll: d(json['avg_roll']),
      avgPitch: d(json['avg_pitch']),
      avgYaw: d(json['avg_yaw']),

      gvi: d(json['gvi']),
      symmetryIndex: d(json['symmetry_index']),
      stepTimeVariability: d(json['step_time_variability']),
      strideLengthVariability: d(json['stride_length_variability']),
      kneeAngleVariability: d(json['knee_angle_variability']),
      stanceTimeVariability: d(json['stance_time_variability']),
      groundImpactForce: d(json['ground_impact_force']),
      propulsionForce: d(json['propulsion_force']),
      energyCost: d(json['energy_cost']),
    );
  }
}