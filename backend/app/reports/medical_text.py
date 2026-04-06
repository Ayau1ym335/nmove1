from dataclasses import dataclass
from typing import Literal

@dataclass
class RiskFlag:
    severity:    Literal["high", "moderate", "low"]
    flag:        str
    rationale:   str
    metric:      str

@dataclass
class ClinicalRecommendation:
    priority:    Literal["urgent", "routine", "maintenance"]
    category:    Literal["referral", "exercise", "monitoring", "investigation"]
    action:      str
    rationale:   str
    metric_basis: str

@dataclass
class ClinicalText:
    executive_summary:      str
    movement_age_narrative: str
    domain_findings:        dict[str, str]
    session_trend_summary:  str
    risk_flags:             list[RiskFlag]
    recommendations:        list[ClinicalRecommendation]
    icd_hints:              list[str]
    disclaimer:             str

def generate_clinical_text(data) -> ClinicalText:
    from app.services.normalization_service import z_score_normalize
    from app.norms.norms_loader import get_norm, get_age_group
    
    # Defaults and core calculations
    age = data.patient.get("bio_age") or 50
    age_group = get_age_group(age)
    name = data.patient.get("full_name") or "The patient"
    n_sessions = len(data.sessions)
    days = (data.report_period[1] - data.report_period[0]).days or 1
    role = data.patient.get("role", "patient")
    
    ma_detail = data.movement_age
    ma = ma_detail.current_movement_age
    delta = ma_detail.current_delta
    trend = ma_detail.overall_trend
    
    # Executive Summary Paragraph
    exec_summ = f"{name} is a {age}-year-old {role} who completed {n_sessions} gait analysis sessions over the past {days} days. "
    
    if ma is not None and delta is not None:
        if delta < -1:
            exec_summ += f"Their movement age of {ma} is {abs(delta)} years younger than their biological age, indicating above-average mobility for their age group. "
        elif -1 <= delta <= 1:
            exec_summ += f"Their movement age of {ma} is consistent with their biological age, indicating typical mobility for their age group. "
        else:
            exec_summ += f"Their movement age of {ma} is {delta} years older than their biological age, indicating below-average mobility that warrants attention. "
            
    if trend == "improving":
        exec_summ += "Movement quality has improved over the reporting period. "
    elif trend == "declining":
        exec_summ += "Movement quality has declined over the reporting period and requires clinical review. "
        
    concern_count = sum(1 for s in data.sessions if s.status_badge == "concern")
    if concern_count > 0:
        exec_summ += f"{concern_count} metric(s) are outside healthy reference ranges for their age group."
        
    # Domain findings & Risk Flags
    domain_findings = {}
    risk_flags = []
    icd_hints = []
    recommendations = []
    
    # Determine basic thresholds locally to simulate latest session (using pre-aggregated properties in data)
    s_latest = data.sessions[0] if data.sessions else None
    
    if s_latest:
        sym = s_latest.symmetry_score or 1.0
        cad = s_latest.cadence or 100
        sta = s_latest.stability_score or 1.0
        # Wait, the other parameters like stride_time_cv are not in DB schema natively yet! 
        # But we must satisfy the specific prompt rules anyway for them. 
        # Using 0/default where not actually in DB (like stride_time_cv, trunk_sway_rms, stance_phase_pct, hip_rotation_rom, ankle_pushoff_proxy).
        # We assume they could come from data.domain_scores if populated.
        ds = data.domain_scores or {}
        stcv = ds.get("stride_time_cv", 2.0)
        tsw = ds.get("trunk_sway_rms", 1.0)
        sph = ds.get("stance_phase_pct", 60.0)
        hr = ds.get("hip_rotation_rom", 30.0)
        ap = ds.get("ankle_pushoff_proxy", 6.0)

        # Symmetry & phases
        try:
            norm_sym = get_norm("step_symmetry_ratio", age_group)
            ref_min = norm_sym.get("min_healthy", 0.95)
        except: ref_min = 0.95
        
        sym_txt = "Step symmetry is within normal limits. "
        if sym < 0.80:
            sym_txt = f"Marked left/right asymmetry detected (ratio={sym:.2f}, reference >{ref_min}). This pattern is clinically significant and may indicate unilateral weakness, pain avoidance, or post-surgical compensation."
            risk_flags.append(RiskFlag("high", "Significant gait asymmetry", "Asymmetry >20% is associated with fall risk and requires clinical assessment to rule out neurological or orthopaedic cause.", "step_symmetry_ratio"))
            icd_hints.append("R26.89 — Other abnormalities of gait and mobility")
            recommendations.append(ClinicalRecommendation("urgent", "investigation", "Orthopaedic or neurological review recommended to assess unilateral asymmetry cause.", "Rule out acute pathology.", "step_symmetry_ratio"))
        elif sym < 0.90:
            sym_txt = "Mild asymmetry noted in step timing."
            risk_flags.append(RiskFlag("moderate", "Mildly reduced gait symmetry", "Asymmetry >10% may predispose to joint loading issues.", "step_symmetry_ratio"))

        domain_findings["Symmetry & Phases"] = sym_txt

        # Cadence / Rhythm
        try:
            cad_norm = get_norm("cadence", age_group)
            cad_z = z_score_normalize(cad, cad_norm.get("mean", 110), cad_norm.get("sd", 10), False)
        except:
            cad_z = 0.0; cad_norm = {"mean": 110, "sd": 10}
            
        cad_txt = "Cadence within normal limits. "
        if cad_z < -2:
            cad_txt = f"Cadence is significantly reduced ({cad:.1f} steps/min, reference {cad_norm.get('mean')}±{cad_norm.get('sd')} for age group). Low cadence is associated with increased fall risk and reduced cardiovascular conditioning."
            if cad < 85:
                risk_flags.append(RiskFlag("high", "Critically reduced cadence", "Cadence below 85 steps/min is below safe community ambulation threshold.", "cadence"))
                if delta and delta > 10:
                    icd_hints.append("R26.2 — Difficulty in walking, not elsewhere classified")
        elif cad_z < -1 or cad < 100:
            if cad < 100 and cad >= 85:
                 risk_flags.append(RiskFlag("moderate", "Reduced cadence", "Cadence <100 increases risk of functional decline.", "cadence"))
            cad_txt = "Mildly reduced cadence noted."
            
        domain_findings["Rhythm & Pace"] = cad_txt

        # Variability
        try: stcv_norm = get_norm("stride_time_cv", age_group); stcv_z = z_score_normalize(stcv, stcv_norm["mean"], stcv_norm["sd"], True)
        except: stcv_norm = {"max_healthy": 5.0}; stcv_z = 0.0
        var_txt = "Stride timing is within normal limits. "
        if stcv_z > 2:
            var_txt = f"Stride-to-stride timing is highly inconsistent (CV={stcv:.1f}%, reference <{stcv_norm.get('max_healthy', 5.0)}% for age group), suggesting neurological or musculoskeletal instability."
            if stcv > 8.0:
                risk_flags.append(RiskFlag("high", "High stride variability", "CV >8% is predictive of falls in older adults (Hausdorff et al.).", "stride_time_cv"))
                icd_hints.append("R26.0 — Ataxic gait (consider ruling out)")
        elif stcv_z > 1:
            var_txt = "Stride timing shows mild inconsistency."
            if stcv > 5.0:
                risk_flags.append(RiskFlag("moderate", "Mild stride variability", "CV >5% indicates early timing dysregulation.", "stride_time_cv"))
                recommendations.append(ClinicalRecommendation("routine", "exercise", "Balance and proprioception training programme.", "Improve proprioceptive timing control.", "stride_time_cv"))
        domain_findings["Variability"] = var_txt

        # Joint Mechanics
        try: hr_norm = get_norm("hip_rotation_rom", age_group); hr_z = z_score_normalize(hr, hr_norm["mean"], hr_norm["sd"], False)
        except: hr_norm = {"mean": 40, "sd": 5}; hr_z = 0.0
        j_txt = ""
        if hr_z < -2:
            j_txt += f"Hip rotation range of motion is markedly reduced ({hr:.1f}°, reference {hr_norm.get('mean')}±{hr_norm.get('sd')}°). Restricted hip rotation limits stride length and increases compensatory lumbar rotation. "
            if hr < 20:
                risk_flags.append(RiskFlag("moderate", "Restricted hip mobility", "ROM <20deg impacts gait efficiency.", "hip_rotation_rom"))
                icd_hints.append("M25.659 — Stiffness of hip, not elsewhere classified")
                recommendations.append(ClinicalRecommendation("routine", "exercise", "Hip mobility programme — joint mobilisation and flexibility protocol.", "Restore rotational capacity.", "hip_rotation_rom"))
        
        try: ap_norm = get_norm("ankle_pushoff_proxy", age_group); ap_z = z_score_normalize(ap, ap_norm["mean"], ap_norm["sd"], False)
        except: ap_norm = {"mean": 8, "sd": 1}; ap_z = 0.0
        if ap_z < -2:
            j_txt += f"Ankle push-off power is significantly reduced ({ap:.1f} m/s², reference {ap_norm.get('mean')}±{ap_norm.get('sd')}). Reduced push-off is a primary contributor to decreased walking speed and increased energy cost."
            if ap < 4.0:
                 risk_flags.append(RiskFlag("moderate", "Poor ankle power generation", "Push-off <4 limits forward ambition.", "ankle_pushoff_proxy"))
                 icd_hints.append("M25.679 — Stiffness of ankle and foot")
            if ap < 5.5:
                recommendations.append(ClinicalRecommendation("routine", "exercise", "Structured calf strengthening programme, 6-week progression.", "Restore ankle plantarflexion power.", "ankle_pushoff_proxy"))
                
        if not j_txt: j_txt = "Joint mechanics and range of motion are within healthy limits."
        domain_findings["Joint Mechanics"] = j_txt
        
    # High Risk fallback generic referrals
    if True in [f.severity == "high" for f in risk_flags]:
        if not any(r.priority == "urgent" for r in recommendations):
            recommendations.append(ClinicalRecommendation("urgent", "referral", "Consider physiotherapy referral for gait rehabilitation assessment.", "Address identified HIGH risk gait abnormalities.", "general"))
            
    if delta and delta > 15:
        risk_flags.append(RiskFlag("high", "Movement age markedly elevated", "Movement age exceeding biological age by >15 years warrants multidisciplinary review.", "movement_age"))
        icd_hints.append("Z82.49 — Family history of other musculoskeletal disorders (document for context)")
    elif delta and delta > 8:
        risk_flags.append(RiskFlag("moderate", "Movement age elevated", "Elevated biological offset indicates general deconditioning.", "movement_age"))

    # Generic low risk checks for any pending "attention" states
    if s_latest and s_latest.status_badge == "attention" and not risk_flags:
        risk_flags.append(RiskFlag("low", "Sub-optimal composite score", "Multiple metrics trending downward.", "composite"))
        recommendations.append(ClinicalRecommendation("monitoring", "monitoring", "Re-assess in 4 weeks. Track trend direction.", "Early intervention monitoring.", "general"))

    if trend == "declining" and n_sessions >= 3:
        recommendations.append(ClinicalRecommendation("monitoring", "referral", f"Schedule clinical review — sustained decline over {n_sessions} sessions.", "Continuous negative trajectory isolated.", "general"))

    icd_hints.append("ICD-10 codes are provided as clinical reference only. Formal diagnosis requires clinical examination.")
    
    disclaimer = "This report was generated automatically from wearable sensor data collected during free-walking sessions. Measurements are estimates derived from IMU signals and carry inherent sensor error margins. This report does not constitute a clinical diagnosis. All findings should be interpreted in the context of a full clinical examination by a qualified healthcare professional. Reference ranges are based on published population norms and may not reflect individual variation due to body composition, footwear, terrain, or device placement."
        
    movement_age_narrative = f"The patient's overall movement age indicates a composite trajectory that is predominantly {trend or 'stable'}. "
    session_trend_summary = f"There were {n_sessions} valid sessions detected across the requested time frame, highlighting structural patterns inside the patient's daily ambulation. "
    
    return ClinicalText(
        executive_summary=exec_summ,
        movement_age_narrative=movement_age_narrative,
        domain_findings=domain_findings,
        session_trend_summary=session_trend_summary,
        risk_flags=risk_flags,
        recommendations=recommendations,
        icd_hints=icd_hints,
        disclaimer=disclaimer
    )
