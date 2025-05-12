**CrimPy**
-

Python scripts to analyse and display data from workouts for rock climbing, in order to track progressions and changes of intensity.

The intensity is meant to measure the overall effort.
It is computed for certain exercises (see below) from empirical formulae which can be found in ```src/crimPy/intensity./py```

Usage
-
The template file ```workout_template.json``` can be edited on the phone during a workout. It can then be moved in the ***data/*** directory.

Run ```./makeplots.sh``` to produce the plots from all JSON files in ***data/***

Installation is standard: run ```pip install .``` in the cloned directory.

Excercises supported:
-

- Campus moves
- Pullup
- Fingerboard (7:3 repeaters)
- Deadhang
- Projects (boulder problems at max effort)
- Free climbs (boulder problems below project level)
- Lead and top rope routes

Examples of plots produced:
-


![intensity.png](plots/Intensity.png)

![weekly_avg_intensity.png](plots/weekly_avg_intensity.png)

![pullups_progression.png](plots/pullups_progression.png)

![fingerboard_progression.png](plots/fingerboard_progression.png)

![campusboard_progression.png](plots/campusboard_progression.png)