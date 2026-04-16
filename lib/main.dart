import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'user_data.dart';
import 'intro_screen.dart';
import 'doctor_patient_list.dart';
import 'link_doctor_screen.dart';
import 'profile_screen.dart';
import 'activity_progress_page.dart';
import 'walking_session.dart';         
import 'dart:typed_data';
import 'dart:io';
import 'package:http/http.dart' as http; 
import 'services/lib/services/gait_session_service.dart';
import 'package:shared_preferences/shared_preferences.dart'; 
import 'package:path_provider/path_provider.dart';
import 'dart:math' as math;
import 'RadarDetailPage.dart';
import 'Radar_painter.dart';


class IMUPacket {
  final int header;
  final double timestamp;
  final List<double> acc1; 
  final List<double> gyro1;
  final List<double> acc2; 
  final List<double> gyro2;

  IMUPacket({
    required this.header,
    required this.timestamp,
    required this.acc1,
    required this.gyro1,
    required this.acc2,
    required this.gyro2,
  });

  factory IMUPacket.fromBytes(Uint8List bytes) {
    final data = ByteData.view(bytes.buffer);
    int offset = 0;

    int header = data.getUint8(offset);
    offset += 1;

    double time = data.getFloat64(offset, Endian.little);
    offset += 8;

    List<double> readFloats(int count) {
      List<double> list = [];
      for (int i = 0; i < count; i++) {
        list.add(data.getFloat32(offset, Endian.little));
        offset += 4;
      }
      return list;
    }

    return IMUPacket(
      header: header,
      timestamp: time,
      acc1: readFloats(3),
      gyro1: readFloats(3),
      acc2: readFloats(3),
      gyro2: readFloats(3),
    );
  }
}

class DataService {
  static const String espUrl = "http://192.168.4.1/download";

  static Future<File> saveBytesToTempBin(Uint8List bytes) async {
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/session_data.bin');
    await file.writeAsBytes(bytes, flush: true);
    return file;
  }

static Future<List<IMUPacket>> fetchAndParseData() async {
  try {
    final response = await http
        .get(Uri.parse(espUrl))
        .timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      Uint8List allBytes = response.bodyBytes;
      
      if (allBytes.isEmpty) throw Exception("File is empty");

      int packetSize = 57; 
      List<IMUPacket> allPackets = [];

      for (int i = 0; i < allBytes.length; i += packetSize) {
        if (i + packetSize > allBytes.length) break;
        
        Uint8List packetBytes = allBytes.sublist(i, i + packetSize);
        allPackets.add(IMUPacket.fromBytes(packetBytes));
      }
      
      print("Parsed ${allPackets.length} packets successfully");
      return allPackets;
    } else {
      throw Exception("Server Error: ${response.statusCode}");
    }
  } catch (e) {
    print("Download error: $e");
    rethrow;
  }
}
static double calculateMovementIntensity(List<IMUPacket> packets) {
    if (packets.isEmpty) return 0.0;
    double totalForce = 0;
    
    for (var p in packets) {
      double force = math.sqrt(
        p.acc1[0] * p.acc1[0] + 
        p.acc1[1] * p.acc1[1] + 
        p.acc1[2] * p.acc1[2]
      );
      totalForce += force;
    }
    return totalForce / packets.length;
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  runApp(
    UserDataProvider(
      userData: UserData(),
      child: const NMoveApp(),
    ),
  );
}

class NMoveApp extends StatelessWidget {
  const NMoveApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark(),
      home: const IntroScreen(),
    );
  }
}

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final double screenWidth = MediaQuery.of(context).size.width;
    final double screenHeight = MediaQuery.of(context).size.height;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 30),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SizedBox(
                  height: screenHeight * 0.3,
                  child: Image.asset(
                    'assets/logo.png',
                    fit: BoxFit.contain,
                    errorBuilder: (context, error, stackTrace) =>
                        const Icon(Icons.flash_on, color: Colors.purpleAccent, size: 80),
                  ),
                ),

                SizedBox(height: screenHeight * 0.04),

                Text(
                  'Hello! Welcome to our application',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: screenWidth * 0.065, 
                    fontWeight: FontWeight.bold,
                  ),
                ),

                SizedBox(height: screenHeight * 0.05),

                _buildAuthButton(
                  context, 
                  'Login', 
                  const LinearGradient(colors: [Colors.cyan, Colors.purpleAccent]), 
                  false
                ),
                
                const SizedBox(height: 16),
                
                _buildAuthButton(
                  context, 
                  'Register', 
                  null, 
                  true, 
                  isBorder: true
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAuthButton(BuildContext context, String text, Gradient? gradient, bool isReg, {bool isBorder = false}) {
    return Container(
      width: double.infinity, 
      height: 55,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        gradient: gradient,
        border: isBorder ? Border.all(color: Colors.purpleAccent.withOpacity(0.5), width: 2) : null,
      ),
      child: TextButton(
        onPressed: () => Navigator.push(
          context, 
          MaterialPageRoute(builder: (context) => LoginScreen(isRegistration: isReg))
        ),
        child: Text(
          text, 
          style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)
        ),
      ),
    );
  }
}

