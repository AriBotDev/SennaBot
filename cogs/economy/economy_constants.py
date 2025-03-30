"""
Constants shared across economy modules.
Provides centralized access to all economy-related configuration values.
"""

# Cooldown times (in seconds)
WORK_COOLDOWN = 60        # 1 minute
CRIME_COOLDOWN = 75       # 1.25 minutes
ROB_COOLDOWN = 300        # 5 minutes
ROULETTE_COOLDOWN = 420   # 7 minutes
PRISON_COOLDOWN = 3600    # 1 hour
ESCAPE_COOLDOWN = 120     # 2 minutes
BREAKOUT_COOLDOWN = 300   # 5 minutes
ROB_VICTIM_COOLDOWN = 600 # 10 minutes protection for victims

# Payout ranges
WORK_PAYOUT_MIN = 4
WORK_PAYOUT_MAX = 12
CRIME_PAYOUT_MIN = 15
CRIME_PAYOUT_MAX = 35
ROB_MIN_AMOUNT = 15       # Minimum amount stolen on success

# Penalty values
FINE_MIN = 5
FINE_MAX = 30
DEATH_SAVINGS_PENALTY = 0.10  # 10% of savings penalty on death

# Critical success settings
CRITICAL_SUCCESS_CHANCE = 2    # 2% chance of critical success
CRITICAL_MULTIPLIER_MIN = 3    # 3x minimum multiplier
CRITICAL_MULTIPLIER_MAX = 5    # 5x maximum multiplier

# Failure rates (percentages)
FAIL_RATES = {
    "crime": 51,  # 51% chance of crime failure
    "rob": 55     # 55% chance of rob failure
}

# Outcome chances on failure (percentages)
OUTCOME_CHANCES = {
    "death": 15,   # 15% chance for death on failure
    "injury": 65,  # 65% chance for injury on failure
    "prison": 20   # 20% chance for prison on failure (remainder)
}

# Balance challenge settings
SENNABOT_BALANCE = 15000      # Threshold to trigger balance challenge
CHALLENGE_BET = 1000          # Bet amount for the challenge
SENNABOT_ID = 1349242668672090253  # SennaBot's user ID
CHALLENGE_TIMEOUT = 120       # Timeout for challenge interactions