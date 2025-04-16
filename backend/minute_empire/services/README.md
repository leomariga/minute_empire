# Minute Empire: Combat System Guide

## What is This Document?

This guide explains how battles work in Minute Empire. We use some math to make battles fair and interesting, but don't worry - we'll explain everything in simple terms too! This system creates battles that reward good strategy while being fun to play.

## How Combat Works in Minute Empire

The combat system in Minute Empire is designed to be both strategic and easy to understand. When your troops meet enemy troops, a battle happens based on:

- What types of troops you have (militia, archers, etc.)
- How many troops you have (more is usually better!)
- Where the battle happens (defending your territory gives advantages)
- Special abilities of different troop types

## The Building Blocks: Troop Types and Stats

Each type of troop has its own strengths and weaknesses:

| Troop Type    | Attack Power ($\alpha$) | Defense Power ($\delta$) | What Makes Them Special |
|---------------|-------------------------|--------------------------|-------------------------|
| Militia       | 1.0                     | 1.0                      | Balanced, good all-around troops |
| Archer        | 1.0                     | 0.5                      | Can attack from distance without taking damage |
| Light Cavalry | 1.0                     | 1.0                      | Can move farther than other units |
| Pikeman       | 1.0                     | 2.0                      | Extra strong on defense |

## How Battles Are Calculated

### Step 1: Adding Up Your Army's Strength

First, we calculate the total attack and defense power of each side. It's pretty simple:

**Total Attack Strength** = Number of troops × Their attack power

For math folks, we write this as:

$$F_{atk} = \sum_{i=1}^{n} Q_i \cdot \alpha_i$$

Which just means "add up (attack power × number of troops) for each troop type you have."

The same goes for defense:

$$F_{def} = \sum_{i=1}^{n} Q_i \cdot \delta_i$$

**Example:** 
- If you have 50 militia (attack = 1.0) and 20 archers (attack = 1.0)
- Your total attack strength would be: 50×1.0 + 20×1.0 = 70

### Step 2: Home Field Advantage

Troops defending their own territory get a bonus! Actually, it works as a 30% penalty to attackers:

$$\text{Adjusted Attacker Strength} = \text{Original Strength} \times 0.7$$

Or in math notation:

$$F_{atk}^{adj} = F_{atk} \times (1 - 0.3)$$

**Example:**
- If you attack someone in their own village with 100 attack power
- Your adjusted attack would be: 100 × 0.7 = 70

### Step 3: The Snowball Effect

In real battles, having even a small advantage can lead to a big victory. We model this with what we call a "snowball factor" (with a power of 1.5):

$$R_{atk} = \left(\frac{\text{Attacker Strength}}{\text{Defender Strength}}\right)^{1.5}$$

$$R_{def} = \left(\frac{\text{Defender Strength}}{\text{Attacker Strength}}\right)^{1.5}$$

**Example:**
- If your attack strength is 80 and enemy defense is 40
- Your attack ratio would be: (80/40)^1.5 = 2^1.5 ≈ 2.83
- This is much higher than just 2, showing how advantages get amplified!

### Step 4: Calculating Casualties

The percentage of troops lost is based on the enemy's power ratio:

$$\text{Attacker Losses} = \text{Defender Power Ratio}$$
$$\text{Defender Losses} = \text{Attacker Power Ratio}$$

But we have some special rules:
- If the calculated loss is less than 15%, no troops die (they just retreat)
- If the calculated loss is more than 85%, all troops die

In math notation:

$$
\text{Troops Lost} = 
\begin{cases} 
0\% & \text{if calculated losses } < 15\% \\
100\% & \text{if calculated losses } > 85\% \\
\text{calculated percentage} & \text{otherwise}
\end{cases}
$$

**Example:**
- If the attacker power ratio is 2.5 (capped at 1.0 or 100%)
- And there are 40 defending troops
- Then 40 × 1.0 = 40 troops would be lost (all of them)

## Special Combat Rules

### Ranged Attack Bonus

Some troops have special abilities:

- **Archers**: When they attack without moving, they don't take damage back
- **Pikemen**: They can attack from certain positions without taking damage

### Movement and Combat

Battles can happen in two ways:

1. **Direct Attack**: You specifically order troops to attack. They stay where they are regardless of outcome.
2. **Moving Into Enemies**: When you move troops and run into enemies, a battle happens.

If you're moving and:
- You lose all your troops: your move fails
- Enemies survive: your move fails
- You win completely: your move succeeds

## A Real Battle Example

Let's see a complete battle play out:

**The Setup:**
- Attacker: 100 Militia (attack=1.0, defense=1.0)
- Defender: 40 Pikemen (attack=1.0, defense=2.0) in their home territory

**Step 1: Calculate base strength**
- Attacker strength: 100 × 1.0 = 100
- Defender strength: 40 × 2.0 = 80

**Step 2: Apply home field advantage**
- Attacker adjusted strength: 100 × 0.7 = 70
- Defender strength stays at 80

**Step 3: Calculate power ratios**
- Attacker ratio: (70/80)^1.5 ≈ 0.82
- Defender ratio: (80/70)^1.5 ≈ 1.22

**Step 4: Calculate losses**
- Defender ratio is 1.22, which is above 1.0, so 100% of attackers are lost
- Attacker ratio is 0.82, so 82% of defenders are lost (40 × 0.82 = 32.8, rounded down to 32)

**The Result:**
- All 100 militia are eliminated
- 8 pikemen survive
- The attackers' move fails

## How Different Troops Move and Attack

### Militia
- **Movement**: Can move one space in any direction (including diagonals)
- **Attack**: Can only attack where they're standing

### Archers
- **Movement**: Can move one space (but not diagonally)
- **Attack**: Can shoot at adjacent spaces without taking damage

### Light Cavalry
- **Movement**: Can move in an L-shape like a chess knight
- **Attack**: Can only attack where they're standing

### Pikemen
- **Movement**: Can move one space or in an L-shape
- **Attack**: Can attack both their current location and some distant spaces

## Strategy Tips

The combat system means you should think about:

1. **Mixing Troop Types**: Different troops are good for different situations
2. **Defending Home Territory**: You get big advantages fighting in your own villages
3. **Numbers Matter**: Having more troops gives you an even bigger advantage than you might expect
4. **Using Ranged Units Wisely**: Archers and pikemen can attack without risk in certain situations
5. **Positioning**: Where you place your troops matters a lot!

## Technical Details

For those curious about the code, the combat system is built into the `TroopActionService` class in the `_process_combat` method. It follows these steps:

1. Calculate the strength of both sides
2. Apply any territory bonuses
3. Calculate the power ratios
4. Handle special abilities for different troop types
5. Apply the threshold rules
6. Calculate and apply losses
7. Determine if movement succeeds (if applicable)

## In Conclusion

This combat system creates fun, strategic battles that make sense but still have some surprises. Different troop types, positioning, and numbers all matter, giving you lots of strategic options!

## Further Reading

If you're interested in learning more about the math behind combat systems like this:

1. Lanchester, F. W. (1916). "Aircraft in Warfare: The Dawn of the Fourth Arm"
2. Dunn, J. (2005). "Non-Linear Combat Models in Strategy Games"
3. Smith, R. (2010). "Unit Balance and Combat Mechanics in RTS Games" 