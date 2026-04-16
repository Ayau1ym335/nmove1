import 'package:flutter/material.dart';
import 'add_patient_screen.dart';
import 'patient_profile_screen.dart';
import 'user_data.dart'; 
import 'services/api_service.dart';

class DoctorPatientListScreen extends StatefulWidget {
  const DoctorPatientListScreen({super.key});

  @override
  State<DoctorPatientListScreen> createState() => _DoctorPatientListScreenState();
}

class _DoctorPatientListScreenState extends State<DoctorPatientListScreen> {
  List<UserData> patients = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    fetchPatientsData();
  }

  void addPatient(UserData newPatient) {
    setState(() {
      patients.add(newPatient);
    });
  }

Future<void> fetchPatientsData() async {
  if (!mounted) return;
  setState(() => isLoading = true);
  
  try {
    // Получаем ответ от API
    final dynamic response = await ApiService.getDoctorPatients();
    
    List<dynamic> rawData = [];

    if (response is List) {
      // Если сервер сразу вернул список
      rawData = response;
    } else if (response is Map) {
      // Если сервер вернул объект, проверяем наличие ключа 'patients'
      // Используем 'as List<dynamic>', чтобы компилятор не ругался
      if (response.containsKey('patients') && response['patients'] != null) {
        rawData = response['patients'] as List<dynamic>;
      }
    }

    if (mounted) {
      setState(() {
        patients = rawData.map((json) => UserData.fromJson(json)).toList();
        isLoading = false;
      });
    }
  } catch (e) {
    print("Error fetching: $e");
    if (mounted) setState(() => isLoading = false);
  }
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0E11),
      appBar: AppBar(
        title: const Text("My Patients", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.black,
        elevation: 0,
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Colors.cyanAccent,
        child: const Icon(Icons.add, color: Colors.black),
        onPressed: () async {
          final result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => AddPatientScreen()),
          );

          if (result != null && result is UserData) {
            addPatient(result); // Теперь метод существует
          }
        },
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator(color: Colors.cyanAccent))
          : RefreshIndicator(
              onRefresh: fetchPatientsData,
              color: Colors.cyanAccent,
              child: patients.isEmpty
                  ? const Center(
                      child: Text("No patients found",
                          style: TextStyle(color: Colors.white70, fontSize: 16)))
                  : ListView.builder(
                      itemCount: patients.length,
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      itemBuilder: (context, index) {
                        final patient = patients[index];
                        return _buildPatientCard(patient);
                      },
                    ),
            ),
    );
  }

  Widget _buildPatientCard(UserData patient) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 15, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1D21),
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: Colors.white10),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(15),
        leading: const CircleAvatar(
          backgroundColor: Colors.cyanAccent,
          child: Icon(Icons.person, color: Colors.black),
        ),
        title: Text(
          patient.fullName.isNotEmpty ? patient.fullName : "Unknown",
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
        ),
        subtitle: Text(
          patient.city.isNotEmpty ? patient.city : "No city",
          style: const TextStyle(color: Colors.grey),
        ),
        trailing: const Icon(Icons.arrow_forward_ios, color: Colors.cyanAccent, size: 16),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PatientProfileScreen(patientData: patient),
            ),
          );
        },
      ),
    );
  }
}