class LoginScreen extends StatefulWidget {
  final bool isRegistration;
  const LoginScreen({super.key, this.isRegistration = false});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text.trim();

    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter email and password')),
      );
      return;
    }

    setState(() => _loading = true);

    try {
      if (widget.isRegistration) {
        // For registration, proceed to role/profile selection
        final provider = UserDataProvider.of(context);
        provider?.userData.email = email;
        provider?.userData.password = password;

        if (!mounted) return;
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => RoleSelectionScreen(
              initialEmail: email,
              initialPassword: password,
            ),
          ),
        );
        return;
      }

      // Login
      final role = await ApiService.login(email, password)
          .timeout(const Duration(seconds: 10));

      if (!mounted) return;

      if (role.toLowerCase() == 'doctor') {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const DoctorPatientListScreen()),
        );
      } else {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const MainAppPlaceholder()),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${widget.isRegistration ? "Registration" : "Login"} error: $e')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final screenHeight = MediaQuery.of(context).size.height;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 30),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                children: [
                  SizedBox(
                    height: screenHeight * 0.25,
                    child: Image.asset(
                      'assets/logo.png',
                      fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) =>
                          const Icon(Icons.image, color: Colors.cyan, size: 80),
                    ),
                  ),
                  Text(
                    'NMove',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: screenWidth * 0.08,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.isRegistration ? 'Create Account' : 'Welcome Back',
                    style: TextStyle(color: Colors.white70, fontSize: screenWidth * 0.045),
                  ),
                  SizedBox(height: screenHeight * 0.04),
                  GradientTextField(
                    controller: _emailController,
                    hintText: 'Email',
                    gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
                  ),
                  const SizedBox(height: 15),
                  GradientTextField(
                    controller: _passwordController,
                    hintText: 'Password',
                    gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
                    obscureText: true,
                  ),
                  SizedBox(height: screenHeight * 0.05),
                  Container(
                    width: double.infinity,
                    height: 55,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(15),
                      gradient:
                          const LinearGradient(colors: [Colors.pink, Colors.purpleAccent]),
                    ),
                    child: TextButton(
                      onPressed: _loading ? null : _handleSubmit,
                      child: _loading
                          ? const SizedBox(
                              width: 22,
                              height: 22,
                              child: CircularProgressIndicator(
                                  color: Colors.white, strokeWidth: 2),
                            )
                          : Text(
                              widget.isRegistration ? 'Next' : 'Sign In',
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold),
                            ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
class RoleSelectionScreen extends StatefulWidget {
  final String? initialEmail;
  final String? initialPassword;
  const RoleSelectionScreen({super.key, this.initialEmail, this.initialPassword});

  @override
  State<RoleSelectionScreen> createState() => _RoleSelectionScreenState();
}

class _RoleSelectionScreenState extends State<RoleSelectionScreen> {
  int selectedRole = 0;
  final TextEditingController _fullNameController = TextEditingController();
  final TextEditingController _cityController = TextEditingController();

  @override
  void dispose() {
    _fullNameController.dispose();
    _cityController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = UserDataProvider.of(context);
      if (provider != null) {
        if ((widget.initialEmail ?? '').isNotEmpty) {
          provider.userData.email = widget.initialEmail!.trim();
        }
        if ((widget.initialPassword ?? '').isNotEmpty) {
          provider.userData.password = widget.initialPassword!.trim();
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Column(
              children: [
                const SizedBox(height: 10),
                Container(
                  width: double.infinity,
                  height: 100,
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [Colors.pink, Colors.purpleAccent]),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    children: [
                      _roleTab('Doctor', 1, Icons.medical_services_outlined),
                      _buildDivider(),
                      _roleTab('User', 2, Icons.person_outline),
                    ],
                  ),
                ),
                
                const SizedBox(height: 30),

                if (selectedRole == 1) _buildDoctorForm(),
                if (selectedRole == 2) _buildUserFormStep1(),
                if (selectedRole == 0)
                  const Padding(
                    padding: EdgeInsets.only(top: 50),
                    child: Text("Select your role to continue", 
                      style: TextStyle(color: Colors.white54, fontSize: 16)),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
   Widget _roleTab(String label, int index, IconData icon) {
    final active = selectedRole == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => selectedRole = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          decoration: BoxDecoration(
            color: active ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(15),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: active ? Colors.black : Colors.white, size: 30),
              const SizedBox(height: 4),
              Text(label,
                  style: TextStyle(
                      color: active ? Colors.black : Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDivider() => Container(
      width: 1.5, height: 40, color: Colors.white24, margin: const EdgeInsets.symmetric(horizontal: 8));

  Widget _buildDoctorForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        GradientTextField(
          hintText: 'Full Name',
          gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
          controller: _fullNameController,
        ),
        const SizedBox(height: 10),
        GradientTextField(
          hintText: 'City',
          gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
          controller: _cityController,
        ),
        const SizedBox(height: 10),
        const GradientTextField(
            hintText: 'Workplace',
            gradient: LinearGradient(colors: [Colors.cyan, Colors.purple])),
        const SizedBox(height: 10),
        const GradientTextField(
            hintText: 'Specialization',
            gradient: LinearGradient(colors: [Colors.pink, Colors.purple])),
        const SizedBox(height: 10),
        const GradientTextField(
            hintText: 'License ID',
            gradient: LinearGradient(colors: [Colors.cyan, Colors.purple])),
        const SizedBox(height: 30),
        _confirmBtn(() => const DoctorPatientListScreen()),
      ],
    );
  }

  Widget _buildUserFormStep1() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        GradientTextField(
          hintText: 'Full Name',
          gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
          controller: _fullNameController,
        ),
        const SizedBox(height: 10),
        GradientTextField(
          hintText: 'City of residence',
          gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
          controller: _cityController,
        ),
        const SizedBox(height: 10),
        const GradientTextField(
            hintText: 'Do you have a device? (Optional)',
            gradient: LinearGradient(colors: [Colors.cyan, Colors.purple])),
        const SizedBox(height: 30),
        _confirmBtn(() => const UserStep2()),
      ],
    );
  }

  Widget _confirmBtn(Widget Function() next) {
    return Container(
      width: double.infinity,
      height: 55,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        gradient: const LinearGradient(colors: [Colors.pink, Colors.purpleAccent]),
      ),
      child: TextButton(
        onPressed: () {
          final provider = UserDataProvider.of(context);
          if (provider != null) {
            final name = _fullNameController.text.trim();
            final city = _cityController.text.trim();
            if (name.isNotEmpty) provider.userData.fullName = name;
            if (city.isNotEmpty) provider.userData.city = city;
          }
          Navigator.push(context, MaterialPageRoute(builder: (_) => next()));
        },
        child: const Text('Confirm',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
      ),
    );
  }
}


class UserStep2 extends StatefulWidget {
  const UserStep2({super.key});

  @override
  _UserStep2State createState() => _UserStep2State();
}

class _UserStep2State extends State<UserStep2> {
  String selectedGender = 'Gender';
  String selectedDominantLeg = 'Dominant leg';

  final ageController = TextEditingController();
  final weightController = TextEditingController();
  final heightController = TextEditingController();
  final illnessesController = TextEditingController();
  final problemController = TextEditingController();
  final shoeSizeController = TextEditingController();
  final legLengthController = TextEditingController();
  final cityController = TextEditingController();

  void _showPicker(String title, List<String> options, Function(String) onSelect) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1A1A1A),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(title, style: const TextStyle(color: Colors.white54, fontSize: 16)),
            const Divider(color: Colors.white10),
            ...options.map((option) => ListTile(
              title: Text(option, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 18)),
              onTap: () {
                onSelect(option);
                Navigator.pop(ctx);
              },
            )),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    ageController.dispose();
    weightController.dispose();
    heightController.dispose();
    illnessesController.dispose();
    problemController.dispose();
    shoeSizeController.dispose();
    legLengthController.dispose();
    cityController.dispose();
        super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        title: const Text("Health Details", style: TextStyle(color: Colors.white, fontSize: 18)),
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 400),
            child: Column(
              children: [
                _buildFieldTitle("General Information"),
                GradientTextField(
                  hintText: 'Age',
                  gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
                  controller: ageController,
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),

                _buildCustomPicker(
                  label: selectedGender, 
                  icon: Icons.wc, 
                  onTap: () => _showPicker("Select Gender", ["Male", "Female"], (val) => setState(() => selectedGender = val))
                ),
                const SizedBox(height: 12),

                GradientTextField(
                  hintText: 'Weight (kg)',
                  gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
                  controller: weightController,
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),

                GradientTextField(
                  hintText: 'Height (cm)',
                  gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
                  controller: heightController,
                  keyboardType: TextInputType.number,
                ),
                
                const SizedBox(height: 24),
                _buildFieldTitle("Medical & Physical"),

                GradientTextField(
                  hintText: 'Other illnesses',
                  gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
                  controller: illnessesController,
                ),
                const SizedBox(height: 12),

                GradientTextField(
                  hintText: 'Describe your problem',
                  gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
                  controller: problemController,
                ),
                const SizedBox(height: 12),

                GradientTextField(
                  hintText: 'Shoe size',
                  gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
                  controller: shoeSizeController,
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),

                GradientTextField(
                  hintText: 'Leg length (cm)',
                  gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
                  controller: legLengthController,
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),

                _buildCustomPicker(
                  label: selectedDominantLeg, 
                  icon: Icons.accessibility_new, 
                  onTap: () => _showPicker("Dominant Leg", ["Left", "Right"], (val) => setState(() => selectedDominantLeg = val))
                ),

                const SizedBox(height: 40),
                _nextBtn(),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFieldTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12, left: 4),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(title, style: const TextStyle(color: Colors.white38, fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
      ),
    );
  }

  Widget _buildCustomPicker({required String label, required IconData icon, required VoidCallback onTap}) {
    bool isPlaceholder = label.contains('Gender') || label.contains('Dominant');
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          border: Border.all(color: Colors.white10),
          borderRadius: BorderRadius.circular(15),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.purpleAccent, size: 20),
            const SizedBox(width: 12),
            Text(label, style: TextStyle(color: isPlaceholder ? Colors.grey : Colors.white, fontSize: 16)),
            const Spacer(),
            const Icon(Icons.keyboard_arrow_down, color: Colors.white24),
          ],
        ),
      ),
    );
  }

  Widget _nextBtn() {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        gradient: const LinearGradient(colors: [Colors.pink, Colors.purpleAccent]),
        boxShadow: [BoxShadow(color: Colors.pink.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      child: TextButton(
        onPressed: () {
          // Простая валидация: проверяем только Age и Weight для примера
          if (ageController.text.isEmpty || weightController.text.isEmpty) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text("Please fill in Age and Weight"), backgroundColor: Colors.pinkAccent),
            );
            return;
          }

          final provider = UserDataProvider.of(context);
          provider?.userData.updateFromStep2(
            age: ageController.text,
            gender: selectedGender,
            city: cityController.text,
            weight: weightController.text,
            height: heightController.text,
            illnesses: illnessesController.text,
            problem: problemController.text,
            shoeSize: shoeSizeController.text,
            legLength: legLengthController.text,
            dominantLeg: selectedDominantLeg,
          );

          Navigator.push(context, MaterialPageRoute(builder: (context) => const UserStep3()));
        },
        child: const Text('Next Step', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
      ),
    );
  }
}

