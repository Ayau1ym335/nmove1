import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart'; 
import 'walking_session.dart';

class UserData {

  String userId = '#00000001';
  String fullName = '';
  String email = '';
  String password = '';
  String city = '';
  String age = '';
  String gender = '';
String? biomechanicalAge;
  String weight = '';
  String height = '';
  String illnesses = '';
  String problem = '';
  String shoeSize = '';
  String legLength = '';
  String dominantLeg = '';

  String injuryType = '';
  String diagnosisDate = '';
  String selectedSide = ''; 
  Map<String, List<String>> selectedBodyParts = {
    'left': [],
    'right': [],
  };
  bool hasActivePain = false;
  bool hasPathology = false;
  bool hasEnoughSleep = false;
  double painLevel = 1.0;

  WalkingSession? lastSession; 
  String doctorName = '';
  String doctorEmail = '';
  
  List<double> progressData = List.filled(10, 0.0);
  List<String> progressMonths = List.filled(10, '');

  
  UserData();

factory UserData.fromJson(Map<String, dynamic> json) {
final Map<String, dynamic>? profile = json['profile'] is Map ? json['profile'] as Map<String, dynamic> : null;
  return UserData()
    // Бэкенд возвращает 'id', 'full_name' и 'email'
    ..userId = json['id']?.toString() ?? '#00000000'
    ..fullName = json['full_name'] ?? json['name'] ?? 'Unknown' 
    ..email = json['email'] ?? ''
    ..city = json['profile']?['notes'] ?? json['city'] ?? 'No City'
    ..age = json['profile']?['age']?.toString() ?? json['age']?.toString() ?? ''
    ..biomechanicalAge = profile?['biomechanical_age']?.toString() ?? 
                           json['biomechanical_age']?.toString() ?? '—';
}

  Future<Map<String, dynamic>> getFilteredProgress() async {
    final prefs = await SharedPreferences.getInstance();
    int level = prefs.getInt('user_subscription_level') ?? 0;

    if (level == 0) {
      if (progressData.length > 7) {
        return {
          'data': progressData.sublist(progressData.length - 7),
          'months': progressMonths.sublist(progressMonths.length - 7),
          'isRestricted': true,
        };
      }
    }
    return {
      'data': progressData,
      'months': progressMonths,
      'isRestricted': false,
    };
  }

  void updateProgress(List<double> newData, List<String> newMonths) {
    this.progressData = newData;
    this.progressMonths = newMonths;
  }

  double getImprovement({List<double>? specificData}) {
    final dataToCalculate = specificData ?? progressData;

    if (dataToCalculate.isEmpty || dataToCalculate.first == 0) return 0.0;
    
    double start = dataToCalculate.first;
    double end = dataToCalculate.last;
    
    return ((start - end).abs() / start) * 100;
  }

  void updateFromStep2({
    required String age,
    required String gender,
    required String weight,
    required String height,
    required String illnesses,
    required String problem,
    required String shoeSize,
    required String legLength,
    required String dominantLeg,
    required String city,
  }) {
    this.age = age;
    this.gender = gender;
    this.weight = weight;
    this.height = height;
    this.illnesses = illnesses;
    this.problem = problem;
    this.shoeSize = shoeSize;
    this.legLength = legLength;
    this.dominantLeg = dominantLeg;
    this.city = city;
  }

  void updateFromStep3({
    required String injuryType,
    required String diagnosisDate,
    required String side,
    required Map<String, List<String>> parts,
    required bool activePain,
    required bool pathology,
    required bool enoughSleep,
    required double pain,
  }) {
    this.injuryType = injuryType;
    this.diagnosisDate = diagnosisDate;
    this.selectedSide = side;
    this.selectedBodyParts = parts;
    this.hasActivePain = activePain;
    this.hasPathology = pathology;
    this.hasEnoughSleep = enoughSleep;
    this.painLevel = pain;
  }
}

class UserDataProvider extends InheritedWidget {
  final UserData userData;
  const UserDataProvider({super.key, required this.userData, required super.child});

  static UserDataProvider? of(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<UserDataProvider>();
  }

  @override
  bool updateShouldNotify(covariant UserDataProvider oldWidget) => true;
}