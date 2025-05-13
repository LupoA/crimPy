import re
import numpy as np

MY_WEIGHT_KG = 63

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
            "deadhang": 0.0,
            "free_climbs": 0.0,
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
            elif ex_type == "deadhang":
                breakdown["deadhang"] += self.deadhang_intensity(exercise)
            elif ex_type == "free_climbs":
                breakdown["free_climbs"] += self.free_climbs_intensity(exercise)
        breakdown["outdoor"] = self.outdoor_intensity()
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
        todo write description
        """
        intensity = 0.0
        K_fb = 0.0004  # scaling constant
        for s in exercise.get("sets", []):
            edge_val = self.extract_edge_value(s.get("edge", ""))
            edge_ref = 35.0  # reference edge in mm
            alpha = 1.1  # exponent > 1 for convex reward

            edge_factor = (edge_ref / edge_val) ** alpha if edge_val and edge_val != 0 else 1.0

            reps = s.get("reps", 0)
            timeon = time_str_to_seconds(s.get("timeon", "0s"))
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            rest = time_str_to_seconds(s.get("rest", "0s"))
            intensity_set = (timeon/7)*0.3 + (3/timeoff)*0.2 + (35*edge_factor)*0.5
            intensity_set *= reps
            rest_factor = 1.8*np.log(np.e - 1 + rest/1800)
            #print("Fingerboard ::: ", f"[{self.source_file} | {self.date}] edge: {edge_val}, I = {intensity_set:.3f} : "f"{(timeon / 7) * 0.2:.2f}, {(3 / timeoff) * 0.1:.2f}, {(35 * edge_factor) * 0.4:.2f}, {(reps / 6) * 0.3:.2f}, {rest_factor:.2f}")
            intensity_set /= rest_factor
            intensity += intensity_set
        return K_fb * intensity

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
        K_cb = 0.014  # scaling constant

        # reference values
        ref_span = 3.0
        ref_steps = 6.0
        # weights
        w_span = 0.25
        w_step = 0.35
        w_edge = 0.40
        alpha_edge = 2
        alpha_span = 1.3
        alpha_step = 1.2

        for s in exercise.get("sets", []):
            edge_val = self.extract_edge_value(s.get("edge", ""))
            edge_factor = (1.0 / edge_val) if edge_val and edge_val != 0 else 1/35
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

            edge_term = ((35 * edge_factor)**alpha_edge) * w_edge
            span_term = (span_norm ** alpha_span) * w_span
            step_term = (step_norm ** alpha_step)* w_step

            intensity_set = span_term + step_term + edge_term

            rest_factor = np.log(np.e- 1 + timeoff/1200) / 0.6
            intensity_set /= rest_factor
            intensity += intensity_set

        #print("Campusboard ::: Intensity contribution ",  K_cb * intensity / 10, f" [{self.source_file} | {self.date}]")
        return K_cb * intensity

    def pullup_intensity(self, exercise):
        """
        Adjust variable at the top to your own weight
        """
        intensity = 0.0
        K_pu = 0.005  # scaling constant

        alpha = 4
        for s in exercise.get("sets", []):
            reps = s.get("repetitions", 0)
            if "weight_kg" in s:
                weight = float(s["weight_kg"])
            elif "weight_lb" in s:
                weight = float(s["weight_lb"]) * 0.453592
            else:
                weight = 0.0
            edge = str(s.get("edge", "")).lower()
            if edge == "bar":
                edge_multiplier = 1
            elif edge == "pinch":
                edge_multiplier = 1.15
            elif edge == 'chin-up':
                edge_multiplier = 0.85
            else:
                edge_val = self.extract_edge_value(s.get("edge", ""))
                edge_multiplier = 35 / edge_val if edge_val else 1
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))

            weight_term = (MY_WEIGHT_KG + weight) / MY_WEIGHT_KG
            weight_term = weight_term ** alpha

            intensity_set = weight_term * reps

            intensity_set *= edge_multiplier
            intensity_set /= np.log(np.e - 1 + timeoff / 180)
            intensity += intensity_set
        return K_pu * intensity

    def project_intensity(self, exercise):
        """
        For project exercises, (boulders at max effort)

          intensity_set = attempts * log(e - 1 + rest[s]/300s)
        """
        intensity = 0.0
        K_proj = 0.026  # scaling constant is quite small.
                      # Project intensity is very dependent on the grade and the effort put,
                      # which is not being measured
        for s in exercise.get("sets", []):
            attempts = s.get("attempts", 0)
            timeoff = time_str_to_seconds(s.get("timeoff", "0s"))
            intensity_set = attempts
            intensity_set /= np.log(np.e - 1 + timeoff / 300)
            intensity += intensity_set
        return K_proj * intensity

    def free_climbs_intensity(self, exercise):
        """
        For free_climbs exercises: (below project level)

          intensity_set = number_of_climbs
          total_intensity = K_free * sum(intensity_set)

        We choose K_free so that 1 free climb ≈ 1/5 of 1 project attempt.
        Since project gives ~0.045 per attempt at rest=0, we set:

          K_free = 0.045
        """
        intensity = 0.0
        K_free = 0.45 / 5

        for s in exercise.get("sets", []):
            number = s.get("number", 0)
            intensity += number

        return K_free * intensity / 10


    def outdoor_intensity(self):
        """
        Manually score each outdoor climb attempt based on grade, type, and success.
        Returns a single float (summing all attempts × per‐attempt score).
        """
        # Base scores for lead attempts
        GRADE_SCORES = {
            "5b": 0.1,
            "5b+": 0.15,
            "5c":  0.2,
            "5c+": 0.25,
            "6a":  0.3,
            "6a+": 0.35,
            "6b":  0.40,
            "6b+": 0.45,
            "6c":  0.50,
            "6c+": 0.55,
            "7a":  0.6,
            "7a+": 0.65
        }
        total = 0.0

        for climb in self.data.get("climbs", []):
            if not climb.get("executed", False) or climb.get("order", 0) == 0:
                continue

            typ = climb.get("type", "").lower()
            # toprope is 0.1 less on every score
            type_penalty = 0.1 if typ == "toprope" else 0.0

            for s in climb.get("sets", []):
                grade = s.get("Grade", "").lower()
                base = GRADE_SCORES.get(grade)
                if base is None:
                    # unknown grade → skip
                    print("Unkown grade : ", grade, ". Skipping.")
                    continue

                # subtract for toprope
                score = base - type_penalty
                # subtract if not successful
                if not s.get("success", False):
                    score -= 0.1

                # each attempt gets that score
                attempts = s.get("attempts", 1)
                total += max(score, 0) * attempts

        return total
    def deadhang_intensity(self, exercise):
        """
        Compute intensity for deadhang sets.

        Reference values:
          - edge_ref   = 25 mm
          - time_ref   = 7 s
        Weights (sum to 1.0):
          w_edge   = 0.6
          w_time   = 0.3
          w_weight = 0.1

        Two‑hand hangs register at 50% intensity of a one‑hand hang.
        """
        edge_ref   = 35.0
        time_ref   = 7.0
        weight_ref = 6
        w_edge, w_time, w_weight = 0.5, 0.2, 0.3
        total = 0.0
        K_dh = 0.035

        for s in exercise.get("sets", []):
            # 1) Edge term (smaller = harder)
            edge_val    = self.extract_edge_value(s.get("edge","")) or edge_ref
            edge_term   = (edge_ref / edge_val) * w_edge

            # 2) Time‑on term
            ton         = time_str_to_seconds(s.get("timeon","0s"))
            time_term   = (ton / time_ref) * w_time

            # 3) Weight term
            weight      = float(s.get("weight_kg", 0))
            weight_term = (weight / (weight_ref)) * w_weight

            # 4) Validate hands
            hands = s.get("hands", 1)
            if hands not in (1, 2):
                raise ValueError(f"Invalid number of hands in deadhang set: {hands}. Must be 1 or 2.")
            hand_multiplier = 1.0 if hands == 1 else 0.5

            # 5) Combine
            set_intensity = hand_multiplier * (edge_term + time_term + weight_term)
            total += set_intensity
        total *= K_dh
        return total
