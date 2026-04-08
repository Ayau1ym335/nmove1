import numpy as np

def compute_gait_metrics(readings: list) -> dict:
    """Compute true biomechanical gait metrics from a chronological list of GaitReading ORM objects."""
    if len(readings) < 10:
        raise ValueError("Insufficient readings for metric calculation")

    duration_s = (readings[-1].time - readings[0].time).total_seconds()
    
    ax_values = np.array([r.ax for r in readings])
    ay_values = np.array([r.ay for r in readings])
    az_values = np.array([r.az for r in readings])
    gz_values = np.array([r.gz for r in readings])
    
    # -------------------------------------------------------------
    # 1. Cadence (steps/min)
    # -------------------------------------------------------------
    # Peak detection on vertical acceleration (az)
    diff = np.diff(az_values)
    sign_changes = np.where(np.diff(np.sign(diff)) < 0)[0]
    
    threshold_az = np.mean(az_values) + 0.5 * np.std(az_values)
    peaks_above_threshold = sign_changes[
        az_values[sign_changes + 1] > threshold_az
    ]
    step_count = len(peaks_above_threshold)
    cadence = (step_count / max(duration_s, 1)) * 60

    # -------------------------------------------------------------
    # 2. Stride Length (m)
    # -------------------------------------------------------------
    dt = duration_s / len(readings) if len(readings) > 0 else 0
    ax_detrended = ax_values - np.linspace(ax_values[0], ax_values[-1], len(ax_values))
    velocity = np.cumsum(ax_detrended) * dt
    displacement = np.cumsum(velocity) * dt
    total_distance = abs(displacement[-1] - displacement[0])
    
    stride_length = total_distance / max(step_count / 2, 1)
    stride_length = float(np.clip(stride_length, 0.3, 2.5))

    # -------------------------------------------------------------
    # 3. Step Symmetry Ratio
    # -------------------------------------------------------------
    peak_values = az_values[peaks_above_threshold + 1]
    if len(peak_values) >= 4:
        even_peaks = peak_values[::2]
        odd_peaks = peak_values[1::2]
        mean_even = float(np.mean(even_peaks))
        mean_odd = float(np.mean(odd_peaks))
        
        max_val = max(mean_even, mean_odd)
        ratio = min(mean_even, mean_odd) / max_val if max_val != 0 else 1.0
        step_symmetry_ratio = float(np.clip(ratio, 0.0, 1.0))
    else:
        step_symmetry_ratio = 0.90

    # -------------------------------------------------------------
    # 4. Stance Phase % and Double Support %
    # -------------------------------------------------------------
    gravity = 9.81
    threshold_stance = 0.5 * np.std(az_values)
    near_gravity = np.abs(az_values - gravity) < threshold_stance
    
    stance_phase_pct = float(np.mean(near_gravity) * 100) if len(near_gravity) > 0 else 60.0
    stance_phase_pct = float(np.clip(stance_phase_pct, 45.0, 80.0))
    double_support_pct = float(np.clip(stance_phase_pct * 0.18, 5.0, 35.0))

    # -------------------------------------------------------------
    # 5. Stride Time Variability (CV %)
    # -------------------------------------------------------------
    if len(peaks_above_threshold) >= 3:
        peak_times = np.array([readings[i].time.timestamp() for i in peaks_above_threshold])
        inter_peak = np.diff(peak_times)
        if np.mean(inter_peak) > 0:
            stride_time_cv = float((np.std(inter_peak) / np.mean(inter_peak)) * 100)
        else:
            stride_time_cv = 5.0
        stride_time_cv = float(np.clip(stride_time_cv, 0.5, 20.0))
    else:
        stride_time_cv = 5.0

    # -------------------------------------------------------------
    # 6. Trunk Sway RMS (m/s²)
    # -------------------------------------------------------------
    trunk_sway_rms = float(np.sqrt(np.mean(ay_values ** 2))) if len(ay_values) > 0 else 0.0
    trunk_sway_rms = float(np.clip(trunk_sway_rms, 0.0, 2.0))

    # -------------------------------------------------------------
    # 7. Vertical Oscillation Peak-to-Peak (m/s²)
    # -------------------------------------------------------------
    vertical_oscillation = float(np.max(az_values) - np.min(az_values)) if len(az_values) > 0 else 0.0
    vertical_oscillation = float(np.clip(vertical_oscillation, 2.0, 30.0))

    # -------------------------------------------------------------
    # 8. Hip Rotation ROM (deg)
    # -------------------------------------------------------------
    hip_rotation_rom = float(np.max(gz_values) - np.min(gz_values)) if len(gz_values) > 0 else 0.0
    hip_rotation_rom = float(np.clip(hip_rotation_rom, 0.0, 120.0))

    # -------------------------------------------------------------
    # 9. Ankle Push-off Proxy (m/s²)
    # -------------------------------------------------------------
    ax_negative = ax_values[ax_values < 0]
    if len(ax_negative) > 0:
        ankle_pushoff_proxy = float(abs(np.min(ax_values)))
    else:
        ankle_pushoff_proxy = 0.0
    ankle_pushoff_proxy = float(np.clip(ankle_pushoff_proxy, 0.0, 20.0))

    # Average walking speed (m/s) — total distance / total duration
    avg_speed = float(np.clip(total_distance / max(duration_s, 1), 0.0, 4.0))

    return {
        "cadence": round(cadence, 2),
        "stride_length": round(stride_length, 3),
        "avg_speed": round(avg_speed, 3),
        "step_symmetry_ratio": round(step_symmetry_ratio, 4),
        "stance_phase_pct": round(stance_phase_pct, 2),
        "double_support_pct": round(double_support_pct, 2),
        "stride_time_cv": round(stride_time_cv, 3),
        "trunk_sway_rms": round(trunk_sway_rms, 4),
        "vertical_oscillation": round(vertical_oscillation, 3),
        "hip_rotation_rom": round(hip_rotation_rom, 2),
        "ankle_pushoff_proxy": round(ankle_pushoff_proxy, 3),
        "duration_seconds": round(duration_s, 2),
        "reading_count": len(readings),
        "step_count": step_count,
    }
