# src/crimpy/fingerboard.py

import numpy as np
import re
from crimpy.intensity import time_str_to_seconds  # reuse the helper from intensity module, if available

class Fingerboard:
    def __init__(self, date, edge, reps, timeon, timeoff, rest):
        """
        Represents a single fingerboard set.

        Args:
            date (datetime): The workout date.
            edge (str): e.g., "35mm" or "20mm"
            reps (int): Number of repetitions.
            timeon (str): Time on (e.g., "7s").
            timeoff (str): Time off (e.g., "3s").
            rest (str): Rest time (e.g., "60s").
        """
        self.date = date
        self.edge = edge
        self.reps = reps
        self.timeon = timeon
        self.timeoff = timeoff
        self.rest = rest
        self.effort = self.compute_effort()

    def compute_effort(self):
        """
        Computes an "effort" metric for a fingerboard set based on the formula:

            effort_set = [(timeon/7)*0.2 + (3/timeoff)*0.1 + (35*edge_factor)*0.4 + (reps/6)*0.3]
                         / ln(e - 1 + rest/60)

        where:
          - edge_factor = 1/sqrt(edge_value), with edge_value extracted from the edge string.
        """
        ton = time_str_to_seconds(self.timeon)
        toff = time_str_to_seconds(self.timeoff)
        r = time_str_to_seconds(self.rest)
        edge_val = self.extract_edge_value(self.edge)
        edge_factor = 1.0 / np.sqrt(edge_val) if edge_val and edge_val != 0 else 1.0

        # Calculate the components
        part1 = (ton / 7) * 0.2
        part2 = (3 / toff) * 0.1 if toff > 0 else 0
        part3 = (35 * edge_factor) * 0.4
        part4 = (self.reps / 6) * 0.3

        effort_set = (part1 + part2 + part3 + part4)
        # Divide by ln(e - 1 + rest/60) to account for longer rest lowering effort.
        divisor = np.log(np.e - 1 + r / 60) if r > 0 else 1
        return effort_set / divisor

    def extract_edge_value(self, edge_str):
        """
        Extracts the numeric part from an edge string (e.g., "35mm" → 35).
        Returns None if no number is found.
        """
        try:
            numeric_part = ''.join(filter(lambda c: c.isdigit() or c == '.', edge_str))
            if numeric_part:
                return float(numeric_part)
        except Exception:
            pass
        return None
