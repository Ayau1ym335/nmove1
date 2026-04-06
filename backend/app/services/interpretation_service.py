def compute_interpretation(
    metrics: dict,
    movement_age: dict,
) -> dict:
    RULES = [
        {
            "metric": "cadence",
            "label": "Walking pace",
            "concern_threshold":    lambda v: v < 85,
            "attention_threshold":  lambda v: v < 100,
            "exercises": {
                "concern": [
                    {
                        "title": "Metronome walking",
                        "description": "Set a metronome to 100 bpm. Walk in sync for 5 minutes, focusing on matching each beat with a step. Increase by 5 bpm weekly.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Interval pace walk",
                        "description": "Alternate 1 minute slow walk with 1 minute brisk walk. Complete 6 cycles. Gradually increase brisk pace each session.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Step cadence drill",
                        "description": "Count steps aloud for 30 seconds, multiply by 2 to get cadence. Target adding 5 steps/min per week until reaching 100+.",
                        "difficulty": "easy",
                    },
                ],
                "attention": [
                    {
                        "title": "Brisk walk intervals",
                        "description": "Walk at a comfortable pace for 2 minutes, then increase speed for 1 minute. Repeat 5 times. Target 105-110 steps/min.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Music-paced walking",
                        "description": "Walk to music at 110-115 bpm. Many streaming apps have walking playlists by BPM. Do 10 minutes daily.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "step_symmetry_ratio",
            "label": "Left/right balance",
            "concern_threshold":    lambda v: v < 0.80,
            "attention_threshold":  lambda v: v < 0.90,
            "exercises": {
                "concern": [
                    {
                        "title": "Single-leg stance progression",
                        "description": "Stand on weaker leg for 20 seconds. Use wall for safety if needed. Progress to 40 seconds eyes open, then 20 seconds eyes closed.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Lateral step-overs",
                        "description": "Place 6 small objects in a line. Step laterally over each object leading with each foot. Focus on equal force through both legs.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Mirror feedback walking",
                        "description": "Walk parallel to a full-length mirror for 5 minutes. Observe and correct any visible lean or uneven arm swing immediately.",
                        "difficulty": "easy",
                    },
                ],
                "attention": [
                    {
                        "title": "Tandem walking",
                        "description": "Walk heel-to-toe in a straight line for 10 steps. Turn and repeat in opposite direction. Complete 4 lengths. Improves symmetry control.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Single-leg balance",
                        "description": "Stand on one leg 30 seconds each side, 3 sets. Progress by closing eyes or standing on a folded towel.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "stride_time_cv",
            "label": "Stride consistency",
            "concern_threshold":    lambda v: v > 8.0,
            "attention_threshold":  lambda v: v > 5.0,
            "exercises": {
                "concern": [
                    {
                        "title": "Rhythmic treadmill walking",
                        "description": "Walk on treadmill at fixed speed for 10 minutes. The constant pace forces rhythm regulation. Start at comfortable speed, hold it steady for the full duration.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Counting stride drill",
                        "description": "Count every right foot strike. Walk 20 strides, rest 30 seconds. Repeat 5 times focusing on making each stride feel identical.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Obstacle course walking",
                        "description": "Place 8 markers 60cm apart on the floor. Walk stepping over each at a controlled pace. Builds deliberate stride length consistency.",
                        "difficulty": "medium",
                    },
                ],
                "attention": [
                    {
                        "title": "Paced corridor walk",
                        "description": "Walk a fixed corridor at the same pace each lap. Time each lap — aim for under 2 seconds variation across 5 laps.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Barefoot balance walk",
                        "description": "Walk barefoot on a smooth surface for 5 minutes. Heightened sensory feedback naturally improves rhythmic consistency.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "trunk_sway_rms",
            "label": "Trunk stability",
            "concern_threshold":    lambda v: v > 0.50,
            "attention_threshold":  lambda v: v > 0.35,
            "exercises": {
                "concern": [
                    {
                        "title": "Dead bug core activation",
                        "description": "Lie on back, arms up, knees at 90°. Lower opposite arm and leg slowly to floor, return. 10 reps each side. Builds deep core stability essential for trunk control.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Pallof press hold",
                        "description": "Use resistance band anchored to side. Hold band at chest, press out and hold 3 seconds, return. 10 reps each side. Anti-rotation training for lateral sway reduction.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Book-on-head walking",
                        "description": "Place a light flat object on head. Walk 20 metres without it falling. Immediate biofeedback for trunk sway correction.",
                        "difficulty": "easy",
                    },
                ],
                "attention": [
                    {
                        "title": "Plank progression",
                        "description": "Hold plank position 20 seconds, rest 10 seconds, repeat 4 times. Progress by 5 seconds per session. Targets transverse abdominis — primary trunk stabiliser.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Side-step with arm control",
                        "description": "Step side-to-side 1 metre each way, keeping arms crossed on chest. 3 sets of 20 steps. Removes arm compensation, isolates trunk.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "hip_rotation_rom",
            "label": "Hip mobility",
            "concern_threshold":    lambda v: v < 20.0,
            "attention_threshold":  lambda v: v < 28.0,
            "exercises": {
                "concern": [
                    {
                        "title": "90/90 hip stretch",
                        "description": "Sit with front leg at 90° and rear leg at 90° to the side. Lean gently forward over front shin 30 seconds each side. 3 sets. Best stretch for hip internal/external ROM.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Hip CARs — controlled articular rotations",
                        "description": "Stand on one leg. Draw the largest possible circle with your raised knee — forward, up, out, back, down. 5 slow circles each direction each leg. Lubricates and opens hip joint.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Pigeon pose hold",
                        "description": "From plank, bring one knee forward behind same-side wrist. Lower hips toward floor, hold 60 seconds each side. 2 sets. Deep hip external rotator release.",
                        "difficulty": "medium",
                    },
                ],
                "attention": [
                    {
                        "title": "Standing hip flexor stretch",
                        "description": "Lunge forward, drop rear knee to floor. Push hips forward gently 30 seconds each side. 2 sets. Releases hip flexor tightness that limits rotation during walking.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Hip circles standing",
                        "description": "Hands on hips, feet shoulder width. Draw large slow circles with pelvis 10 each direction. 2 sets. Warms and mobilises hip joint through full available range.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "ankle_pushoff_proxy",
            "label": "Ankle push-off power",
            "concern_threshold":    lambda v: v < 4.0,
            "attention_threshold":  lambda v: v < 5.5,
            "exercises": {
                "concern": [
                    {
                        "title": "Calf raise progression",
                        "description": "Stand on step edge, heels hanging. Lower heels below step level, rise to maximum height. 3 sets of 15 reps each leg. Builds soleus and gastrocnemius strength directly improving push-off power.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Ankle elastic band resistance",
                        "description": "Loop band around foot. Point and flex foot against resistance, 3 sets of 20 reps each foot. Targets tibialis anterior and peroneals for balanced ankle mechanics.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Skipping rope — slow singles",
                        "description": "Skip at slow controlled pace 60 seconds, rest 30 seconds, repeat 5 times. Low-impact plyometric that trains explosive ankle plantarflexion — the push-off motion.",
                        "difficulty": "hard",
                    },
                ],
                "attention": [
                    {
                        "title": "Double calf raises",
                        "description": "Stand flat, rise onto toes slowly (2 sec up, 2 sec down). 3 sets of 12. Focus on full plantar flexion at top. Restores push-off timing and force.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Toe-heel walk",
                        "description": "Walk 10m on toes, walk 10m on heels, repeat 4 lengths. Activates full ankle range and teaches deliberate push-off engagement.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "vertical_oscillation",
            "label": "Vertical bounce efficiency",
            "concern_threshold":    lambda v: v < 8.0 or v > 22.0,
            "attention_threshold":  lambda v: v < 10.0 or v > 18.0,
            "exercises": {
                "concern": [
                    {
                        "title": "Soft-knee walking drill",
                        "description": "Walk with slightly bent knees throughout the stride cycle. Focus on gliding forward rather than bouncing up. 5 minutes. Reduces excessive vertical oscillation.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Heel-strike reduction walk",
                        "description": "Walk landing on mid-foot rather than heel. Shorter steps, higher cadence. 5 minutes focus walking. Reduces impact forces and normalises vertical movement.",
                        "difficulty": "medium",
                    },
                    {
                        "title": "Glute bridge activation",
                        "description": "Lie on back, feet flat, drive hips to ceiling squeezing glutes. Hold 2 seconds at top. 3 sets of 15. Improves hip extension reducing compensatory bounce.",
                        "difficulty": "easy",
                    },
                ],
                "attention": [
                    {
                        "title": "Forward lean walk",
                        "description": "Walk with 5-degree forward lean from ankles — not waist. 5 minutes. Shifts propulsion forward, reduces vertical energy waste.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Step length awareness",
                        "description": "Consciously take slightly shorter steps at higher frequency for 5 minutes. Shorter steps reduce vertical oscillation while maintaining speed.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
        {
            "metric": "movement_age_delta",
            "label": "Overall movement age vs biological age",
            "concern_threshold":    lambda v: v > 10,
            "attention_threshold":  lambda v: v > 5,
            "exercises": {
                "concern": [
                    {
                        "title": "Daily 20-minute structured walk",
                        "description": "Walk at brisk pace (you can talk but feel slightly breathless) for 20 minutes every day. Consistent aerobic stimulus is the single highest-impact intervention for overall movement age improvement.",
                        "difficulty": "easy",
                    },
                    {
                        "title": "Full-body mobility flow",
                        "description": "10-minute routine: ankle circles (1 min), hip circles (1 min), spinal rotations (1 min), shoulder rolls (1 min), leg swings (1 min each leg), then repeat. Daily practice.",
                        "difficulty": "easy",
                    },
                ],
                "attention": [
                    {
                        "title": "Active recovery walk",
                        "description": "15-minute easy walk focusing on upright posture, relaxed arms, and even breathing. Quality over speed. Do this on rest days between more intense sessions.",
                        "difficulty": "easy",
                    },
                ],
            },
        },
    ]

    issues = []

    for rule in RULES:
        metric_name = rule["metric"]

        if metric_name == "movement_age_delta":
            value = movement_age.get("delta")
            if value is None:
                continue
        else:
            value = metrics.get(metric_name)
            if value is None:
                continue

        if rule["concern_threshold"](value):
            severity = "concern"
        elif rule["attention_threshold"](value):
            severity = "attention"
        else:
            continue

        issues.append({
            "metric": metric_name,
            "label": rule["label"],
            "value": value,
            "severity": severity,
            "exercises": rule["exercises"][severity],
        })

    if any(i["severity"] == "concern" for i in issues):
        status = "concern"
    elif any(i["severity"] == "attention" for i in issues):
        status = "attention"
    else:
        status = "normal"

    all_exercises = []
    seen_titles = set()

    for issue in sorted(issues, key=lambda x: x["severity"] == "concern", reverse=True):
        for ex in issue["exercises"]:
            if ex["title"] not in seen_titles and len(all_exercises) < 5:
                all_exercises.append({**ex, "for_metric": issue["label"]})
                seen_titles.add(ex["title"])

    if status == "normal" and not all_exercises:
        all_exercises.append({
            "title": "Maintenance walk",
            "description": "Your movement patterns are healthy. Maintain them with a 20-minute brisk walk at comfortable pace 3-5 times per week.",
            "difficulty": "easy",
            "for_metric": "General maintenance",
        })

    return {
        "status": status,
        "issues": issues,
        "exercises": all_exercises,
        "issue_count": len(issues),
        "concern_count": sum(1 for i in issues if i["severity"] == "concern"),
        "attention_count": sum(1 for i in issues if i["severity"] == "attention"),
    }
