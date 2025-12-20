# Game Mechanics (Draft)

## Encounter Turn Structure
- Teams act as a group on their turn.
- Player team always goes first unless an enemy has a "haste" ability that overrides it.
- Turns alternate between player team and enemy team.
- The player selects action type (Attack or Convert) and then selects a target square on the enemy grid.
- Every allied creature that can perform that action on that square does so.
- Convert uses the same targeting rules as attacks; the effect differs.
- Move is a separate action type that moves one allied unit one square; it consumes the entire team's turn.
- Move uses orthogonal adjacency only and allows swapping with another allied unit.
- Moving and swapping are the same action; the first selected unit is the designated moving unit (with future significance).
- Encounter size scaling: deeper biomes field more units per battle.
- In deeper biomes, enemy units can randomly start at higher experience tiers.
- Enemy units start placed randomly on the enemy 3x3 grid.
- Moving a 2x2 unit shifts it one square at a time and displaces two squares; displaced units move into the two squares that open up.

## Attack Types
- Melee: attacks the closest enemy horizontally.
- Ranged: has a distance range (for example, "2-3") and can attack any square whose column is 2 or 3 columns away (but not 1 column away).
- Magic: attacks every square in the "mirror" column on the enemy side (front to front, middle to middle, back to back).

## Stats and Damage
- Units have max HP plus three defense stats: defense (vs melee), dodge (vs ranged), and resistance (vs magic).
- Units also have a conversion efficacy that scales how effective their attacks are when used to convert.
- Attacks have a damage value assigned to the attack itself (not derived from unit stats).
- Damage is reduced directly by the relevant defense stat for the attack type.
- Final damage = max(1, attack_damage - relevant_defense).
- Legacy stats (STR/DEX/CON) are removed in favor of these three defenses.

## Hero Attributes
- INT reduces the number of battles needed for a unit to reach its experience levels.
- Tiered formulas (base 0):
- INT: every +5 INT reduces each tier's battle requirement by 1 (min 1).
- WIS: every +4 WIS adds +1 to defense, dodge, and resistance for all allied units.
- CHA: every +4 CHA increases conversion efficacy by +10% (multiplies base efficacy).

## Hero Battle Stats
- Heroes have melee, ranged, and magic attack values, plus matching defenses (defense, dodge, resistance).
- Base hero attacks and defenses are 3 across the board; heroes can use all three attack types.
- INT increases the hero's ranged attack and ranged defense (dodge).
- WIS increases the hero's melee attack and melee defense (defense).
- CHA increases the hero's magic attack and magic defense (resistance).
- BATTLE scales the effect of INT/WIS/CHA on the hero's attack and defense values. With low BATTLE, the hero remains physically weak even with high stats.
- Heroes always have ranged attack range 2-3.
- Battle scaling formula (no clamping):
- `battle_scale = 0.25 + 0.05 * BATTLE`
- `effective_stat = floor(stat * battle_scale)`
- `attack_bonus = floor(effective_stat / 2)`
- `defense_bonus = floor(effective_stat / 3)`
- `final_attack = base_attack + attack_bonus`
- `final_defense = base_defense + defense_bonus`

## Experience Levels
- Creatures have 3 experience levels based on how many battles they finish.
- Battle counts are tracked per unit; thresholds and benefits are also per-unit.
- Hero INT reduces the required battle counts for allies.
- Tier battle requirement increases by 1 every two tiers (1-based): `requirement = base_requirement + floor((tier - 1) / 2)`.
- Total battles to reach a tier is the sum of requirements for all tiers up to that tier.
- Heroes do not gain stats per battle; they gain 3 stat points each floor.

## Conversion
- Conversion uses the same targeting rules as attacks.
- Each unit's conversion efficacy (0-100) scales its attack damage when converting.
- Conversion is defended against by the target's highest defense stat (max of defense, dodge, resistance).
- Conversion progress required to recruit a target equals the target's max HP.
- Effective conversion efficacy = `conversion_efficacy * (1 + 0.10 * floor(CHA / 4))`.
- If the target is below 50% HP, conversion efficacy is boosted by 50% before defenses are applied.
- Conversion points per hit: `max(0, floor(attack_damage * (effective_conversion_efficacy / 100)) - highest_defense)`.
- Conversion progress resets after battle.
- Fully converted units are removed from battle and added to pending recruits (not immediate party members).