class UserStep3 extends StatefulWidget {
  const UserStep3({super.key});

  @override
  _UserStep3State createState() => _UserStep3State();
}

class _UserStep3State extends State<UserStep3> {
  final injuryController = TextEditingController();
  final dateController = TextEditingController();

  double painLevel = 3;
  String selectedSide = ''; 
  Map<String, List<String>> selectedBodyParts = {
    'left': [],
    'right': [],
  };
  bool hasActivePain = false;
  bool hasPathology = false;
  bool hasEnoughSleep = false;

  final List<String> bodyParts = [
    'Thigh', 'Knee', 'Calf', 'Ankle', 'Foot',
    'Hip', 'Shin', 'Toes', 'Heel', 'Achilles'
  ];

  @override
  void dispose() {
    injuryController.dispose();
    dateController.dispose();
    super.dispose();
  }

  void _toggleBodyPart(String part) {
    setState(() {
      if (selectedSide == 'both') {
        final inBoth = selectedBodyParts['left']!.contains(part) &&
            selectedBodyParts['right']!.contains(part);
        if (inBoth) {
          selectedBodyParts['left']!.remove(part);
          selectedBodyParts['right']!.remove(part);
        } else {
          if (!selectedBodyParts['left']!.contains(part)) selectedBodyParts['left']!.add(part);
          if (!selectedBodyParts['right']!.contains(part)) selectedBodyParts['right']!.add(part);
        }
      } else {
        if (selectedBodyParts[selectedSide]!.contains(part)) {
          selectedBodyParts[selectedSide]!.remove(part);
        } else {
          selectedBodyParts[selectedSide]!.add(part);
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
        title: const Text('Injury Details',
            style: TextStyle(color: Colors.white, fontSize: 18)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GradientTextField(
                controller: injuryController,
                hintText: 'Injury type',
                gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple])),
            const SizedBox(height: 12),
            GradientTextField(
                controller: dateController,
                hintText: 'Date of diagnosis (DD.MM.YYYY)',
                gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
                keyboardType: TextInputType.datetime),
            const SizedBox(height: 35),
            const Text('Which side is affected?',
                style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            Row(children: [
              _sideBtn('Left', 'left'),
              _sideBtn('Right', 'right'),
              _sideBtn('Both', 'both'),
            ]),
            if (selectedSide.isNotEmpty) ...[
              const SizedBox(height: 35),
              Row(children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                      color: Colors.purpleAccent, borderRadius: BorderRadius.circular(8)),
                  child: Text(
                    selectedSide == 'both' ? 'L+R' : selectedSide[0].toUpperCase(),
                    style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
                  ),
                ),
                const SizedBox(width: 12),
                const Text('Select affected parts:',
                    style: TextStyle(color: Colors.white, fontSize: 16)),
              ]),
              const SizedBox(height: 20),
              _bodyPartsGrid(),
            ],
            const SizedBox(height: 35),
            _statusSwitches(),
            const SizedBox(height: 35),
            _painSlider(),
            const SizedBox(height: 40),
            _finishBtn(),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _sideBtn(String label, String side) {
    final active = selectedSide == side;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => selectedSide = side),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: const EdgeInsets.symmetric(horizontal: 4),
          height: 50,
          decoration: BoxDecoration(
            color: active ? Colors.purpleAccent.withOpacity(0.15) : Colors.white.withOpacity(0.02),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: active ? Colors.purpleAccent : Colors.white10, width: 1.2),
          ),
          child: Center(
            child: Text(label,
                style: TextStyle(
                    color: active ? Colors.white : Colors.white38,
                    fontSize: 14,
                    fontWeight: active ? FontWeight.bold : FontWeight.normal)),
          ),
        ),
      ),
    );
  }

  Widget _bodyPartsGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 3, childAspectRatio: 2.3, crossAxisSpacing: 10, mainAxisSpacing: 10),
      itemCount: bodyParts.length,
      itemBuilder: (_, i) {
        final part = bodyParts[i];
        final active = selectedSide == 'left'
            ? selectedBodyParts['left']!.contains(part)
            : selectedSide == 'right'
                ? selectedBodyParts['right']!.contains(part)
                : (selectedBodyParts['left']!.contains(part) ||
                    selectedBodyParts['right']!.contains(part));
        return GestureDetector(
          onTap: () => _toggleBodyPart(part),
          child: Container(
            decoration: BoxDecoration(
              color: active
                  ? Colors.purpleAccent.withOpacity(0.2)
                  : Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: active ? Colors.purpleAccent : Colors.white10),
            ),
            child: Center(
              child: Text(part,
                  style: TextStyle(
                      color: active ? Colors.white : Colors.white38, fontSize: 12)),
            ),
          ),
        );
      },
    );
  }

  Widget _statusSwitches() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(15),
          border: Border.all(color: Colors.white10)),
      child: Column(children: [
        _toggle('Active pain right now?', hasActivePain, (v) => setState(() => hasActivePain = v)),
        _toggle('Chronic pathology?', hasPathology, (v) => setState(() => hasPathology = v)),
        _toggle('Getting enough sleep?', hasEnoughSleep, (v) => setState(() => hasEnoughSleep = v)),
      ]),
    );
  }

  Widget _toggle(String title, bool value, void Function(bool) onChange) => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(color: Colors.white70)),
          Switch(value: value, onChanged: onChange, activeColor: Colors.purpleAccent),
        ],
      );

  Widget _painSlider() {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        const Text('Pain Level',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        Text('${painLevel.toInt()}',
            style: const TextStyle(
                color: Colors.purpleAccent, fontSize: 24, fontWeight: FontWeight.bold)),
      ]),
      Slider(
        value: painLevel,
        min: 1,
        max: 5,
        divisions: 4,
        activeColor: Colors.purpleAccent,
        onChanged: (v) => setState(() => painLevel = v),
      ),
    ]);
  }

  Widget _finishBtn() {
    return Container(
      width: double.infinity,
      height: 55,
      decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(15),
          gradient: const LinearGradient(colors: [Colors.pink, Colors.purpleAccent])),
      child: TextButton(
        onPressed: () async {
          final provider = UserDataProvider.of(context);
          if (provider != null) {
            provider.userData.updateFromStep3(
              injuryType: injuryController.text,
              diagnosisDate: dateController.text,
              side: selectedSide,
              parts: selectedBodyParts,
              activePain: hasActivePain,
              pathology: hasPathology,
              enoughSleep: hasEnoughSleep,
              pain: painLevel,
            );

            // Now register the patient with all collected data
            final ud = provider.userData;
            try {
              await ApiService.register(
                email: ud.email ?? '',
                password: ud.password ?? '',
                fullName: ud.fullName ?? '',
                role: 'patient',
                city: ud.city,
                gender: ud.gender,
                age: ud.age,
                weight: ud.weight,
                height: ud.height,
                dominantLeg: ud.dominantLeg,
                shoeSize: ud.shoeSize,
                legLength: ud.legLength,
              );
            } catch (e) {
              // Non-blocking: log and continue (duplicate users are handled gracefully)
              debugPrint('Registration error: $e');
            }
          }

          if (!mounted) return;
          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(builder: (_) => const LinkDoctorScreen()),
            (route) => false,
          );
        },
        child: const Text('Finish',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
      ),
    );
  }
}


