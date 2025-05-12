import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from crimpy.intensity import WorkoutIntensityCalculator

# Data directory (adjust path as needed)
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

# Container for all fingerboard intensity entries
effort_by_date_edge = defaultdict(lambda: defaultdict(float))

# Loop over all JSON files in the data directory
json_files = glob.glob(os.path.join(data_dir, "*.json"))
for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")
            continue

    # Get the workout date
    workout_date = data.get("date")
    if not workout_date:
        print(f"Error: missing date in {file_path}")
        continue
    try:
        date_obj = datetime.strptime(workout_date, "%d-%m-%Y")
    except ValueError as e:
        print(f"Date format error in {file_path}: {e}")
        continue
    date_str = date_obj.strftime("%d-%m-%Y")

    # Iterate through exercises to pick fingerboard sets
    for exercise in data.get("exercises", []):
        if not exercise.get("executed") or exercise.get("order", 0) == 0:
            continue
        if exercise.get("type", "").lower() != "fingerboard":
            continue

        # For each set, compute intensity of that single-set exercise
        for s in exercise.get("sets", []):
            # Ensure required keys are present
            if not all(k in s for k in ("edge", "reps", "timeon", "timeoff", "rest")):
                continue
            edge = s["edge"]
            # Build a one-set dummy exercise
            single = {**exercise, "sets": [s]}
            # Compute intensity of this set
            calc = WorkoutIntensityCalculator({"exercises": [single]})
            contrib = calc.fingerboard_intensity(single)
            # Accumulate by date and edge
            effort_by_date_edge[date_str][edge] += contrib

# Sort dates
sorted_dates = sorted(effort_by_date_edge.keys(), key=lambda d: datetime.strptime(d, "%d-%m-%Y"))

# Determine unique edges
unique_edges = sorted({e for dct in effort_by_date_edge.values() for e in dct})

# Map edge to numeric value for coloring
def extract_edge_value(edge_str):
    try:
        numeric_part = ''.join(filter(lambda c: c.isdigit() or c == '.', edge_str))
        if numeric_part:
            return float(numeric_part)
    except:
        pass
    return None

edge_values = {edge: extract_edge_value(edge) for edge in unique_edges}
numeric_values = [v for v in edge_values.values() if v is not None]
min_edge = min(numeric_values) if numeric_values else 0
max_edge = max(numeric_values) if numeric_values else 1

# Use a colormap (Oranges) so smaller edges are more intense
edge_color = {}
for edge, value in edge_values.items():
    if value is None:
        edge_color[edge] = "lightgray"
    else:
        norm = (value - min_edge) / (max_edge - min_edge) if max_edge > min_edge else 0
        inv_norm = 0.2 + 0.8 * (1 - norm)
        edge_color[edge] = plt.cm.Oranges(inv_norm)

# Prepare data for plotting
effort_data = {edge: [] for edge in unique_edges}
for d in sorted_dates:
    for edge in unique_edges:
        effort_data[edge].append(effort_by_date_edge[d].get(edge, 0.0))

x = np.arange(len(sorted_dates))

# Plot a stacked bar chart of fingerboard intensity over time
fig, ax = plt.subplots(figsize=(10, 6))
bottom = np.zeros(len(sorted_dates))
for edge in unique_edges:
    vals = np.array(effort_data[edge])
    ax.bar(x, vals, bottom=bottom, color=edge_color[edge], label=edge)
    bottom += vals

ax.set_xticks(x)
ax.set_xticklabels(sorted_dates, rotation=45)
ax.set_xlabel("Date")
ax.set_ylim(top=bottom.max() * 1.1)
ax.set_ylabel("Fingerboard Intensity [7:3 repeaters]")
ax.set_title("Progression")
ax.legend(title="Edge")
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "..", "plots", "fingerboard_progression.png"))
#plt.show()
