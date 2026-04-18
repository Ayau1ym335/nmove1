import 'package:flutter/material.dart';

enum SubscriptionPlan { free, plus, pro }

class SubscriptionProvider extends ChangeNotifier {
  SubscriptionPlan _currentPlan = SubscriptionPlan.free;

  SubscriptionPlan get currentPlan => _currentPlan;

  void activatePlan(SubscriptionPlan plan) {
    _currentPlan = plan;
    notifyListeners(); 
  }

  bool get isPlusOrPro => _currentPlan != SubscriptionPlan.free;
  bool get isPro => _currentPlan == SubscriptionPlan.pro;
}