class GradientTextField extends StatelessWidget {
  final String hintText;
  final Gradient gradient;
  final TextEditingController? controller;
  final bool obscureText;
  final TextInputType? keyboardType;

  const GradientTextField({
    super.key,
    required this.hintText,
    required this.gradient,
    this.controller,
    this.obscureText = false,
    this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(1.5),
      decoration: BoxDecoration(gradient: gradient, borderRadius: BorderRadius.circular(12)),
      child: Container(
        decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(11)),
        child: TextField(
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
            hintText: hintText,
            hintStyle: const TextStyle(color: Colors.grey, fontSize: 14),
            border: InputBorder.none,
          ),
        ),
      ),
    );
  }
}


class MainAppPlaceholder extends StatefulWidget {
  final String userName;
  const MainAppPlaceholder({super.key, this.userName = 'User'});
  

  @override
  State<MainAppPlaceholder> createState() => _MainAppPlaceholderState();
}

class _MainAppPlaceholderState extends State<MainAppPlaceholder> {
  static const bool _useEspDownload = false;

  WalkingSession? currentSession;
  int selectedIndex = 0;
  bool isDeviceConnected = false;
  int legAge = 24;
  String ageMessage = 'Calculating...';
  final _homePageController = PageController();
  bool _backendReachable = false;
  bool _tokenPresent = false;

double _toDouble(dynamic v) {
    if (v is num) return v.toDouble();
    return double.tryParse(v?.toString() ?? '') ?? 0.0;
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadUserData();
      _refreshDebugStatus();
    });
  }

  Future<void> _refreshDebugStatus() async {
    final prefs = await SharedPreferences.getInstance();
    final token = (prefs.getString('access_token') ?? '').trim();
    bool backendOk = false;
    try {
      backendOk = await ApiService.healthCheck();
    } catch (_) {}
    if (!mounted) return;
    setState(() {
      _tokenPresent = token.isNotEmpty;
      _backendReachable = backendOk;
    });
  }

