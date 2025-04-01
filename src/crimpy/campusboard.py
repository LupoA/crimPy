# src/campusboard.py

from datetime import datetime
import numpy as np


class CampusBoard:
    def __init__(self, date, edge, steps_str, timeoff, sides):
        """
        Initialize a CampusBoard instance.

        Args:
            date (datetime): The date of the workout.
            edge (str): The edge identifier (e.g. "20mm" or "sphere").
            steps_str (str): The string representing steps (e.g. "1-2-4").
            timeoff (str): Resting time.
            sides (str): Left or Right pull. "L", "R" or "LR".
        """
        self.date = date
        self.edge = edge
        self.steps_str = steps_str
        self.timeoff = timeoff
        self.sides = sides
        self.moves = self.compute_moves()
        self.spread = self.compute_spread()

    def compute_moves(self):
        # Count moves as the number of numbers separated by "-"
        return len(self.steps_str.split("-"))

    def compute_spread(self):
        # Compute spread as the sum of absolute differences between consecutive moves.
        try:
            numbers = [int(n) for n in self.steps_str.split("-")]
        except ValueError:
            return 0
        return sum(abs(numbers[i] - numbers[i - 1]) for i in range(1, len(numbers)))


def extract_edge_value(edge_str):
    """
    Extract the numeric part of an edge string (e.g., "20mm" -> 20).
    Returns None if no numeric value is found.
    """
    numeric_part = ''.join(filter(str.isdigit, edge_str))
    return float(numeric_part) if numeric_part else None

