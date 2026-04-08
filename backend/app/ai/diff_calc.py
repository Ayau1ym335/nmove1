from typing import Dict, Any, Union, Optional

def calculate_diff(current: float, target: Optional[float]) -> Union[float, str]:
    if target is None:
        return "N/A"
    
    if abs(target) < 0.001:
        return round(current - target, 2)
    
    try:
        diff = (current - target) / target * 100.0
        return round(diff, 1)
    except ZeroDivisionError:
        return 0.0


def matrix_calc(
    user_data: Dict[str, float],
    clinical_norm: Dict[str, float],
    baseline_data: Optional[Dict[str, float]] = None
) -> Dict[str, Dict[str, Any]]:
    
    matrix = {}
    
    for metric, value in user_data.items():
        c_target = clinical_norm.get(metric)
        b_target = baseline_data.get(metric) if baseline_data else None
        
        clinical_diff = calculate_diff(value, c_target)
        baseline_diff = calculate_diff(value, b_target)
        
        c_status = "Unknown"
        if clinical_diff is not None:
            if abs(clinical_diff) <= 10: c_status = "Normal"
            elif abs(clinical_diff) <= 20: c_status = "Warning"
            else: c_status = "Critical"

        b_status = "No Baseline"
        if baseline_diff is not None:
            if abs(baseline_diff) < 3: b_status = "Stable"
            elif baseline_diff > 0: b_status = "Changed (+)" 
            else: b_status = "Changed (-)"
        
        matrix[metric] = {
            "current_value": value,
            "vs_clinical": {
                "target": c_target,
                "diff_percent": clinical_diff,
                "status": c_status
            },
            "vs_baseline": {
                "target": b_target,
                "diff_percent": baseline_diff,
                "status": b_status
            }
        }
        
    return matrix

def start_doctor_chat(clinical_report_text):
    chat_system_instruction = f"""
SYSTEM ROLE
You are Nmove AI Assistant, a helpful and empathetic medical consultant.
You are talking to the patient RIGHT NOW.

CONTEXT (THE TRUTH)
The patient has just completed a gait analysis. Here is their generated report.
You must answer all questions based ONLY on this report and the medical books you know.

--- BEGIN CLINICAL REPORT ---
{clinical_report_text}

RULES OF ENGAGEMENT (STRICT)
1.  Be Consistency: If the Report says "Knee Angle is bad", do NOT say "It's okay" just to be nice. Stick to the facts in the report.
2.  No New Diagnoses: Do not invent new problems. If the user asks about something not in the report (e.g., "Do I have cancer?"), say: "I can only analyze your gait metrics."
3.  Safety First: If the user asks about running/jumping, check the GVI (Stability) in the report. If GVI < 90, forbid sports.
4.  Tone: Professional, encouraging, but firm on safety.
5.  Anti-Hallucination: If you don't know the answer, say "I recommend showing this report to your doctor."

GOAL
Explain the difficult numbers from the report in simple words.
"""

    chat_session = model.start_chat(
        history=[
            {"role": "user", "parts": [chat_system_instruction]},
            {"role": "model", "parts": ["Understood. I am ready to answer questions about this report."]}
        ]
    )
    while True:
        user_question = input("Вы: ")
        
        if user_question.lower() in ["exit", "выход", "quit"]:
            print("NMove: Выздоравливайте!")
            break
            
        try:
            response = chat_session.send_message(user_question)
            print(f"NMove: {response.text}")
        except Exception as e:
            print(f"Ошибка соединения: {e}")

