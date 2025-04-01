# apps/plot_pullups.py

import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
import matplotlib.colors as mcolors
from crimpy.pullup import Pullup

data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
pullup_workouts = []

# Loop over all JSON files in the data directory
json_files = glob.glob(os.path.join(data_dir, "*.json"))
for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")
            continue

    # Parse date
    workout_date = data.get("date")
    if not workout_date:
        continue  # Skip files without a date.
    try:
        date_obj = datetime.strptime(workout_date, "%d-%m-%Y")
    except ValueError as e:
        print(f"Date format error in {file_path}: {e}")
        continue

    # Iterate through exercises in the file
    for exercise in data.get("exercises", []):
        # Check if the exercise is executed and order is non-zero.
        if exercise.get("executed") and exercise.get("order", 0) != 0:
            if exercise["type"] == "pullup":
                for s in exercise.get("sets", []):
                    # Create a Pullup instance for each set.
                    p = Pullup(date=date_obj,
                               edge=s.get("edge"),
                               set_data=s)
                    pullup_workouts.append(p)

# Group data by date and by weight, store total reps / weight / date
reps_by_date_weight = defaultdict(lambda: defaultdict(int))
for p in pullup_workouts:
    date_str = p.date.strftime("%d-%m-%Y")
    # Only group if a weight is provided.
    if p.weight_kg is not None:
        reps_by_date_weight[date_str][p.weight_kg] += p.repetitions

# Get sorted dates
sorted_dates = sorted(reps_by_date_weight.keys(), key=lambda d: datetime.strptime(d, "%d-%m-%Y"))

# Determine unique weights across workouts
unique_weights = set()
for weight_dict in reps_by_date_weight.values():
    unique_weights.update(weight_dict.keys())
unique_weights = sorted(unique_weights)

# Map weights to colors with proportional intensity
if unique_weights:
    min_weight = min(unique_weights)
    max_weight = max(unique_weights)
else:
    min_weight, max_weight = 0, 1

weight_color = {}
for weight in unique_weights:
    # Normalize weight between 0 and 1.
    norm = (weight - min_weight) / (max_weight - min_weight) if max_weight > min_weight else 0
    # Rescale norm to [0.2, 1.0] so that the lightest weight (norm=0) gets 0.2
    scaled_norm = 0.2 + 0.8 * norm
    weight_color[weight] = plt.cm.Greens(scaled_norm)


# Plotting!
# For each date and for each weight, we need the total reps
reps_data = {weight: [] for weight in unique_weights}
for d in sorted_dates:
    for weight in unique_weights:
        reps_data[weight].append(reps_by_date_weight[d].get(weight, 0))

x = np.arange(len(sorted_dates))

# Plotting total repetitions as a stacked bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bottom = np.zeros(len(sorted_dates))
for weight in unique_weights:
    ax.bar(x, reps_data[weight], bottom=bottom, color=weight_color[weight],
           label=f"Additional weight: {weight:.1f} kg")
    bottom += np.array(reps_data[weight])

ax.set_xticks(x)
ax.set_xticklabels(sorted_dates, rotation=45)
ax.set_xlabel("Date")
ax.set_ylabel("# Repetitions")
# If pullup sets always use the same edge include that in the title
ax.set_title("Pullup progression")
ax.legend()
plt.tight_layout()
plt.show()
