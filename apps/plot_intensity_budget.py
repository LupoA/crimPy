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

    dates.append(date_obj)
    fb_intensity.append(breakdown.get("fingerboard", 0))
    cb_intensity.append(breakdown.get("campusboard", 0))
    pu_intensity.append(breakdown.get("pullup", 0))
    proj_intensity.append(breakdown.get("project", 0))

# Sort by date
sorted_data = sorted(zip(dates, fb_intensity, cb_intensity, pu_intensity, proj_intensity),
                     key=lambda x: x[0])
dates, fb_intensity, cb_intensity, pu_intensity, proj_intensity = zip(*sorted_data)

x = np.arange(len(dates))

# Define colors for each exercise type.
colors = {
    "fingerboard": "#e41a1c",  # red
    "campusboard": "#377eb8",  # blue
    "pullup": "#4daf4a",  # green
    "project": "#984ea3"  # purple
}

# Prepare stacked data.
bottom = np.zeros(len(dates))
fig, ax = plt.subplots(figsize=(12, 7))

ax.bar(x, fb_intensity, bottom=bottom, color=colors["fingerboard"], label="Fingerboard")
bottom += np.array(fb_intensity)

ax.bar(x, cb_intensity, bottom=bottom, color=colors["campusboard"], label="Campusboard")
bottom += np.array(cb_intensity)

ax.bar(x, pu_intensity, bottom=bottom, color=colors["pullup"], label="Pullup")
bottom += np.array(pu_intensity)

ax.bar(x, proj_intensity, bottom=bottom, color=colors["project"], label="Project")
bottom += np.array(proj_intensity)

# Format the x-axis.
ax.set_xticks(x)
date_labels = [dt.strftime("%d-%m-%Y") for dt in dates]
ax.set_xticklabels(date_labels, rotation=45)
ax.set_xlabel("Workout Date")
ax.set_ylabel("Intensity")
ax.set_title(" ")
plt.grid(alpha=0.3)
ax.legend()
plt.tight_layout()
plt.show()
