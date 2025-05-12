from crimpy.intensity import WorkoutIntensityCalculator

# --- Fingerboard Benchmark -----------------------------------------
base_fb_set = {
    "reps": 6,
    "timeon": "7s",
    "timeoff": "3s",
    "rest": "120s"
}

# Edges to test [mm]
edges = [45, 35, 25, 20, 15, 10, 8, 6]

print("Example : Fingerboard 7on 3off, six repeaters : Intensity for Edge Sizes")
print("--------------------------------------------------------")
for edge_mm in edges:
    # Construct one-set fingerboard exercise with current edge
    dummy_workout = {
        "exercises": [
            {
                "type": "fingerboard",
                "executed": True,
                "order": 1,
                "sets": [
                    {**base_fb_set, "edge": f"{edge_mm}mm"}
                ]
            }
        ]
    }

    # Calculate intensity
    calc = WorkoutIntensityCalculator(dummy_workout)
    intensity = calc.calculate_intensity_breakdown()["fingerboard"]
    print(f"Edge: {edge_mm:>4} mm -> Intensity: {intensity:.4f}")

# --- Pull-up Benchmark ---------------------------------------------
base_pu_set = {
    "edge":       "bar",
    "repetitions": 8,
    "timeoff":    "200s"
}

weights = [0, 8, 10, 14, 18, 20, 24, 32]

print("Example : Pullups intensity for 8 reps varying weight [kg]")
print("------------------------------------------------------")
for w in weights:
    dummy = {
        "exercises": [{
            "type":     "pullup",
            "executed": True,
            "order":    1,
            "sets": [{**base_pu_set, "weight_kg": w}]
        }]
    }
    calc      = WorkoutIntensityCalculator(dummy)
    pu_int    = calc.calculate_intensity_breakdown()["pullup"]
    print(f"Weight: {w:>2} → Intensity: {pu_int:.4f}")

# --- Campus Board Benchmark ---------------------------------------------
timeoff = "120s"

# Edges and step‐patterns to test
tests = [
    (35, "1-2-3"),
    (35, "1-3"),
    (35, "1-3-5"),
    (28, "1-2-3"),
    (28, "1-3"),
    (28, "1-3-5"),
    (21, "1-2-3"),
    (21, "1-3"),
    (21, "1-3-5"),
]

print("Example: Campusboard intensity")
print("--------------------------------")
for edge_mm, steps in tests:
    dummy = {
        "exercises": [{
            "type":     "campus board",
            "executed": True,
            "order":    1,
            "sets": [{
                "edge":   f"{edge_mm}mm",
                "steps":  steps,
                "timeoff": timeoff,
                "sides":  "R"   # sides doesn’t affect intensity
            }]
        }]
    }
    calc = WorkoutIntensityCalculator(dummy)
    cb_i = calc.calculate_intensity_breakdown()["campusboard"]
    print(f"Edge {edge_mm:>2}mm, steps {steps:7} → Intensity: {cb_i:.4f}")