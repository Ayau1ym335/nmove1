import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'user_data.dart';
import 'subscription_screen.dart';
import 'services/api_service.dart';
import 'main.dart';
import 'config.dart';
import 'app_texts.dart';
import 'package:url_launcher/url_launcher.dart';

class ProfileScreen extends StatefulWidget {
  final bool isBluetoothConnected;
  final int upperBattery;
  final int lowerBattery;

  const ProfileScreen({
    super.key,
    this.isBluetoothConnected = false,
    this.upperBattery = 0,
    this.lowerBattery = 0,
  });

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final Color neonCyan = const Color(0xFF00E5FF);
  final Color neonPink = const Color(0xFFFF007F);

  @override
  Widget build(BuildContext context) {
    final userDataProvider = UserDataProvider.of(context);
    if (userDataProvider == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final userData = userDataProvider.userData;

    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              // Заголовок
              Row(
                children: [
                  Text("N", style: TextStyle(color: neonCyan, fontSize: 32, fontWeight: FontWeight.bold)),
                  const Text("Move ", style: TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                  const Expanded(
                    child: Text("Profile&Settings",
                        style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w300),
                        overflow: TextOverflow.ellipsis),
                  ),
                ],
              ),
              const SizedBox(height: 30),
              Row(
                children: [
                  Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      CircleAvatar(
                        radius: 45,
                        backgroundColor: neonCyan.withOpacity(0.1),
                        child: const Icon(Icons.person, size: 55, color: Colors.white),
                      ),
                      GestureDetector(
                        onTap: () => _showEditDialog(userData),
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: neonPink,
                            shape: BoxShape.circle,
                            border: Border.all(color: Colors.black, width: 2),
                          ),
                          child: const Icon(Icons.edit, color: Colors.white, size: 16),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(width: 20),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          userData.fullName.isEmpty ? "User Name" : userData.fullName,
                          style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
                        ),
                        Text(
                        "#${userData.userId}", 
                        style: TextStyle(color: neonCyan.withOpacity(0.7), fontSize: 14),
                        ),
                        const Text("Premium Member", style: TextStyle(color: Colors.grey, fontSize: 14)),
                        const SizedBox(height: 10),
                        GestureDetector(
                          onTap: () {
                            Navigator.push(context, MaterialPageRoute(builder: (context) => const SubscriptionScreen()));
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: neonCyan, width: 1.5),
                            ),
                            child: const Text("Manage My Premium", style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 40),
              const Text("My Parametres", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 15),
              _buildParamGrid(userData),
              const SizedBox(height: 30),
              const Text("Hardware", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 15),
              _buildHardwareBlock(),
              const SizedBox(height: 15),
              GestureDetector(
                onTap: () {},
                child: _buildNeonButton("Recalibrate Sensors", neonCyan),
              ),
              const SizedBox(height: 40),
              const Divider(color: Colors.white24, thickness: 1),
              const SizedBox(height: 15),
              const Text("Data & Privacy", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              _buildNeonBorderContainer("Data Privacy: Secured\nEncryption: Active", neonPink),
              const SizedBox(height: 35),
const SizedBox(height: 20),
_buildDownloadReportButton(userData),
const SizedBox(height: 20),
_buildLogoutButton(),
            ],
          ),
        ),
      ),
    );
  }
Widget _buildDownloadReportButton(dynamic userData) {
  return GestureDetector(
    onTap: () => _generateAndOpenReport(userData),
    child: Container(
      width: double.infinity,
      height: 55,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        gradient: LinearGradient(colors: [Colors.redAccent, Colors.deepOrange.shade900]),
        boxShadow: [
          BoxShadow(color: Colors.redAccent.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 4)),
        ],
      ),
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.picture_as_pdf, color: Colors.white, size: 22),
          SizedBox(width: 10),
          Text("Download PDF Report", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
        ],
      ),
    ),
  );
}