Future<void> _loadUserData() async {
  try {
    final data = await ApiService.getMe();
    
    if (!mounted) return;

    final ud = UserDataProvider.of(context)?.userData;
    if (ud != null) {
      ud.fullName = (data['full_name'] ?? data['name'] ?? ud.fullName).toString();
      ud.email = (data['email'] ?? ud.email).toString();
      ud.userId = (data['id'] ?? ud.userId).toString();
      
      final userId = ud.userId;
      if (userId.isNotEmpty) {
        try {
          final summary = await ApiService.getDashboardSummary(userId);
          
          if (!mounted) return; // Еще одна проверка перед setState

          final movementAgeValue = summary['movement_age']?['movement_age'];
          final movementAge = _toDouble(movementAgeValue);
          
          if (movementAge > 0) {
            final userAge = int.tryParse(ud.age) ?? 25;
            final mAgeRounded = movementAge.round();
            final diff = (userAge - mAgeRounded).abs();
            
            setState(() {
              legAge = mAgeRounded;
              if (mAgeRounded < userAge) {
                ageMessage = 'Your leg is $diff years younger than you!';
              } else if (mAgeRounded > userAge) {
                ageMessage = 'Your leg is $diff years older than you!';
              } else {
                ageMessage = 'Your leg age matches your real age!';
              }
            });
          }
        } catch (e) {
          debugPrint('Summary error: $e');
        }
      }
    }
  } catch (e) {
    if (!mounted) return;
    setState(() => ageMessage = 'Sync your device');
    debugPrint('loadUserData error: $e');
  }
}

  Future<void> _syncViaWifi() async {
    setState(() => ageMessage = 'Initializing connection...');

    try {
      Uint8List? binData;

      if (_useEspDownload) {
        setState(() => ageMessage = 'Step 1/4: Downloading from ESP32...');
        try {
          final resp = await http
              .get(Uri.parse('http://192.168.4.1/download'))
              .timeout(const Duration(seconds: 8));
          if (resp.statusCode == 200 && resp.bodyBytes.isNotEmpty) {
            binData = resp.bodyBytes;
          } else {
            setState(() => ageMessage = 'ESP not connected. Checking backend...');
          }
        } catch (_) {
          setState(() => ageMessage = 'ESP not available. Checking backend...');
        }
      } else {
        setState(() => ageMessage = 'ESP mode off. Checking backend...');
      }

      // Step 2: Verify token
      setState(() => ageMessage = 'Step 2/4: Checking session...');
      final prefs = await SharedPreferences.getInstance();
      final token = (prefs.getString('access_token') ?? '').trim();
      if (token.isEmpty) throw 'No access token. Please login first.';

      // Step 3: Start session via GaitSessionService
      setState(() => ageMessage = 'Step 3/4: Starting session...');
      final gaitService = GaitSessionService(authToken: token);
      final sessionId = await gaitService.startSessionOnBackend();
      if (sessionId == null || sessionId.isEmpty) {
        throw 'Failed to start backend session.';
      }

      if (binData == null) {
        setState(() {
          isDeviceConnected = false;
          ageMessage = 'Backend OK. Session #$sessionId started. Connect ESP to upload data.';
        });
        return;
      }

      setState(() => ageMessage = 'Step 4/4: Uploading .bin to backend...');
      final tempFile = await DataService.saveBytesToTempBin(binData);
      final uploaded = await gaitService.uploadBinToBackend(
        sessionId: sessionId,
        binFile: tempFile,
        legSide: 'left',
        sensorSlot: 1,
        deviceId: 'esp32',
      );
      if (!uploaded) throw 'Upload to backend failed.';

      setState(() => ageMessage = 'Processing on backend...');
      final sessionData = await gaitService.waitForSessionDone(sessionId);
      if (sessionData != null) {
        final snapshots = (sessionData['metrics_snapshots'] as List?) ?? [];
        final latest =
            snapshots.isNotEmpty && snapshots.last is Map<String, dynamic>
                ? snapshots.last as Map<String, dynamic>
                : <String, dynamic>{};

        final mapped = WalkingSession(
          stepCount: (sessionData['reading_count'] ?? 1) as int,
          cadence: _toDouble(latest['cadence']),
          symmetryIndex: _toDouble(latest['symmetry_score']) * 100,
          gvi: _toDouble(latest['stability_score']) * 100,
        );
        currentSession = mapped;
        UserDataProvider.of(context)?.userData.lastSession = mapped;

        final movAge = _toDouble(latest['movement_age']);
        if (movAge > 0) legAge = movAge.round();
      }

// ... в конце блока try внутри _syncViaWifi ...
      setState(() {
        isDeviceConnected = true;
        ageMessage = 'Session uploaded successfully.';
        // 1. Переключаем нижний BottomNavigationBar на первую вкладку (Home)
        selectedIndex = 0; 
      });

      Future.delayed(const Duration(milliseconds: 300), () {
        if (_homePageController.hasClients) {
          _homePageController.animateToPage(
            1, // Переходим на HeroPage (или 0, если хочешь сначала Hero)
            duration: const Duration(milliseconds: 800),
            curve: Curves.easeInOut,
          );
        }
      });

    } on http.ClientException {
      _handleSyncError('Network error: Check Wi-Fi connection.');
    } catch (e) {
      _handleSyncError(e.toString());
    }
  }

  void _handleSyncError(String error) {
    debugPrint('Sync error: $error');
    setState(() {
      isDeviceConnected = false;
      ageMessage = error;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(error), backgroundColor: Colors.redAccent),
    );
  }

  @override
  Widget build(BuildContext context) {
final tabs = [
  isDeviceConnected ? _buildVerticalHome() : _buildConnectScreen(),
  const ActivityProgressPage(),
  // Это страница с метриками и Baseline (из твоего отдельного файла)
  RadarDetailPage(homeController: _homePageController), 
  const ProfileScreen(),
];

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: IndexedStack(index: selectedIndex, children: tabs),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: selectedIndex,
        onTap: (i) => setState(() => selectedIndex = i),
        backgroundColor: Colors.black,
        selectedItemColor: Colors.cyanAccent,
        unselectedItemColor: Colors.white24,
        type: BottomNavigationBarType.fixed,
        showSelectedLabels: false,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_filled), label: ''),
          BottomNavigationBarItem(icon: Icon(Icons.query_stats), label: ''),
          BottomNavigationBarItem(icon: Icon(Icons.auto_awesome), label: ''),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: ''),
        ],
      ),
    );
  }

