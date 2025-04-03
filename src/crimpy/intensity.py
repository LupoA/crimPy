import re
import numpy as np

def time_str_to_seconds(time_str):
    """
    Convert a time string like '7s' or '15m' to seconds.
    """
    if time_str is None:
        return 0
    time_str = time_str.strip().lower()
    match = re.match(r"(\d+\.?\d*)([sm])", time_str)
    if match:
        value, unit = match.groups()
        value = float(value)
        if unit == "s":
            return value
        elif unit == "m":
            return value * 60
    return 0


class WorkoutIntensityCalculator:
    def __init__(self, workout_data):
        """
        workout_data: dict loaded from a workout JSON.
        """
        self.data = workout_data

    def calculate_intensity(self):
        """
        Calculates total intensity by summing the intensity from each exercise.
        """
        breakdown = self.calculate_intensity_breakdown()
        return sum(breakdown.values())

    def calculate_intensity_breakdown(self):
        """
        Returns a dictionary with intensity contributions per exercise type.
        The keys are: "fingerboard", "campusboard", "pullup", "project".
        """
        breakdown = {
            "fingerboard": 0.0,
            "campusboard": 0.0,
            "pullup": 0.0,
            "project": 0.0,
        }
        for exercise in self.data.get("exercises", []):
            # Only consider executed exercises with nonzero order.
            if not exercise.get("executed", False) or exercise.get("order", 0) == 0:
                continue
            ex_type = exercise.get("type", "").lower()
            if ex_type == "fingerboard":
                breakdown["fingerboard"] += self.fingerboard_intensity(exercise)
            elif ex_type == "campus board":
                breakdown["campusboard"] += self.campusboard_intensity(exercise)
            elif ex_type == "pullup":
                breakdown["pullup"] += self.pullup_intensity(exercise)
            elif ex_type == "project":
                breakdown["project"] += self.project_intensity(exercise)
        return breakdown

    def extract_edge_value(self, edge_str):
        """
        Extracts the numeric part from an edge string (e.g., '20mm' -> 20).
        Returns None if not found.
        """
        try:
            numeric_part = ''.join(filter(lambda c: c.isdigit() or c == '.', edge_str))
            if numeric_part:
                return float(numeric_part)
        except Exception:
            pass
        return None

    def fingerboard_intensity(self, exercise):
        """
        For fingerboard sets, we propose:

          intensity_set = (reps * timeon) / (timeoff + 0.5 * rest) * (1 / edge)

        Then we sum over all sets and multiply by a scaling constant.
        """
        intensity = 0.0
        K_fb = 0.8  # scaling constant
        for s in exercise.get("sets", []):
            edge_val = self.extract_edge_value(s.get("edge", ""))
            edge_factor = 1.0 / np.sqrt(edge_val) if edge_val and edge_val != 0 else 1.0
            reps = s.get("reps", 0)
            timeon = time_str_to_seconds(s.get("timeon", "0s"))
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            rest = time_str_to_seconds(s.get("rest", "0s"))

            intensity_set = (timeon/7)*0.2 + (3/timeoff)*0.1 + (35*edge_factor)*0.4 + (reps/6)*0.3
            intensity_set /= np.log(np.e - 1 + rest/60)
            #print(edge_val, reps, timeon, timeoff, rest)
            #print("total, intensity_set, reps*timeone, denom, edge_fact ", K_fb * intensity, intensity_set, reps*timeon, denom, edge_factor)
            intensity += intensity_set
        return K_fb * intensity

    def campusboard_intensity(self, exercise):
        """
        For campus board, we consider:

          intensity_set = (span * num_steps) / timeoff * (1 / edge)

        where:
          - span = (max(steps) - min(steps))
          - num_steps = number of moves in the "steps" string.
        """
        intensity = 0.0
        K_cb = 0.9  # scaling constant
        for s in exercise.get("sets", []):
            edge_val = self.extract_edge_value(s.get("edge", ""))
            edge_factor = 1.0 / edge_val if edge_val and edge_val != 0 else 1/35
            steps_str = s.get("steps", "")
            try:
                steps = [float(x) for x in steps_str.split("-") if x]
            except:
                steps = []
            if not steps:
                continue
            num_steps = len(steps)
            span = max(steps) - min(steps)
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            intensity_set = (span/4)*0.25 + ((num_steps/5)*0.35) + (35*edge_factor)*0.4
            intensity_set /= np.log(np.e- 1 + timeoff/90)
            intensity += intensity_set
        return K_cb * intensity

    def pullup_intensity(self, exercise):
        """
        For pullups, we propose:

          intensity_set = (repetitions * (1 + weight/10)) / (timeoff + 1)
        """
        intensity = 0.0
        K_pu = 2  # scaling constant
        for s in exercise.get("sets", []):
            reps = s.get("repetitions", 0)
            if "weight_kg" in s:
                weight = float(s["weight_kg"])
            elif "weight_lb" in s:
                weight = float(s["weight_lb"]) * 0.453592
            else:
                weight = 0.0
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            intensity_set = (reps/8)*0.5 + (weight/10)*0.5
            intensity_set /= np.log(np.e - 1 + timeoff / 180)
            intensity += intensity_set
        return K_pu * intensity

    def project_intensity(self, exercise):
        """
        For project exercises, we propose:

          intensity_set = attempts / (timeoff + 1)
        """
        intensity = 0.0
        K_proj = 1  # scaling constant
        for s in exercise.get("sets", []):
            attempts = s.get("attempts", 0)
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            intensity_set = attempts
            intensity_set /= np.log(np.e - 1 + timeoff / 300)
            intensity += intensity_set
        return K_proj * intensity
