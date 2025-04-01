# src/crimpy/pullup.py

class Pullup:
    def __init__(self, date, edge, set_data):
        """
        Initialize a Pullup instance.

        Args:
            date (datetime): ...of the execution.
            edge (str): typically "bar".
            set_data (dict): A dictionary containing the pullup set data.
                Expected keys include "repetitions", and either "weight_kg" or "weight_lb".
        """
        self.date = date
        self.edge = edge
        self.repetitions = int(set_data.get("repetitions", 0))
        # Convert weight to kg if necessary.
        if "weight_kg" in set_data:
            self.weight_kg = float(set_data["weight_kg"])
        elif "weight_lb" in set_data:
            self.weight_kg = float(set_data["weight_lb"]) * 0.453592
        else:
            self.weight_kg = None  # In case no weight is provided.
        self.timeoff = set_data.get("timeoff")