Widget _buildVerticalHome() {
  return PageView(
    controller: _homePageController,
    scrollDirection: Axis.vertical,
    children: [
      _buildHeroPage(),  // Главная с кнопкой "Start"
      _buildRadarPage(), // Чистый радар (график)
    ],
  );
}

  Widget _buildHeroPage() {
    return SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(children: [
          const Text('NMove',
              style: TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Text('Welcome, ${widget.userName}!',
              style: const TextStyle(
                  color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 40),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text('$legAge',
                style: const TextStyle(
                    color: Colors.cyanAccent, fontSize: 60, fontWeight: FontWeight.bold)),
            const SizedBox(width: 15),
            Flexible(
                child: Text(ageMessage,
                    style: const TextStyle(color: Colors.white70, fontSize: 16))),
          ]),
          Container(
            margin: const EdgeInsets.symmetric(vertical: 30),
            height: 250,
            child: Image.asset('assets/leg_glow.png', fit: BoxFit.contain),
          ),
          const SizedBox(height: 50),
          _neonButton('Go to Radar Chart', () {
            _homePageController.animateToPage(1,
                duration: const Duration(milliseconds: 500), curve: Curves.easeOut);
          }),
          const Icon(Icons.keyboard_arrow_down, color: Colors.white24, size: 30),
        ]),
      ),
    );
  }

  Widget _neonButton(String text, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        height: 55,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(15),
          gradient: const LinearGradient(colors: [Colors.purple, Colors.blueAccent]),
          boxShadow: [BoxShadow(color: Colors.purple.withOpacity(0.3), blurRadius: 10)],
        ),
        child: Center(child: Text(text, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
      ),
    );
  }

