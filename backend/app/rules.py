"""LoreForge - D&D 5e Deterministic Rules Engine
   Pure functional game mechanics: dice math, ability modifiers, and HP constraints."""

import random
from typing import Tuple, List

def calculate_modifier(score: int) -> int:
    """Computes standard D&D 5e ability modifier using floor division.
       Formula: floor((score - 10) / 2)"""
    return (score - 10) // 2

def roll_dice(sides: int = 20) -> int:
    """Rolls a fair dice with the specified number of sides (default is a d20)."""
    return random.randint(1, sides)

def roll_d20(advantage: bool = False, disadvantage: bool = False) -> Tuple[int, List[int], str]:
    """Rolls a d20 handling standard, advantage, and disadvantage mechanics.
       Returns: (final_result, individual_rolls, roll_type)"""
    if advantage and disadvantage:
        # If both are true, they cancel out; roll normally.
        advantage = disadvantage = False
    if advantage:
        d1, d2 = roll_dice(20), roll_dice(20)
        return max(d1, d2), [d1, d2], "advantage"
    if disadvantage:
        d1, d2 = roll_dice(20), roll_dice(20)
        return min(d1, d2), [d1, d2], "disadvantage"
        single = roll_dice(20)
    return single, [single], "normal"

def apply_hp_change(current_hp: int, max_hp: int, amount: int, is_healing: bool = False) -> int:
    """Calculates updated HP ensuring bounds between 0 and max_hp."""
    if is_healing:
        # Healing the character, cannot exceed max_hp.
        return min(max_hp, current_hp + amount)

    # Applying damage
    return max(0, current_hp - amount)

