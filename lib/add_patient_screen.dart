import 'package:flutter/material.dart';
import 'services/api_service.dart'; 
import 'main.dart';
import 'user_data.dart';

class AddPatientScreen extends StatelessWidget {
  final nameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  AddPatientScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text("Add New Patient", style: TextStyle(color: Colors.white)),
      ),
      body: Padding(
        padding: const EdgeInsets.all(30),
        child: Column(
          children: [
            GradientTextField(
              hintText: "Full Name",
              gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
              controller: nameController,
            ),
            const SizedBox(height: 10),
            GradientTextField(
              hintText: "Email",
              gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
              controller: emailController,
            ),
            const SizedBox(height: 10),
            GradientTextField(
              hintText: "Login key",
              gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
              controller: passwordController,
            ),
            const SizedBox(height: 30),

ElevatedButton(
  style: ElevatedButton.styleFrom(
    backgroundColor: Colors.cyanAccent,
    minimumSize: const Size(double.infinity, 50),
  ),

onPressed: () async {
  // 1. Валидация
  if (nameController.text.isEmpty || emailController.text.isEmpty) return;

  try {
    // 2. Вызываем сервис, передавая каждое поле отдельно (как в твоем новом ApiService)
    await ApiService.createNewPatient(
      email: emailController.text.trim(),
      fullName: nameController.text.trim(),
      password: passwordController.text.isNotEmpty 
          ? passwordController.text 
          : "password123", // Пароль по умолчанию
    );
    
    // 3. Создаем локальный объект для мгновенного обновления UI
// ... после await ApiService.createNewPatient
UserData newPatient = UserData()
  ..fullName = nameController.text.trim()
  ..email = emailController.text.trim() // Добавь это
  ..city = "Astana"; 

if (context.mounted) {
  Navigator.pop(context, newPatient); 
}
  } catch (e) {
    print("Error creating patient: $e");
    // Опционально: покажи ошибку пользователю
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Ошибка: $e")),
      );
    }
  }
},
  child: const Text(
    "Save Patient",
    style: TextStyle(
      color: Colors.black,
      fontWeight: FontWeight.bold,
    ),
  ),
),

          ],
        ),
      ),
    );
  }
}
