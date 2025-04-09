import os
import json
import glob
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from crimpy.intensity import WorkoutIntensityCalculator

# Define the directory containing JSON workout files.
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

dates = []
fb_intensity = []  # Fingerboard
cb_intensity = []  # Campusboard
pu_intensity = []  # Pullup
proj_intensity = []  # Project
proj_grades = []  # to store label per workout


json_files = glob.glob(os.path.join(data_dir, "*.json"))
for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    workout_date = data.get("date")
    try:
        date_obj = datetime.strptime(workout_date, "%d-%m-%Y")
    except Exception as e:
        continue

    calc = WorkoutIntensityCalculator(data, source_file=os.path.basename(file_path), date=workout_date)
    breakdown = calc.calculate_intensity_breakdown()

    grade_label = None
    for exercise in data.get("exercises", []):
        if exercise.get("type", "").lower() == "project":
            for s in exercise.get("sets", []):
                if s.get("success") and "grade" in s:
                    grade_label = s["grade"]
                    break  # take the first successful grade only
            break
    proj_grades.append(grade_label)

    dates.append(date_obj)
    fb_intensity.append(breakdown.get("fingerboard", 0))
    cb_intensity.append(breakdown.get("campusboard", 0))
    pu_intensity.append(breakdown.get("pullup", 0))
    proj_intensity.append(breakdown.get("project", 0))

# Sort workouts by date.
sorted_data = sorted(zip(dates, fb_intensity, cb_intensity, pu_intensity, proj_intensity, proj_grades),
                     key=lambda x: x[0])
dates, fb_intensity, cb_intensity, pu_intensity, proj_intensity, proj_grades = zip(*sorted_data)
# Compute days elapsed since the first workout.
start_date = dates[0]
days_elapsed = [(dt - start_date).days for dt in dates]
x = np.array(days_elapsed)

# Compute total intensity for each workout.
total_intensity = np.array(fb_intensity) + np.array(cb_intensity) + np.array(pu_intensity) + np.array(proj_intensity)

# Define colors for each exercise type.
colors = {
    "fingerboard": "#e41a1c",  # red
    "campusboard": "#377eb8",  # blue
    "pullup": "#4daf4a",       # green
    "project": "#984ea3"       # purple
}

# Prepare stacked data.
bottom = np.zeros(len(x))
fig, ax = plt.subplots(figsize=(12, 7))

ax.bar(x, fb_intensity, bottom=bottom, color=colors["fingerboard"], label="Fingerboard")
bottom += np.array(fb_intensity)

ax.bar(x, cb_intensity, bottom=bottom, color=colors["campusboard"], label="Campusboard")
bottom += np.array(cb_intensity)

ax.bar(x, pu_intensity, bottom=bottom, color=colors["pullup"], label="Pullup")
bottom += np.array(pu_intensity)

ax.bar(x, proj_intensity, bottom=bottom, color=colors["project"], label="Project")
bottom += np.array(proj_intensity)

for i, (xi, proj, label) in enumerate(zip(x, proj_intensity, proj_grades)):
    if label and proj > 0:
        ax.text(
            xi, bottom[i] - proj / 2,  # place roughly centered vertically in the bar
            label,
            ha="center", va="center",
            fontsize=12, color="black", fontweight="bold",
            rotation=0
        )

# Plot the total intensity as a continuous line over the stacked bars.
ax.plot(x, total_intensity, color="black", marker="o", linestyle="-", linewidth=2, label="Total Intensity")

# Format the x-axis.
ax.set_xticks(x)
ax.set_xlabel("Days")
ax.set_ylabel("Intensity")
ax.set_title(" ")
ax.legend(title="Exercise Type", loc="upper left", bbox_to_anchor=(1, 1))
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