Widget _buildRadarPage() {
  return Container(
    color: Colors.black,
    padding: const EdgeInsets.all(20),
    child: Column(children: [
      IconButton(
        icon: const Icon(Icons.keyboard_arrow_up, color: Colors.cyanAccent, size: 40),
        onPressed: () => _homePageController.animateToPage(
          0,
          duration: const Duration(milliseconds: 500),
          curve: Curves.easeOut,
        ),
      ),
      const Text('Movement Radar',
          style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold)),
      Expanded(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: AspectRatio(
            aspectRatio: 1,
            child: CustomPaint(painter: RadarChartPainter()), // Использует класс рисовальщика
          ),
        ),
      ),
      const Text('Swipe up to go back',
          style: TextStyle(color: Colors.white24, fontSize: 12)),
      const SizedBox(height: 10),
    ]),
  );
}

  Widget _buildConnectScreen() {
    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 40),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text('NMove',
              style: TextStyle(
                  color: Colors.cyanAccent, fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 40),
          const Text('Sync Your Data',
              style: TextStyle(
                  color: Colors.white, fontSize: 26, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          Image.asset('assets/leg_glow.png', height: 200, fit: BoxFit.contain,
              errorBuilder: (_, __, ___) =>
                  const Icon(Icons.wifi_tethering, size: 100, color: Colors.white10)),
          const SizedBox(height: 20),
          _sensorCard('Data Hub (ESP32)', isDeviceConnected ? 'Connected' : 'Not Found',
              isDeviceConnected),
          _sensorCard('Cloud Sync', 'Ready', true),
          const SizedBox(height: 10),
          _debugStatusCard(),
          const SizedBox(height: 50),
          GestureDetector(
            onTap: isDeviceConnected ? null : _syncViaWifi,
            child: Container(
              height: 65,
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(15),
                gradient: const LinearGradient(
                    colors: [Color(0xFF8E2DE2), Color(0xFFF00000)]),
              ),
              child: const Center(
                child: Text('Download Data',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold)),
              ),
            ),
          ),
          const SizedBox(height: 20),
          Text(ageMessage,
              style: const TextStyle(color: Colors.white24, fontSize: 12),
              textAlign: TextAlign.center),
        ]),
      ),
    );
  }

  Widget _debugStatusCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white10)),
      child: Row(children: [
        Expanded(
          child: Text(
            _backendReachable ? 'Backend: OK' : 'Backend: FAIL',
            style: TextStyle(
                color: _backendReachable ? Colors.cyanAccent : Colors.redAccent,
                fontSize: 12,
                fontWeight: FontWeight.bold),
          ),
        ),
        Expanded(
          child: Text(
            _tokenPresent ? 'Token: Present' : 'Token: Missing',
            textAlign: TextAlign.right,
            style: TextStyle(
                color: _tokenPresent ? Colors.cyanAccent : Colors.redAccent,
                fontSize: 12,
                fontWeight: FontWeight.bold),
          ),
        ),
      ]),
    );
  }

  Widget _sensorCard(String name, String status, bool connected) {
    return Container(
      margin: const EdgeInsets.only(bottom: 15),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: const Color(0xFF111111),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: connected ? Colors.cyanAccent : Colors.white10)),
      child: Row(children: [
        Icon(connected ? Icons.bluetooth_connected : Icons.bluetooth_searching,
            color: connected ? Colors.cyanAccent : Colors.white24),
        const SizedBox(width: 15),
        Text(name, style: const TextStyle(color: Colors.white)),
        const Spacer(),
        Text(status, style: TextStyle(color: connected ? Colors.cyanAccent : Colors.white24)),
      ]),
    );
  }
}


class PremiumGuard extends StatelessWidget {
  final Widget child;
  final int requiredLevel;

  const PremiumGuard({super.key, required this.child, this.requiredLevel = 1});

  Future<int> _level() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt('user_subscription_level') ?? 0;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<int>(
      future: _level(),
      builder: (_, snap) {
        if ((snap.data ?? 0) >= requiredLevel) return child;
        return Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(color: Colors.white10)),
          child: Column(children: [
            const Icon(Icons.lock_outline, color: Color(0xFF00E5FF), size: 30),
            const SizedBox(height: 10),
            Text(
              'Available in ${requiredLevel == 1 ? 'Plus' : 'Pro'} Plan',
              style: const TextStyle(color: Colors.white70, fontSize: 14),
            ),
          ]),
        );
      },
    );
  }
}