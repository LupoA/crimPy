# apps/plot_workouts.py

import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
import matplotlib.colors as mcolors
from crimpy.campusboard import CampusBoard, extract_edge_value



# Data directory
data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

# Container for all campus board workouts
campus_board_workouts = []

# Loop over all JSON files in the data directory
json_files = glob.glob(os.path.join(data_dir, "*.json"))
for file_path in json_files:
    with open(file_path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")
            continue

    # Parse the workout date
    workout_date = data.get("date")
    if not workout_date:
        print(f"Error: missing date in {file_path}")
    try:
        date_obj = datetime.strptime(workout_date, "%d-%m-%Y")
    except ValueError as e:
        print(f"Date format error in {file_path}: {e}")
        continue

    # Iterate through exercises in the file to fish for campus board
    for exercise in data.get("exercises", []):
        # Check if the exercise is executed and order is non-zero.
        if exercise.get("executed") and exercise.get("order", 0) != 0:
            if exercise["type"] == "campus board":
                for s in exercise.get("sets", []):
                    if "steps" not in s:
                        continue
                    cb = CampusBoard(
                        date=date_obj,
                        edge=s.get("edge"),
                        steps_str=s.get("steps"),
                        timeoff=s.get("timeoff"),
                        sides=s.get("sides")
                    )
                    campus_board_workouts.append(cb)

# Aggregate data by date and edge
moves_by_date_edge = defaultdict(lambda: defaultdict(int))
spread_by_date_edge = defaultdict(lambda: defaultdict(int))

for cb in campus_board_workouts:
    date_str = cb.date.strftime("%d-%m-%Y")
    moves_by_date_edge[date_str][cb.edge] += cb.moves
    spread_by_date_edge[date_str][cb.edge] += cb.spread

sorted_dates = sorted(moves_by_date_edge.keys(), key=lambda d: datetime.strptime(d, "%d-%m-%Y"))

# Determine unique edges
unique_edges = set()
for v in moves_by_date_edge.values():
    unique_edges.update(v.keys())
unique_edges = sorted(unique_edges)

# Create mapping from edge to numeric value if applicable
edge_values = {edge: extract_edge_value(edge) for edge in unique_edges}
numeric_values = [v for v in edge_values.values() if v is not None]
min_edge = min(numeric_values) if numeric_values else 0
max_edge = max(numeric_values) if numeric_values else 1

# Define colors: scales of blue showing smaller edges as more intense.
# For non-numeric edges (e.g. "sphere"), assign a default light gray
edge_color = {}
for edge, value in edge_values.items():
    if value is None:
        edge_color[edge] = "lightgray"
    else:
        # Normalize and invert such that smaller edges get a more vivid color
        norm = (value - min_edge) / (max_edge - min_edge) if max_edge > min_edge else 0
        inv_norm = 0.2 + 0.8 * (1 - norm)  # ensure a minimum value so that largest edge is not white...
        edge_color[edge] = plt.cm.Blues(inv_norm)

# Time to plot!
moves_data = {edge: [] for edge in unique_edges}
spread_data = {edge: [] for edge in unique_edges}
for d in sorted_dates:
    for edge in unique_edges:
        moves_data[edge].append(moves_by_date_edge[d].get(edge, 0))
        spread_data[edge].append(spread_by_date_edge[d].get(edge, 0))

x = np.arange(len(sorted_dates))

# Stacked bars for total number of moves
fig, ax = plt.subplots(figsize=(10, 6))
bottom = np.zeros(len(sorted_dates))
for edge in unique_edges:
    ax.bar(x, moves_data[edge], bottom=bottom, color=edge_color[edge], label=f"{edge}")
    bottom += np.array(moves_data[edge])
ax.set_xticks(x)
ax.set_xticklabels(sorted_dates, rotation=45)
ax.set_xlabel("Date")
ax.set_ylabel("# Moves")
ax.set_title("Campus Board progression")
ax.legend()
plt.tight_layout()
plt.show()

# Plot total spread as a stacked bar chart.
fig2, ax2 = plt.subplots(figsize=(10, 6))
bottom = np.zeros(len(sorted_dates))
for edge in unique_edges:
    ax2.bar(x, spread_data[edge], bottom=bottom, color=edge_color[edge], label=f"Edge {edge}")
    bottom += np.array(spread_data[edge])
ax2.set_xticks(x)
ax2.set_xticklabels(sorted_dates, rotation=45)
ax2.set_xlabel("Date")
ax2.set_ylabel("Spread per move")
ax2.set_title("Campus Board progression")
ax2.legend()
plt.tight_layout()
plt.show()