## Enemy AI
- Enemies always choose Attack.
- Target square is the one that yields the highest total damage from all valid attackers.
- Ties can be broken arbitrarily (not defined yet).

## Resolution
- All participating units resolve their action for the turn.
- Death is checked and applied after the full action resolution.

## Encounter End Conditions
- Encounters end when all enemies are gone.
- Defeating the Dragon King wins the game.

## HP Persistence
- HP does not heal automatically between battles or floors.

## Team Arrangement and Placement
- 2x2 units are placed by choosing any 2x2 footprint (four possible placements); there is no player-facing anchor.
- Placement UI should outline the entire unit footprint (not just a single square).
- Placing a 2x2 unit from recruits can displace up to four units; displaced units go to the recruits list.
- To move a 2x2 unit on the grid: select any square it occupies, then choose an orthogonally adjacent target square.
- The 2x2 unit shifts by the delta between source and target (one square up/down/left/right).
- Displaced units from the two newly occupied squares move to the two squares that were vacated.

## Special Abilities
- Piercing: melee attacks hit all squares on the horizontal (same row) of the target.
- Splash: ranged attacks target normally; any hit square also hits its orthogonally adjacent squares.
- Evasion: percent chance to avoid all damage whenever the unit takes damage in an attack.
- Weakening: attacks apply weakened; weakened lasts until the damaged unit attacks and reduces that unit's attack strength by 3.
- Weakened stacks; each time a weakened unit attacks, it removes only one stack.
- Defanging: like weakened, but reduces melee attack strength by 6.
- Blinding: like defanging, but reduces ranged attack strength by 6.
- Silencing: like defanging, but reduces magic attack strength by 6.
- Lifelink: whenever this creature deals damage, it gains that amount of HP.
- Healing X: when this creature makes a magic attack, it also heals allies on the same column as itself (including self) for X.
- Shield Wall: this unit gains 50% * x extra dodge and defense for each unit of the same unit type on your team.
- Pack Hunter: this unit gains 50% * x extra melee and ranged damage for each unit of the same unit type on your team.
- Guardian: this unit adds 50% of its defense and dodge to orthogonally adjacent allies.
- Protector: this unit adds 50% of its resistance to orthogonally adjacent allies.
- "Unit type" means exact name matching.
- Flying: immune to damage from melee attacks.
- Haste: if an enemy unit has haste, the enemy team acts first instead of the default player-first rule. Player haste does not override enemy haste.

## Targeting and Grid
- Encounter grid is 3x3 per side.
- Columns are front, middle, and back relative to each team.
- Targeting empty squares is allowed.

## Targeting Definitions (Precise)
- For distance math, treat the two 3-column grids as adjacent: player columns map to global columns 0-2 (back to front), enemy columns map to global columns 3-5 (front to back).
- Column distance is the absolute difference between global columns.
- Ranged min-max (for example, 2-3) is inclusive; a target square is valid if its column distance is within the range.
- Melee "closest horizontally" means the nearest enemy in the attacker's row by column distance; if the chosen target square is not that enemy, the attacker does not act.
- Magic "mirror column" means front hits front, middle hits middle, back hits back (relative to each team).

## Large Units (2x2)
- A 2x2 unit occupies four squares and counts as being in multiple rows and columns.
- A 2x2 unit blocks all four squares it occupies.
- In the grid representation, a 2x2 unit fills all four occupied slots (same unit reference), not a single anchor slot.
- A 2x2 unit is represented by four characters (top-left, top-right, bottom-left, bottom-right).
- On a 3x3 board, only one 2x2 unit can exist at a time.
- For ranged and magic attacks, treat the 2x2 unit as if it is in its front-top-most square.
- Melee attacks from a 2x2 unit still hit one enemy at a time; it can target either row it occupies.
- If a 2x2 unit would be affected by an attack that hits 2+ of its occupied squares, it only takes damage/convert/debuff once.
- Adjacency-based effects treat a 2x2 unit as occupying all four squares it covers.
- If a unit grows to 2x2 at an experience tier, it expands into empty nearby tiles if possible; otherwise it moves to pending recruits for re-placement.
