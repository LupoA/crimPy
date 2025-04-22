import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from crimpy.intensity import time_str_to_seconds

#  Reference parameters and scale factor
K_cb      = 0.25 / 10
ref_span  = 3.0
ref_steps = 6.0
w_span    = 0.25
w_step    = 0.35
w_edge    = 0.40

# load all json workout files
data_dir   = os.path.join(os.path.dirname(__file__), "..", "data")
json_files = glob.glob(os.path.join(data_dir, "*.json"))

# aggregate by edge
intensity_by_date_edge = defaultdict(lambda: defaultdict(float))

for path in json_files:
    with open(path) as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            continue

    # parse the workout date
    ds = data.get("date")
    if not ds:
        continue
    try:
        dt = datetime.strptime(ds, "%d-%m-%Y")
    except ValueError:
        continue
    date_str = dt.strftime("%d-%m-%Y")

    # find campus board exercise
    for ex in data.get("exercises", []):
        if not ex.get("executed", False) or ex.get("order", 0) == 0:
            continue
        if ex.get("type","" ).lower() != "campus board":
            continue

        # for each set, compute intensity contribution
        for s in ex.get("sets", []):
            edge = s.get("edge", "unknown")
            # numeric edge value (default to 35mm for non-numeric)
            ev = ''.join(filter(lambda c: c.isdigit() or c=='.', edge))
            edge_val    = float(ev) if ev else 35.0
            edge_factor = 1.0 / edge_val

            # steps & span
            steps = []
            for part in s.get("steps","" ).split("-"):
                try:
                    steps.append(float(part))
                except:
                    pass
            if not steps:
                continue
            num_steps = len(steps)
            span      = max(steps) - min(steps)

            # timeoff to seconds
            toff = time_str_to_seconds(s.get("timeoff","0s"))

            # normalized terms
            span_norm = span / ref_span
            step_norm = (span / num_steps) / (ref_span / ref_steps)

            # weighted sum
            intensity_set = (span_norm * w_span
                             + step_norm * w_step
                             + (35 * edge_factor) * w_edge)

            # wee rest penalty
            rest_factor = np.log(np.e - 1 + toff/1200) / 0.6
            intensity_set /= rest_factor

            # accumulate (we'll scale by K_cb after)
            intensity_by_date_edge[date_str][edge] += intensity_set

# multiply each date/edge sum by the global scaling
for date_str, edge_dict in intensity_by_date_edge.items():
    for edge in edge_dict:
        edge_dict[edge] = edge_dict[edge] * K_cb

# prepping plots
sorted_dates = sorted(intensity_by_date_edge.keys(),
                      key=lambda d: datetime.strptime(d, "%d-%m-%Y"))

# unique edges in sorted order
edges = sorted({e for ed in intensity_by_date_edge.values() for e in ed})

# color palette: Blues, smaller edges = deeper color
edge_values = {e: float(''.join(filter(str.isdigit,e)))
               if any(c.isdigit() for c in e) else None
               for e in edges}
nums = [v for v in edge_values.values() if v is not None]
min_e, max_e = (min(nums), max(nums)) if nums else (0,1)
edge_color = {}
for e,v in edge_values.items():
    if v is None:
        edge_color[e] = "lightgray"
    else:
        norm     = (v - min_e) / (max_e - min_e) if max_e>min_e else 0
        inv_norm = 0.2 + 0.8*(1-norm)
        edge_color[e] = plt.cm.Blues(inv_norm)

# build data arrays
x = np.arange(len(sorted_dates))
intensity_data = {e: [] for e in edges}
for date_str in sorted_dates:
    for e in edges:
        intensity_data[e].append(intensity_by_date_edge[date_str].get(e, 0.0))

# plotting time!
fig, ax = plt.subplots(figsize=(12,6))
bottom = np.zeros(len(x))

for e in edges:
    vals = np.array(intensity_data[e])
    ax.bar(x, vals, bottom=bottom, color=edge_color[e], label=e)
    bottom += vals

ax.set_xticks(x)
ax.set_xticklabels(sorted_dates, rotation=45)
ax.set_xlabel("Workout Date")
ax.set_ylabel("Campusboard Intensity")
ax.set_title("")

ax.legend(title="Edge", loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "..", "plots", "campusboard_progression.png"))
#plt.show()
