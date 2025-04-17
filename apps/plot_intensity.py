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

# Collect dates of outdoor climbing sessions (files with "climbs")
outdoor_sessions = []  # list of (date_obj, name)

for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except:
            continue
    if "climbs" in data:
        workout_date = data.get("date")
        try:
            date_obj = datetime.strptime(workout_date, "%d-%m-%Y").date()
            name = data.get("name", "Outdoor")  # fallback name
            outdoor_sessions.append((date_obj, name))
        except:
            continue

# Collect dates from workouts
for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

    # Skip files that are for outdoor climbs
    if "exercises" not in data:
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

# Plot lines to mark outdoor sections
for dt, name in outdoor_sessions:
    xi = (datetime.combine(dt, datetime.min.time()) - start_date).days

    print(f"Outdoor session at x={xi}, date={dt}, name={name}")
    ax.axvline(x=xi, color="gray", linestyle="--", linewidth=1.5, alpha=0.9, zorder=10)
    #ax.text(
    #    xi, max(total_intensity)*0.9,
    #    name,
    #    ha="right", va="bottom",
    #    fontsize=10, color="gray", rotation=0
    #)



# Format the x-axis.
ax.set_xticks(x)
ax.set_xlabel("Days")
ax.set_ylabel("Intensity")
ax.set_title(" ")

from matplotlib.lines import Line2D
# Custom legend entry for outdoor sessions
outdoor_legend = Line2D([0], [0], color="gray", linestyle="--", linewidth=1.0, label="Outdoor session")
handles, labels = ax.get_legend_handles_labels()
handles.append(outdoor_legend)
labels.append("Outdoor session")
ax.legend(handles, labels, title="Exercise Type", loc="upper left", bbox_to_anchor=(1, 1))


plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
