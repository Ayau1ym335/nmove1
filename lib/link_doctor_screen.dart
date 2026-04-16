import 'package:flutter/material.dart';
import 'user_data.dart';
import 'main.dart'; 
import 'services/api_service.dart';

class LinkDoctorScreen extends StatefulWidget {
  const LinkDoctorScreen({super.key});

  @override
  State<LinkDoctorScreen> createState() => _LinkDoctorScreenState();
}

class _LinkDoctorScreenState extends State<LinkDoctorScreen> {
  final fullNameController = TextEditingController();
  final emailController = TextEditingController();
  bool _submitting = false;

  @override
  void dispose() {
    fullNameController.dispose();
    emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final userData = UserDataProvider.of(context)!.userData;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        title: const Text("Link Your Doctor", style: TextStyle(color: Colors.white)),
        centerTitle: true,
      ),
      body: Center(
        child: SizedBox(
          width: 310,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const SizedBox(height: 30),
              
              GradientTextField(
                hintText: "Doctor's Full Name",
                gradient: const LinearGradient(colors: [Colors.cyan, Colors.purple]),
                controller: fullNameController,
              ),
              const SizedBox(height: 15),

              GradientTextField(
                hintText: "Doctor's Email",
                gradient: const LinearGradient(colors: [Colors.pink, Colors.purple]),
                controller: emailController,
              ),
              const SizedBox(height: 25),

              Container(
                width: double.infinity,
                height: 55,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(15),
                  gradient: const LinearGradient(colors: [Colors.pink, Colors.purpleAccent]),
                ),
                child: TextButton(
                  onPressed: _submitting
                      ? null
                      : () async {
                          userData.doctorName = fullNameController.text;
                          userData.doctorEmail = emailController.text;

                          final email = userData.email.trim();
                          final password = userData.password.trim();
                          if (email.isEmpty || password.isEmpty) {
                            if (!mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  'Нет email или пароля. Вернитесь и заново пройдите регистрацию.',
                                ),
                              ),
                            );
                            return;
                          }

                          setState(() => _submitting = true);
                          try {
                            try {
                              await ApiService.register(
                                email: email,
                                password: password,
                                fullName: userData.fullName.trim().isEmpty
                                    ? 'User'
                                    : userData.fullName.trim(),
                                role: 'patient',
                                city: userData.city,
                                gender: userData.gender.toLowerCase() == 'male'
                                    ? 'male'
                                    : 'female',
                                age: userData.age,
                                weight: userData.weight,
                                height: userData.height,
                                dominantLeg: userData.dominantLeg.toLowerCase(),
                              );
                            } catch (e) {
                              if (!mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                    'Регистрация на сервере не удалась: $e\n'
                                    'Проверьте адрес API в ApiService и что бэкенд запущен.',
                                  ),
                                  duration: const Duration(seconds: 6),
                                ),
                              );
                              return;
                            }

                            final role = await ApiService.login(email, password);
                            if (!mounted) return;
                            if (role == 'error') {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'Вход не удался. Проверьте пароль и что сервер доступен.',
                                  ),
                                  duration: Duration(seconds: 5),
                                ),
                              );
                              return;
                            }

                            Navigator.pushAndRemoveUntil(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const MainAppPlaceholder(),
                              ),
                              (route) => false,
                            );
                          } finally {
                            if (mounted) setState(() => _submitting = false);
                          }
                        },
                  child: _submitting
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text(
                          "Finish",
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
