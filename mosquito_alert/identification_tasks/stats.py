import math
import numbers
from typing import List
from scipy.stats import entropy

def calculate_norm_entropy(probabilities: List[numbers.Number]) -> float:
    """Computes normalized entropy of the given probability distribution."""
    # Cast the probabilities list to a list of floats
    probabilities = [float(p) for p in probabilities]

    # If there's only one probability, there is no uncertainty (entropy = 0)
    # math.log2(1) = 0 -> would raise in the division (denominator)
    if len(probabilities) <= 1:
        return 0.0
    return entropy(probabilities, base=2) / math.log2(len(probabilities))