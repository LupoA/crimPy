import os
import json
import glob
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from crimpy.intensity import WorkoutIntensityCalculator

# Load all JSON files
data_dir   = os.path.join(os.path.dirname(__file__), "..", "data")
json_files = glob.glob(os.path.join(data_dir, "*.json"))

# Build a list of all sessions (date_obj, data_dict, is_outdoor)
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

# Extract workout dates to define the x‐axis zero
workout_dates = sorted({dt for dt, d, is_out in sessions if not is_out})
if not workout_dates:
    raise RuntimeError("No workout sessions found.")
start_date = workout_dates[0]

# Sort *all* sessions by date
sessions.sort(key=lambda x: x[0])

# Prepare arrays for plotting
all_dates = [dt for dt, _, _ in sessions]
x_all     = np.array([(dt - start_date).days for dt in all_dates])

# Containers
fb_arr    = []
cb_arr    = []
pu_arr    = []
proj_arr  = []
dh_arr    = []
fc_arr    = []  # free_climbs array

total_arr = []

for dt, d, is_out in sessions:
    br = WorkoutIntensityCalculator(d).calculate_intensity_breakdown()
    fb    = br.get("fingerboard", 0.0)
    cb    = br.get("campusboard", 0.0)
    pu    = br.get("pullup",     0.0)
    proj  = br.get("project",    0.0)
    dh    = br.get("deadhang",   0.0)
    fc    = br.get("free_climbs", 0.0)  # free climbs intensity
    out_v = br.get("outdoor",    0.0)

    # if this was an outdoor‐only session, we want zero bars
    if is_out:
        fb, cb, pu, proj, dh, fc = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    fb_arr.append(fb)
    cb_arr.append(cb)
    pu_arr.append(pu)
    proj_arr.append(proj)
    dh_arr.append(dh)
    fc_arr.append(fc)
    total_arr.append(fb + cb + pu + proj + dh + fc + out_v)

fb_arr   = np.array(fb_arr)
cb_arr   = np.array(cb_arr)
pu_arr   = np.array(pu_arr)
proj_arr = np.array(proj_arr)
dh_arr   = np.array(dh_arr)
fc_arr   = np.array(fc_arr)
total_arr= np.array(total_arr)

# Plot:
colors = {
    "fingerboard": "#e41a1c",
    "campusboard": "#377eb8",
    "pullup":      "#4daf4a",
    "project":     "#9370DB",
    "deadhang":    "#ff7f00",
    "free_climbs": "#9932CC",
}

fig, ax = plt.subplots(figsize=(12,7))
bottom = np.zeros_like(x_all, dtype=float)

# indoor session's stacked bars
ax.bar(x_all, fb_arr,   bottom=bottom, color=colors["fingerboard"], label="Fingerboard")
bottom += fb_arr
ax.bar(x_all, dh_arr,   bottom=bottom, color=colors["deadhang"],    label="Deadhang")
bottom += dh_arr
ax.bar(x_all, cb_arr,   bottom=bottom, color=colors["campusboard"], label="Campusboard")
bottom += cb_arr
ax.bar(x_all, pu_arr,   bottom=bottom, color=colors["pullup"],     label="Pullup")
bottom += pu_arr
ax.bar(x_all, proj_arr, bottom=bottom, color=colors["project"],    label="Bouldering")
bottom += proj_arr
#ax.bar(x_all, fc_arr,   bottom=bottom, color=colors["free_climbs"],label="Climbs (< max effort)")
#bottom += fc_arr

# continuous total line through all points
ax.plot(x_all, total_arr,
        color="black", marker="o", linestyle="-", linewidth=2,
        label="Total Intensity")

# vertical dashed lines on pure outdoor days
for dt, name, is_out in sessions:
    if is_out:
        xi = (dt - start_date).days
        ax.axvline(x=xi, color="gray", linestyle="--", linewidth=1.5, alpha=0.7)

# xy axis
ax.set_xticks(x_all)
ax.set_xlabel("Days")
ax.set_ylabel("Intensity")
ax.set_title("")  # blank title

# Legend: bars + line + dashed outdoor marker
handles, labels = ax.get_legend_handles_labels()
dash = Line2D([0],[0], color="gray", linestyle="--", linewidth=1.5, label="Outdoor session")
handles.append(dash); labels.append("Outdoor session")
ax.legend(handles, labels, title="Exercise Type", loc="upper left", bbox_to_anchor=(1,1))

plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "..", "plots", "Intensity.png"))
#plt.show()