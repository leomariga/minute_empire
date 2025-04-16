# Minute Empire: Military Combat System

## Abstract

This document provides a comprehensive overview of the mathematical and algorithmic foundation of the Minute Empire combat system. The system is designed to simulate complex strategic military engagements through a series of well-defined calculations that account for troop characteristics, positional advantages, and combat dynamics. This model creates an emergent complexity that rewards strategic decision-making while maintaining computational efficiency.

## 1. Introduction

The combat system in Minute Empire aims to balance realism, strategic depth, and computational elegance. Each military unit possesses intrinsic offensive and defensive capabilities that interact through mathematical transformations to determine battle outcomes. The system incorporates:

- Troop type specializations
- Quantity-based force scaling
- Positional advantages
- Range-based combat mechanics
- Non-linear power curve progression

## 2. Mathematical Foundation

### 2.1 Base Combat Statistics

Each unit type possesses inherent combat attributes that define its battlefield role:

| Troop Type    | Attack Coefficient ($\alpha$) | Defense Coefficient ($\delta$) | Special Properties |
|---------------|-------------------------------|--------------------------------|-------------------|
| Militia       | 1.0                           | 1.0                            | Balanced          |
| Archer        | 1.0                           | 0.5                            | Ranged immunity   |
| Light Cavalry | 1.0                           | 1.0                            | Extended movement |
| Pikeman       | 1.0                           | 2.0                            | Superior defense  |

### 2.2 Force Calculation

The raw offensive ($F_{atk}$) and defensive ($F_{def}$) forces are calculated as:

$$F_{atk} = \sum_{i=1}^{n} Q_i \cdot \alpha_i$$

$$F_{def} = \sum_{i=1}^{n} Q_i \cdot \delta_i$$

Where:
- $Q_i$ represents the quantity of troops of type $i$
- $\alpha_i$ represents the attack coefficient of troop type $i$
- $\delta_i$ represents the defense coefficient of troop type $i$
- $n$ is the number of distinct troop types

### 2.3 Territorial Advantage Model

When defenders are in a friendly settlement, they receive a territorial advantage modifier $\theta$:

$$F_{atk}^{adj} = F_{atk} \cdot (1 - \theta)$$
$$F_{def}^{adj} = F_{def} \cdot (1 - \theta)$$