Future<void> _generateAndOpenReport(UserData userData) async {
  try {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text("Generating report..."), backgroundColor: Colors.redAccent),
    );

    final result = await ApiService.createDoctorPatientReport(userData.userId);
    final taskId = result['task_id']?.toString() ?? '';
    if (taskId.isEmpty) throw Exception('No task ID returned');

    String? pdfUrl;
    for (int i = 0; i < 20; i++) {
      await Future.delayed(const Duration(seconds: 3));
      final status = await ApiService.getDoctorReportStatus(userData.userId, taskId);
      if (status['status'] == 'completed' || status['url'] != null) {
        pdfUrl = status['url']?.toString();
        break;
      }
    }

    if (pdfUrl == null) throw Exception('Report generation timed out');

    final uri = Uri.parse(pdfUrl);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }

  } catch (e) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text("Error: ${e.toString()}"), backgroundColor: Colors.redAccent),
    );
  }
}

  Widget _buildParamGrid(dynamic userData) {
  return Column(
    children: [
      Container(
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: Colors.white.withOpacity(0.05), // Тёмный фон намекает, что менять нельзя
          border: Border.all(color: Colors.white10),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text("User Account ID", style: TextStyle(color: Colors.grey, fontSize: 14)),
            Text(
              "#${userData.userId}", 
              style: TextStyle(color: neonCyan, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
      Row(children: [
        _paramBadge("Age: ${userData.age}"),
        const SizedBox(width: 10),
        _paramBadge("Weight: ${userData.weight} kg")
      ]),
      const SizedBox(height: 10),
      Row(children: [
        _paramBadge("Gender: ${userData.gender}"),
        const SizedBox(width: 10),
        _paramBadge("Height: ${userData.height} cm")
      ]),
    ],
  );
}

  Widget _paramBadge(String text) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: neonPink.withOpacity(0.4)),
        ),
        child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 14)),
      ),
    );
  }

  Widget _buildHardwareBlock() {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: neonCyan, width: 2),
      ),
      child: IntrinsicHeight(
        child: Row(
          children: [
            _sensorInfo("Upper Leg Sensor", widget.upperBattery, widget.isBluetoothConnected),
            VerticalDivider(color: neonCyan, thickness: 1, width: 1, indent: 15, endIndent: 15),
            _sensorInfo("Lower Leg Sensor", widget.lowerBattery, widget.isBluetoothConnected),
          ],
        ),
      ),
    );
  }

  Widget _sensorInfo(String label, int battery, bool connected) {
    return Expanded(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 10),
        child: Column(
          children: [
            Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.memory, color: connected ? neonCyan : Colors.grey, size: 28),
                const SizedBox(width: 8),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(connected ? "$battery%" : "--%", style: TextStyle(color: connected ? neonCyan : Colors.grey, fontWeight: FontWeight.bold, fontSize: 16)),
                    Text(connected ? "Connected" : "Offline", style: TextStyle(color: connected ? neonCyan : Colors.redAccent, fontSize: 9)),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNeonButton(String text, Color color) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 14),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(12), border: Border.all(color: color, width: 2)),
      child: Text(text, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
    );
  }

  Widget _buildNeonBorderContainer(String text, Color color) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(15), border: Border.all(color: color.withOpacity(0.5))),
      child: Text(text, style: const TextStyle(color: Colors.white, height: 1.6, fontSize: 14)),
    );
  }

  Widget _buildLogoutButton() {
    return GestureDetector(
      onTap: () async {
        await ApiService.logout();
        if (!mounted) return;
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (context) => const WelcomeScreen()),
          (route) => false,
        );
      },
      child: Container(
      width: double.infinity,
      height: 55,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(15),
        gradient: LinearGradient(colors: [neonPink, Colors.purple.shade900]),
      ),
      child: const Center(child: Text("Log Out", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16))),
    ),
    );
  }

  void _showEditDialog(dynamic userData) {
    final nameController = TextEditingController(text: userData.fullName);
    final ageController = TextEditingController(text: userData.age.toString());
    final weightController = TextEditingController(text: userData.weight.toString());
    final heightController = TextEditingController(text: userData.height.toString());

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.black,
        shape: RoundedRectangleBorder(side: BorderSide(color: neonCyan), borderRadius: BorderRadius.circular(15)),
        title: const Text("Edit Parameters", style: TextStyle(color: Colors.white)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildEditField(nameController, "Name"),
              _buildEditField(ageController, "Age", isNumber: true),
              _buildEditField(weightController, "Weight (kg)", isNumber: true),
              _buildEditField(heightController, "Height (cm)", isNumber: true),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("Cancel", style: TextStyle(color: Colors.white54))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: neonPink),
            onPressed: () async {
              final name = nameController.text.trim();
              final age = ageController.text.trim();
              final weight = weightController.text.trim();
              final height = heightController.text.trim();

              setState(() {
                if (name.isNotEmpty) userData.fullName = name;
                if (age.isNotEmpty) userData.age = age;
                if (weight.isNotEmpty) userData.weight = weight;
                if (height.isNotEmpty) userData.height = height;
              });

              final prefs = await SharedPreferences.getInstance();
              await prefs.setString('profile_full_name', userData.fullName);
              await prefs.setString('profile_age', userData.age);
              await prefs.setString('profile_weight', userData.weight);
              await prefs.setString('profile_height', userData.height);

              Navigator.pop(context);
            },
            child: const Text("Save"),
          ),
        ],
      ),
    );
  }

  Widget _buildEditField(TextEditingController controller, String label, {bool isNumber = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: TextField(
        controller: controller,
        style: const TextStyle(color: Colors.white),
        keyboardType: isNumber ? TextInputType.number : TextInputType.text,
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: neonCyan),
          enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: neonCyan.withOpacity(0.5))),
          focusedBorder: UnderlineInputBorder(borderSide: BorderSide(color: neonPink)),
        ),
      ),
    );
  }
} 