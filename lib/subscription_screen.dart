import 'dart:async';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/services.dart';

class SubscriptionScreen extends StatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  State<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends State<SubscriptionScreen> {
  final Color neonCyan = const Color(0xFF00E5FF);
  final Color neonPink = const Color(0xFFFF007F);

  int selectedPlan = 1;

  final List<Map<String, dynamic>> plans = [
    {
      "name": "Free",
      "price": "0",
      "features": [
        "Functional Risk Score (basic)",
        "Basic gait trend tracking",
        "7-day history",
        "Daily status indicator",
        "Mobile app access"
      ],
      "button": "Join Waitlist"
    },
    {
      "name": "Plus",
      "price": "14.99",
      "features": [
        "Everything in Free",
        "Unlimited history",
        "Movement Age Indicator",
        "Aging Speed Tracking",
        "Weekly trend reports",
        "Detailed health reports",
        "Notes & event logging",
        "Change detection"
      ],
      "button": "Upgrade to Plus"
    },
    {
      "name": "Pro",
      "price": "29.99",
      "features": [
        "Everything in Plus",
        "AI Functional Risk Interpretation",
        "Pathology risk deep-dive reports",
        "Longevity coaching tips",
        "Priority support",
        "Early access to new features",
        "Custom health goal tracking"
      ],
      "button": "Upgrade to Pro"
    },
  ];

  Future<void> _payWithKaspi() async {
    if (selectedPlan == 0) return;

    var current = plans[selectedPlan];
    int amountInTenge = (double.parse(current['price']) * 450).toInt();

    String myIban = "KZ123456789012345678";

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.grey[900],
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Container(
        padding: const EdgeInsets.all(25),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("Payment Details",
                style: TextStyle(
                    color: neonCyan,
                    fontSize: 20,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 15),
            Text("Amount to pay: $amountInTenge KZT",
                style:
                    const TextStyle(color: Colors.white, fontSize: 18)),
            const SizedBox(height: 20),
            const Text("Transfer to IBAN:",
                style: TextStyle(color: Colors.white70)),
            Container(
              margin: const EdgeInsets.symmetric(vertical: 10),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white24),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(myIban,
                        style: const TextStyle(
                            color: Colors.white,
                            fontFamily: 'monospace')),
                  ),
                  IconButton(
                    icon: Icon(Icons.copy, color: neonCyan),
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: myIban));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content:
                                Text("IBAN copied to clipboard!")),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                  backgroundColor: neonCyan,
                  foregroundColor: Colors.black),
              onPressed: () {
                Navigator.pop(context);
                _showConfirmationDialog();
              },
              child: const Text("I have sent the payment"),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _saveSubscriptionStatus(int planIndex) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('user_subscription_level', planIndex);

    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      backgroundColor: neonPink,
      content: Text(
          "Premium features for ${plans[planIndex]['name']} activated!"),
    ));
  }

  void _handleActionButton() {
    if (selectedPlan == 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Free plan activated")),
      );
      return;
    }

    _payWithKaspi();
  }

  void _showConfirmationDialog() {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: Colors.black,
          title: Text(
            "Payment confirmation",
            style:
                TextStyle(color: neonCyan, fontWeight: FontWeight.bold),
          ),
          content: const Text(
            "If the payment is confirmed, your subscription will be activated.",
            style: TextStyle(color: Colors.white70),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text("Cancel",
                  style: TextStyle(color: Colors.white)),
            ),
            TextButton(
              onPressed: () async {
                Navigator.pop(context);
                await _saveSubscriptionStatus(selectedPlan);
              },
              child: Text("Confirm",
                  style: TextStyle(color: neonCyan)),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    var current = plans[selectedPlan];

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        leading: IconButton(
          icon:
              const Icon(Icons.arrow_back_ios, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Column(
          children: [
            const Text("Potential",
                textAlign: TextAlign.center,
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 28,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 25),

            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.grey[900]!.withOpacity(0.5),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.white10),
              ),
              child: Row(
                children: [
                  _buildTab("Free", 0),
                  _buildTab("Plus", 1),
                  _buildTab("Pro", 2),
                ],
              ),
            ),

            const SizedBox(height: 15),

            Align(
              alignment: Alignment.centerRight,
              child: Opacity(
                opacity: selectedPlan > 0 ? 1.0 : 0.0,
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Text(
                    "MOST POPULAR",
                    style: TextStyle(
                        color: neonCyan,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5),
                  ),
                ),
              ),
            ),

            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 40),
              decoration: BoxDecoration(
                color: Colors.grey[900]!.withOpacity(0.2),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(
                    color: neonCyan.withOpacity(0.8), width: 1),
              ),
              child: Center(
                child: RichText(
                  text: TextSpan(
                    children: [
                      TextSpan(
                          text: "\$${current['price']}",
                          style: const TextStyle(
                              fontSize: 55,
                              fontWeight: FontWeight.bold,
                              color: Colors.white)),
                      const TextSpan(
                          text: " /month",
                          style: TextStyle(
                              fontSize: 18,
                              color: Colors.white70)),
                    ],
                  ),
                ),
              ),
            ),

            const SizedBox(height: 30),

            Column(
              children:
                  (current['features'] as List<String>).map((feature) {
                return Padding(
                  padding:
                      const EdgeInsets.symmetric(vertical: 8),
                  child: Row(
                    children: [
                      Icon(Icons.check,
                          color: neonCyan, size: 20),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(feature,
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16)),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),

            const SizedBox(height: 40),

            GestureDetector(
              onTap: _handleActionButton,
              child: Container(
                width: double.infinity,
                height: 55,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  gradient: LinearGradient(
                      colors: [const Color(0xFF9C27B0), neonPink]),
                ),
                child: Center(
                  child: Text(current['button'],
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold)),
                ),
              ),
            ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildTab(String title, int index) {
    bool isSel = selectedPlan == index;

    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => selectedPlan = index),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSel ? neonCyan : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(title,
              textAlign: TextAlign.center,
              style: TextStyle(
                  color: isSel ? Colors.black : Colors.white,
                  fontWeight: FontWeight.bold)),
        ),
      ),
    );
  }
}