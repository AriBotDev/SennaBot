"""
Constants shared across economy modules.
"""

# Prison constants
PRISON_COOLDOWN = 3600  # 1 hour
ESCAPE_COOLDOWN = 120   # 2 minutes
BREAKOUT_COOLDOWN = 300 # 5 minutes

# Failure rates
FAIL_RATES = {
    "crime": 51,
    "rob": 55
}

# Outcome chances
OUTCOME_CHANCES = {
    "death": 15,    # 15% chance for death on failure
    "injury": 65,   # 65% chance for injury on failure
    "prison": 20    # 20% chance for prison on failure
}

# Death penalty
DEATH_SAVINGS_PENALTY = 0.10  # 10% of savings