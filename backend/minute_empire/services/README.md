# Minute Empire Combat System

## Overview

The Minute Empire combat system is designed to create dynamic, strategic battles between troops in the game world. This document outlines the mathematical model and combat mechanics that determine the outcome of battles.

## Troop Statistics

Each troop type has unique attack and defense values:

| Troop Type    | Attack Value | Defense Value |
|---------------|--------------|---------------|
| Militia       | 1.0          | 1.0           |
| Archer        | 1.0          | 0.5           |
| Light Cavalry | 1.0          | 1.0           |
| Pikeman       | 1.0          | 2.0           |

These base statistics are scaled by the quantity of each troop.

## Combat Calculation Process

### 1. Raw Strength Calculation

Combat begins with calculating the raw attacking and defending power of all involved units:

```
raw_attacker_atk = attacker_quantity * attacker_type_atk_value
raw_attacker_def = attacker_quantity * attacker_type_def_value

raw_defender_atk = sum(defender_quantity * defender_type_atk_value for all defenders)
raw_defender_def = sum(defender_quantity * defender_type_def_value for all defenders)
```

### 2. Situational Modifiers

Various combat situations can modify the raw values:

- **Defender's Home Advantage**: Troops defending a village receive a 30% bonus (applied as a 30% reduction to the attacker's attack and defense values) if the village is owned by the same user who owns the defender's home village. This means troops get a defensive bonus in any friendly village, not just their own home village.

```
if defending_a_friendly_village:
    final_attacker_atk = raw_attacker_atk * 0.7
    final_attacker_def = raw_attacker_def * 0.7
```

### 3. Snowball Ratio Calculation

To simulate the escalating advantage of having superior forces, a snowball ratio is calculated:

```
attacker_snowball_ratio = (final_attacker_atk / final_defender_def)^1.5
defender_snowball_ratio = (final_defender_atk / final_attacker_def)^1.5
```

The exponent of 1.5 amplifies the effect of strength differences, creating a more decisive outcome when one side has a significant advantage.

### 4. Loss Calculation

Troop losses are determined by the opponent's snowball ratio, capped between 0 and 1:

```
attacker_loss = median(0, defender_snowball_ratio, 1)
defender_loss = median(0, attacker_snowball_ratio, 1)
```

### 5. Special Rules for Ranged Units

- **Archers**: Can attack without moving and don't receive return damage when attacking from range.
- **Pikemen**: Can attack their current location or from range. When attacking from range, they don't receive return damage, but when attacking their current location, they do take damage.

### 6. Threshold Application

Two thresholds determine the final outcome:

- **All Dead Threshold (0.85)**: If a side's loss ratio exceeds 0.85, all troops on that side are eliminated.
- **All Alive Threshold (0.15)**: If a side's loss ratio is below 0.15, no troops on that side are lost.

### 7. Outcome Resolution

After losses are applied:

- **Movement Action**: If the attacker survives and defeats all defenders, it can move to the target location.
- **Attack Action**: The attacker never moves to the target location, regardless of the outcome.
- If the attacker loses all troops or fails to defeat all defenders during a movement, the action fails and surviving attackers remain in their original position.

## Movement and Combat Interaction

Combat can be triggered in two ways:

1. **Direct Attack**: A troop uses an attack action against a target location. The troop attacks but stays in its original position regardless of the outcome.
2. **Movement Encounter**: A troop attempts to move to a location and encounters enemy troops. If it defeats all enemies, it can move to the target location.

Each troop type has unique movement and attack patterns:

- **Militia**: Can move and attack adjacent cells (including diagonals).
- **Archer**: Can move to adjacent orthogonal cells and attack from a distance without taking damage.
- **Light Cavalry**: Moves in L-shaped patterns (like a chess knight) and must be in the same location to attack.
- **Pikeman**: Has versatile movement options and can attack both its current location and distant targets without taking damage.

## Implementation Details

The combat system is implemented in the `_process_combat` method of the `TroopActionService` class. This method handles all combat calculations and updates troop quantities and status in the database.

The troop statistics are defined as constants in the `Troop` domain class for easy maintenance and reuse.

Detailed logs of combat results are printed during execution for debugging and analysis purposes. 