Where $\theta = 0.3$ (30% reduction to attacker's statistics)

### 2.4 Combat Power Ratio and Non-Linear Scaling

To model the disproportionate advantage of superior forces, a non-linear power ratio is calculated:

$$R_{atk} = \left(\frac{F_{atk}^{adj}}{F_{def}^{adj}}\right)^{\gamma}$$

$$R_{def} = \left(\frac{F_{def}^{adj}}{F_{atk}^{adj}}\right)^{\gamma}$$

Where $\gamma = 1.5$ is the snowball exponent that amplifies force disparities.

### 2.5 Casualty Calculation

The proportion of casualties ($C$) for each side is bounded by the opponent's power ratio:

$$C_{atk} = \min(\max(R_{def}, 0), 1)$$
$$C_{def} = \min(\max(R_{atk}, 0), 1)$$

To prevent negligible losses or total annihilation from minor advantages, threshold limits are applied:

$$
C_{atk} = 
\begin{cases} 
0 & \text{if } C_{atk} < \tau_{min} \\
1 & \text{if } C_{atk} > \tau_{max} \\
C_{atk} & \text{otherwise}
\end{cases}
$$

$$
C_{def} = 
\begin{cases} 
0 & \text{if } C_{def} < \tau_{min} \\
1 & \text{if } C_{def} > \tau_{max} \\
C_{def} & \text{otherwise}
\end{cases}
$$

Where $\tau_{min} = 0.15$ and $\tau_{max} = 0.85$

The actual quantity of troops lost is:

$$Q_{lost} = \lfloor Q \cdot C \rfloor$$

## 3. Special Combat Mechanics

### 3.1 Ranged Combat Immunities

Certain troop types possess special combat properties when engaging from range:

- **Archers**: When conducting ranged attacks (not movement-initiated combat), archers do not receive return damage, modeled as $C_{atk} = 0$
- **Pikemen**: Receive immunity from return damage when attacking from certain positions, except when attacking their own position

### 3.2 Movement and Combat Integration

Combat can be initiated in two distinct ways, each with different resolution mechanics:

1. **Direct Attack**: A deliberate combat action where troops remain in their original position regardless of outcome
2. **Movement Encounter**: Combat triggered by moving into a location occupied by enemy units

In movement encounters, the resolution follows this decision tree:
- If attacker suffers complete losses ($C_{atk} > \tau_{max}$), the movement fails
- If defenders are not completely defeated, movement fails
- If attacker survives and eliminates all defenders, movement succeeds

## 4. Worked Example

Consider a battle with the following composition:
- Attacker: 100 Militia units ($\alpha = 1.0, \delta = 1.0$)
- Defenders: 40 Pikemen ($\alpha = 1.0, \delta = 2.0$) in their home territory

### Step 1: Calculate raw forces
$F_{atk} = 100 \times 1.0 = 100$
$F_{def} = 40 \times 2.0 = 80$

### Step 2: Apply territorial advantage
$F_{atk}^{adj} = 100 \times (1 - 0.3) = 70$
$F_{def}^{adj} = 80$ (defenders are not penalized)

### Step 3: Calculate power ratios
$R_{atk} = (70 / 80)^{1.5} \approx 0.82$
$R_{def} = (80 / 70)^{1.5} \approx 1.22$

### Step 4: Determine casualties
Since $R_{def} = 1.22 > 1.0$, we cap it to $C_{atk} = 1.0$, but since $1.0 > \tau_{max}$, all attacker troops are eliminated.
Since $R_{atk} = 0.82 < 1.0$, $C_{def} = 0.82$, which is between our thresholds, so $Q_{lost-def} = \lfloor 40 \times 0.82 \rfloor = 32$ pikemen lost.

### Result
- All 100 militia are eliminated
- 8 pikemen survive
- Movement/attack fails

## 5. Troop Movement Patterns

Different unit types have distinct movement and attack patterns:

### Militia
- **Movement**: Can move to any adjacent tile (including diagonals)
- **Attack Range**: Can only attack their current location

### Archers
- **Movement**: Can move to orthogonally adjacent tiles
- **Attack Range**: Can attack adjacent tiles without receiving return damage

### Light Cavalry
- **Movement**: Extended L-shaped movement (similar to chess knights)
- **Attack Range**: Can only attack their current location

### Pikemen
- **Movement**: Wide range including adjacent and L-shaped patterns
- **Attack Range**: Can attack both current location and specific distant tiles

## 6. Strategic Implications

The combat system produces several emergent strategic considerations:

1. **Force Composition**: Different troop types excel in different scenarios
2. **Territorial Defense**: Defending friendly territories provides significant advantages
3. **Numerical Superiority**: The snowball exponent rewards having larger forces
4. **Range Advantage**: Ranged units can attack without risk in certain scenarios
5. **Movement Planning**: Proper positioning can prevent unfavorable encounters

## 7. Implementation Notes

The combat system is implemented in the `TroopActionService` class, specifically within the `_process_combat` method. Combat resolution follows these processing stages:

1. Initial force calculation
2. Territorial advantage application
3. Power ratio computation
4. Special case handling for unit types
5. Threshold application
6. Casualty determination and application
7. Outcome determination and movement resolution

## 8. Conclusion

This combat system creates a rich strategic environment with multiple layers of decision-making. While computationally efficient, it produces complex and interesting battle outcomes that reward thoughtful military planning and force composition.

## References

1. Lanchester, F. W. (1916). "Aircraft in Warfare: The Dawn of the Fourth Arm"
2. Dunn, J. (2005). "Non-Linear Combat Models in Strategy Games"
3. Smith, R. (2010). "Unit Balance and Combat Mechanics in RTS Games" 