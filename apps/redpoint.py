import os
import json
import glob
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime

# Helper to sort grades naturally
def grade_key(g):
    # e.g. "5c+" -> (5,2,1), "6a"->(6,0,0)
    plus = g.endswith('+')
    core = g[:-1] if plus else g
    num = int(''.join(filter(str.isdigit, core)))
    letter = ''.join(filter(str.isalpha, core))
    letter_order = {'a':0, 'b':1, 'c':2}
    return (num, letter_order.get(letter,0), 1 if plus else 0)

# Full list of grades in order
all_grades = ['5b','5b+','5c','5c+',
              '6a','6a+','6b','6b+',
              '6c','6c+','7a','7a+']

# Count redpointed lead grades
redpoint_counts = Counter()

data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
for path in glob.glob(os.path.join(data_dir, "*.json")):
    with open(path) as f:
        try:
            d = json.load(f)
        except json.JSONDecodeError:
            continue
    climbs = d.get('climbs')
    if not climbs:
        continue
    for climb in climbs:
        if climb.get('type','').lower() != 'lead' or not climb.get('executed',False):
            continue
        for s in climb.get('sets',[]):
            if s.get('redpoint') and s.get('success'):
                grade = s.get('Grade') or s.get('grade')
                if grade:
                    redpoint_counts[grade] += 1

# Prepare grade range
observed = sorted(redpoint_counts.keys(), key=grade_key)
if not observed:
    print("No redpointed leads found.")
    exit(0)
min_g, max_g = observed[0], observed[-1]
start = all_grades.index(min_g)
end   = all_grades.index(max_g)
grades = all_grades[start:end+1]

# Build counts including zeros
counts = [redpoint_counts.get(g, 0) for g in grades]

# Plot
y_pos = range(len(grades))
fig, ax = plt.subplots(figsize=(8,6))
ax.barh(y_pos, counts, align='center', color='teal')
ax.set_yticks(y_pos)
ax.set_yticklabels(grades)
ax.set_xlabel('Count')
ax.set_title('Redpointed grades on Lead')
plt.tight_layout()
plt.savefig(os.path.join(os.path.dirname(__file__), "..", "plots", "redpointed_grades.png"))