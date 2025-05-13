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

Example of estimated effort from excercise
--
***
**Fingerboard 7on 3off, six repeaters : Intensity for Edge Sizes**
```
Edge:   45 mm -> Intensity: 0.0317
Edge:   35 mm -> Intensity: 0.0414
Edge:   25 mm -> Intensity: 0.0595
Edge:   20 mm -> Intensity: 0.0757
Edge:   15 mm -> Intensity: 0.1034
Edge:   10 mm -> Intensity: 0.1609
Edge:    8 mm -> Intensity: 0.2054
Edge:    6 mm -> Intensity: 0.2814

```
***
**Pullups intensity for 8 reps varying weight**

```
Weight:  0 → Intensity: 0.0385
Weight:  8 → Intensity: 0.0620
Weight: 10 → Intensity: 0.0693
Weight: 14 → Intensity: 0.0858
Weight: 18 → Intensity: 0.1051
Weight: 20 → Intensity: 0.1159
Weight: 24 → Intensity: 0.1399
Weight: 32 → Intensity: 0.1989

```