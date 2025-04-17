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
    """
    Each exercise has a scaling factor to adjust the perceived effort. Exercises with features that are hard to measure (project grade, effort, ...) have a lower scaling factor
    in order to minimise the effect of these on the overall intensity.
    Each exercise has certain measurable quantity (reps, weight, ...) These are divided by a reference value and then summed with weights that sum to 1.
    In this way, if an excerises hits all its reference values, it will contribute to the intensity with a factor of one.
    The intensity is also very weakly depending on the rest between sets, through a logarithmic function.
    """
    def __init__(self, workout_data, source_file=None, date=None):
        """
        workout_data: dict loaded from a workout JSON.
        """
        self.data = workout_data
        self.source_file = source_file
        self.date = date

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

          intensity_set = [(timeon/timeon0)*0.2 + (timeoff0/timeoff)*0.1 + (edge0*edge)*0.4 + (reps/reps0)*0.3] * log(e - 1 + rest[s]/300s)

        xxx0 being your reference numbers, and the
        xxx_weights are supposed to sum to 1
        Then we sum over all sets and multiply by a scaling constant.
        """
        intensity = 0.0
        K_fb = 0.03  # scaling constant
        for s in exercise.get("sets", []):
            edge_val = self.extract_edge_value(s.get("edge", ""))
            edge_ref = 35.0  # reference edge in mm
            alpha = 1.5  # exponent > 1 for convex reward

            edge_factor = (edge_ref / edge_val) ** alpha if edge_val and edge_val != 0 else 1.0

            reps = s.get("reps", 0)
            timeon = time_str_to_seconds(s.get("timeon", "0s"))
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            rest = time_str_to_seconds(s.get("rest", "0s"))
            intensity_set = (timeon/7)*0.2 + (3/timeoff)*0.1 + (35*edge_factor)*0.4 + (reps/6)*0.3
            rest_factor = 1.8*np.log(np.e - 1 + rest/1800)
            print("Fingerboard ::: ", f"[{self.source_file} | {self.date}] edge: {edge_val}, I = {intensity_set:.3f} : "
                  f"{(timeon / 7) * 0.2:.2f}, {(3 / timeoff) * 0.1:.2f}, {(35 * edge_factor) * 0.4:.2f}, {(reps / 6) * 0.3:.2f}, {rest_factor:.2f}")
            intensity_set /= rest_factor
            intensity += intensity_set
        return K_fb * intensity / 10 # all are divided by 10 so that the typical intensity is O(1)

    def campusboard_intensity(self, exercise):
        """
        For campus board, we consider:

          intensity_set = intensity_set = [(span/span0)*span_weight + (num_steps/num_steps0)*nsteps_weight + edge0/edge] * log(e - 1 + rest[s]/300s)
          xxx0 being your reference numbers, and the
          xxx_weights are supposed to sum to 1

        where:
          - span = (max(steps) - min(steps))
          - num_steps = number of moves in the "steps" string.
        """
        intensity = 0.0
        K_cb = 0.25  # scaling constant

        # reference values
        ref_span = 3.0
        ref_steps = 6.0
        # weights
        w_span = 0.25
        w_step = 0.35
        w_edge = 0.40

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

            span_norm = span / ref_span
            step_norm = (span / num_steps) / (ref_span / ref_steps)

            edge_term = (35 * edge_factor) * w_edge
            span_term = span_norm * w_span
            step_term = step_norm * w_step

            intensity_set = span_term + step_term + edge_term

            rest_factor = np.log(np.e- 1 + timeoff/1200) / 0.6
            intensity_set /= rest_factor
            intensity += intensity_set

            print("Campusboard ::: ", f"[{self.source_file} | {self.date}] edge: {edge_val}, I = {intensity_set:.3f} : edge contrib: {(35*edge_factor)*0.4:.2f}, steps contrib : {((num_steps/6)*0.35):.2f}, span contrib {(span/3)*0.25:.2f}, rest factor {rest_factor:2f}")

        return K_cb * intensity / 10

    def pullup_intensity(self, exercise):
        """
        For pullups, we propose:

          intensity_set = [(reps/reps0)*reps_weight + (weight/weight0)*weight_weight] * log(e - 1 + rest[s]/300s)
          reps0, weight0 being your reference numbers, and the
          xxx_weights are supposed to sum to 1
        """
        intensity = 0.0
        K_pu = 0.9  # scaling constant
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
        return K_pu * intensity / 10

    def project_intensity(self, exercise):
        """
        For project exercises, we propose:

          intensity_set = attempts * log(e - 1 + rest[s]/300s)
        """
        intensity = 0.0
        K_proj = 0.45  # scaling constant is quite small.
                      # Project intensity is very dependent on the grade and the effort put,
                      # which is not being measured
        for s in exercise.get("sets", []):
            attempts = s.get("attempts", 0)
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            intensity_set = attempts
            intensity_set /= np.log(np.e - 1 + timeoff / 300)
            intensity += intensity_set
        return K_proj * intensity / 10
