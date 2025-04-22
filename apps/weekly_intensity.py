import os
import json
import glob
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from matplotlib.lines import Line2D

from crimpy.intensity import WorkoutIntensityCalculator

# Directory containing JSON workout files
data_dir   = os.path.join(os.path.dirname(__file__), "..", "data")
json_files = glob.glob(os.path.join(data_dir, "*.json"))

# Gather all sessions (date, data, is_outdoor)
sessions = []
for path in json_files:
    with open(path) as f:
        try:
            d = json.load(f)
        except:
            continue
    date_str = d.get("date")
    if not date_str:
        continue
    try:
        dt = datetime.strptime(date_str, "%d-%m-%Y").date()
    except:
        continue

    is_out = "climbs" in d and "exercises" not in d
    sessions.append((dt, d, is_out))

# Determine first workout Monday to zero our week count
workout_dates = [dt for dt, d, is_out in sessions if not is_out]
if not workout_dates:
    raise RuntimeError("No workout sessions found.")
first_date   = min(workout_dates)
start_monday = first_date - timedelta(days=first_date.weekday())

# Aggregate intensity by week index
weekly = defaultdict(lambda: defaultdict(float))
for dt, data, is_out in sessions:
    week_idx = (dt - start_monday).days // 7
    br       = WorkoutIntensityCalculator(data).calculate_intensity_breakdown()
    if is_out:
        weekly[week_idx]['outdoor']    += br.get('outdoor',   0.0)
    else:
        for key in ['fingerboard', 'deadhang', 'campusboard', 'pullup', 'project', 'outdoor']:
            weekly[week_idx][key] += br.get(key, 0.0)

# Sort weeks
weeks = sorted(weekly.keys())
x     = np.array(weeks)

# Build arrays per exercise type
types       = ['fingerboard', 'deadhang', 'campusboard', 'pullup', 'project', 'outdoor']
data_arrays = {t: np.array([weekly[w].get(t, 0.0) for w in weeks]) for t in types}

# Total intensity including outdoor-only
total_intensity = sum(data_arrays[t] for t in types)

# Colors for each type
colors = {
    'fingerboard': '#990000',
    'campusboard': '#2471a3',
    'pullup':      '#186A3B',
    'project':     '#76448A',
    'outdoor':     '#AEB6BF',
    'deadhang':    '#D35400'
}

# Plot stacked bars
fig, ax = plt.subplots(figsize=(12,7))
bottom = np.zeros_like(x, dtype=float)
for t in types:
    ax.bar(x, data_arrays[t], bottom=bottom, color=colors[t], label=t.capitalize())
    bottom += data_arrays[t]

# Continuous total intensity line through all weeks
ax.plot(x, total_intensity,
        color='black', marker='o', linestyle='-', linewidth=2,
        label='Total Intensity', zorder=10)

# X-axis formatting
ax.set_xticks(x)
ax.set_xlabel("Weeks Since First Workout")
ax.set_ylabel("Summed Intensity")
ax.set_title("")  # blank title

# Legend including outdoor session marker
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, title="Type", loc="upper left", bbox_to_anchor=(1,1))

plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "..", "plots", "weekly_avg_intensity.png"))
#plt.show()
