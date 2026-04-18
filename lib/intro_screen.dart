import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart'; 
import 'package:url_launcher/url_launcher.dart'; 
import 'main.dart'; 
import 'app_texts.dart';
class IntroScreen extends StatefulWidget {
  const IntroScreen({super.key});

  @override
  State<IntroScreen> createState() => _IntroScreenState();
}

class _IntroScreenState extends State<IntroScreen> {
  bool _isAgreed = false;

  final String _privacyPolicyUrl = "https://nmove.vercel.app/privacy";
  final String _termsOfUseUrl = "https://nmove.vercel.app/terms";
  // Function to open URLs
  Future<void> _launchURL(String urlString) async {
    final Uri url = Uri.parse(urlString);
    try {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (e) {
      debugPrint('Could not launch $urlString: $e');
    }
  }

  @override
Widget build(BuildContext context) {
  final double screenWidth = MediaQuery.of(context).size.width;
  final double screenHeight = MediaQuery.of(context).size.height;

  return Scaffold(
    backgroundColor: Colors.black,
    body: Center(
      child: SingleChildScrollView( 
        padding: EdgeInsets.symmetric(vertical: screenHeight * 0.05, horizontal: 24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ConstrainedBox(
              constraints: BoxConstraints(
                maxHeight: screenHeight * 0.35, 
                maxWidth: screenWidth * 0.8,
              ),
              child: Image.asset(
                "assets/logo.png",
                fit: BoxFit.contain,
              ),
            ),

            SizedBox(height: screenHeight * 0.05),

            Text(
              "NMove",
              style: TextStyle(
                color: Colors.white,
                fontSize: screenWidth * 0.1, 
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
            ),

            const SizedBox(height: 10),

            Text(
              "Move your age",
              style: TextStyle(
                color: Colors.white70,
                fontSize: screenWidth * 0.05,
              ),
            ),

            SizedBox(height: screenHeight * 0.06),
            _buildAgreementBlock(),

            SizedBox(height: screenHeight * 0.05),

            ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400), 
              child: _buildMainButton(
                text: "Get Started",
                onPressed: _isAgreed 
                  ? () => Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (context) => const WelcomeScreen()),
                    )
                  : null,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

Widget _buildMainButton({required String text, VoidCallback? onPressed}) {
  return AnimatedOpacity(
    duration: const Duration(milliseconds: 300),
    opacity: onPressed != null ? 1.0 : 0.4,
    child: Container(
      width: double.infinity, 
      height: 60,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Colors.pink, Colors.purpleAccent],
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: onPressed != null 
          ? [BoxShadow(color: Colors.purpleAccent.withOpacity(0.3), blurRadius: 15, spreadRadius: 2)]
          : [],
      ),
      child: TextButton(
        onPressed: onPressed,
        style: TextButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
        ),
        child: Text(
          text,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    ),
  );
} 
Widget _buildAgreementBlock() {
  return Padding(
    padding: const EdgeInsets.symmetric(horizontal: 8),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        GestureDetector(
          onTap: () => setState(() => _isAgreed = !_isAgreed),
          child: Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: Colors.transparent,
              border: Border.all(
                color: _isAgreed ? Colors.greenAccent : Colors.white24,
                width: 2.0,
              ),
              borderRadius: BorderRadius.circular(6),
            ),
            child: _isAgreed
                ? const Icon(Icons.check, size: 20, color: Colors.greenAccent)
                : null,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: RichText(
            text: TextSpan(
              style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
              children: [
                const TextSpan(text: "By clicking 'Get Started', you agree to our "),
                TextSpan(
                  text: "Privacy Policy",
                  style: const TextStyle(
                    color: Colors.greenAccent, 
                    fontWeight: FontWeight.bold, 
                    decoration: TextDecoration.underline
                  ),
                  recognizer: TapGestureRecognizer()
                    ..onTap = () => _showTextSheet("Privacy Policy", AppTexts.privacyPolicyEn),
                ),
                const TextSpan(text: " and "),
                TextSpan(
                  text: "Terms of Use",
                  style: const TextStyle(
                    color: Colors.greenAccent, 
                    fontWeight: FontWeight.bold, 
                    decoration: TextDecoration.underline
                  ),
                  recognizer: TapGestureRecognizer()
                    ..onTap = () => _showTextSheet("Terms of Use", AppTexts.termsOfUseEn),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}
void _showTextSheet(String title, String content) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.black, 
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      side: BorderSide(color: Colors.white10),
    ),
    builder: (context) => Container(
      padding: const EdgeInsets.all(20),
      height: MediaQuery.of(context).size.height * 0.8,
      child: Column(
        children: [
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(10))),
          const SizedBox(height: 20),
          Text(title, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 15),
          Expanded(
            child: SingleChildScrollView(
              child: Text(
                content,
                style: const TextStyle(color: Colors.white70, fontSize: 15, height: 1.5),
              ),
            ),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: Colors.greenAccent, foregroundColor: Colors.black),
              onPressed: () => Navigator.pop(context),
              child: const Text("Close", style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    ),
  );
}
}