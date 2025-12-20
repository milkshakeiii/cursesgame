# Game Entities (Draft)

This file lists placeholder creature placements and a unit data template. All stats are TBD.

## Unit Data Template
- name (string, exact unit type name)
- size (1x1 | 2x2)
- glyph (single character, 1x1 units) or glyphs (list of 4 characters: TL, TR, BL, BR for 2x2)
- color (RGB tuple, applies to all glyphs)
- max_hp (int)
- defense (int, vs melee)
- dodge (int, vs ranged)
- resistance (int, vs magic)
- conversion_efficacy (int 0-100)
- attacks (list)
  - type (melee | ranged | magic)
  - damage (int)
  - range (string "min-max", ranged only)
  - attack_abilities (list, optional; e.g., Piercing, Splash)
- abilities (list, optional; e.g., Evasion 20%, Lifelink, Healing 5)
- experience (per-unit progression data)
  - base_requirement (int, base battles for tier 1)
  - tier_bonuses (list, per-tier bonuses)
- notes (freeform, optional)

## Forest
### Terrain: grass
- Wolf
  - size: 1x1
  - glyph: w
  - color: (80, 90, 80)
  - max_hp: 10
  - defense: 2
  - dodge: 1
  - resistance: 2
  - conversion_efficacy: 75
  - attacks:
    - type: melee
      damage: 4
  - abilities: none
  - experience:
    - base_requirement: 5
    - tier_bonuses:
      - tier 1 (5 battles): Pack Hunter
      - tier 2 (10 battles): +2 defense/dodge/resistance, +4 melee damage, +8 max_hp
  - notes: dark green-grey coloration

### Terrain: trees
- Giant Spider
  - size: 1x1
  - glyph: s
  - color: (120, 120, 120)
  - max_hp: 15
  - defense: 1
  - dodge: 3
  - resistance: 2
  - conversion_efficacy: 25
  - attacks:
    - type: ranged
      damage: 4
      range: "1-2"
      attack_abilities: [Weakening]
  - abilities: none
  - experience:
    - base_requirement: 10
    - tier_bonuses:
      - tier 1 (10 battles): becomes 2x2, max_hp +15, defense/dodge/resistance +2/+2/+3, conversion_efficacy -15, +6 ranged damage
  - notes: when large, use glyphs [s, s, s, s]

### Terrain: bushes
- Goblin Pikeman
  - size: 1x1
  - glyph: p
  - color: (80, 120, 60)
  - max_hp: 12
  - defense: 3
  - dodge: 1
  - resistance: 1
  - conversion_efficacy: 50
  - attacks:
    - type: melee
      damage: 5
      attack_abilities: [Piercing]
  - abilities: none
  - experience:
    - base_requirement: 6
    - tier_bonuses:
      - tier 1 (6 battles): +1 defense, +2 melee damage
      - tier 2 (12 battles): Shield Wall
  - notes: spear fighter; uses piercing melee

### Terrain: hill
- Centaur Shaman
  - size: 1x1
  - glyph: C
  - color: (140, 90, 60)
  - max_hp: 15
  - defense: 2
  - dodge: 2
  - resistance: 3
  - conversion_efficacy: 40
  - attacks:
    - type: melee
      damage: 4
    - type: magic
      damage: 7
  - abilities: none
  - experience:
    - base_requirement: 8
    - tier_bonuses:
      - tier 1 (8 battles): +1 defense/dodge/resistance, +1 melee damage, +1 magic damage
  - notes: strong magic, solid melee

## Plains
### Terrain: short_grass
- Eagle
  - size: 1x1
  - glyph: E
  - color: (200, 200, 180)
  - max_hp: 8
  - defense: 1
  - dodge: 3
  - resistance: 1
  - conversion_efficacy: 45
  - attacks:
    - type: melee
      damage: 6
  - abilities: [Haste, Flying]
  - experience:
    - base_requirement: 7
    - tier_bonuses:
      - tier 1 (7 battles): gain ranged attack (2-3) damage 6, Evasion 50%
  - notes: fast striker; fragile

### Terrain: tall_grass
- Lion
  - size: 1x1
  - glyph: L
  - color: (200, 170, 80)
  - max_hp: 12
  - defense: 3
  - dodge: 1
  - resistance: 2
  - conversion_efficacy: 70
  - attacks:
    - type: melee
      damage: 5
  - abilities: none
  - experience:
    - base_requirement: 5
    - tier_bonuses:
      - tier 1 (5 battles): Protector
      - tier 2 (10 battles): +2 defense/dodge/resistance, +4 melee damage, +8 max_hp
      - tier 3 (15 battles): Guardian
  - notes: similar to wolf; trades Pack Hunter for Protector and adds Guardian later
- Scorpion
  - size: 1x1
  - glyph: S
  - color: (140, 110, 60)
  - max_hp: 11
  - defense: 2
  - dodge: 2
  - resistance: 1
  - conversion_efficacy: 20
  - attacks:
    - type: ranged
      damage: 4
      range: "1-2"
      attack_abilities: [Blinding]
  - abilities: none
  - experience:
    - base_requirement: 9
    - tier_bonuses:
      - tier 1 (9 battles): gain Silencing on ranged attack
  - notes: low conversion efficacy

## Snowy Mountain
### Terrain: snow
- Yeti
  - size: 2x2
  - glyphs: [Y, Y, Y, Y]
  - color: (220, 230, 240)
  - max_hp: 28
  - defense: 3
  - dodge: 1
  - resistance: 5
  - conversion_efficacy: 35
  - attacks:
    - type: melee
      damage: 6
    - type: magic
      damage: 7
  - abilities: none
  - experience: none
  - notes: heavy 2x2 bruiser; high resistance

### Terrain: rocky
- Dwarf
  - size: 1x1
  - glyph: D
  - color: (160, 140, 110)
  - max_hp: 14
  - defense: 3
  - dodge: 1
  - resistance: 2
  - conversion_efficacy: 80
  - attacks:
    - type: melee
      damage: 5
    - type: ranged
      damage: 4
      range: "1-2"
      attack_abilities: [Splash]
  - abilities: none
  - experience:
    - base_requirement: 6
    - tier_bonuses:
      - tier 1 (6 battles): Shield Wall
      - tier 2 (12 battles): +1 defense/dodge/resistance, +2 melee damage, +2 ranged damage, +4 max_hp
  - notes: sturdy; good conversion efficacy

### Terrain: trees
- Frost Owl
  - size: 1x1
  - glyph: O
  - color: (180, 210, 235)
  - max_hp: 9
  - defense: 1
  - dodge: 2
  - resistance: 3
  - conversion_efficacy: 55
  - attacks:
    - type: magic
      damage: 5
      attack_abilities: [Silencing]
  - abilities: [Healing 3]
  - experience:
    - base_requirement: 7
    - tier_bonuses:
      - tier 1 (7 battles): +1 magic damage, Healing +1
  - notes: support caster with silence

## Underground
### Terrain: dirt
- Skeleton
  - size: 1x1
  - glyph: K
  - color: (200, 200, 200)
  - max_hp: 11
  - defense: 1
  - dodge: 5
  - resistance: 0
  - conversion_efficacy: 30
  - attacks:
    - type: melee
      damage: 6
  - abilities: none
  - experience: none
  - notes: strong melee, fragile to magic

### Terrain: moss
- Slime
  - size: 1x1
  - glyph: S
  - color: (60, 150, 80)
  - max_hp: 16
  - defense: 2
  - dodge: 1
  - resistance: 3
  - conversion_efficacy: 25
  - attacks:
    - type: ranged
      damage: 4
      range: "1-2"
      attack_abilities: [Defanging]
  - abilities: none
  - experience:
    - base_requirement: 10
    - tier_bonuses:
      - tier 1 (10 battles): becomes 2x2, max_hp +16, defense/dodge/resistance +2/+1/+3, conversion_efficacy -10, +6 ranged damage
  - notes: similar to giant spider growth; use glyphs [S, S, S, S] when large

### Terrain: mushrooms
- Safe terrain (no encounters yet)

### Terrain: stalactite
- Bat
  - size: 1x1
  - glyph: b
  - color: (90, 90, 110)
  - max_hp: 7
  - defense: 0
  - dodge: 3
  - resistance: 1
  - conversion_efficacy: 40
  - attacks:
    - type: melee
      damage: 4
  - abilities: [Lifelink]
  - experience:
    - base_requirement: 6
    - tier_bonuses:
      - tier 1 (6 battles): +1 melee damage, +2 max_hp
      - tier 2 (12 battles): +1 dodge, +1 melee damage, +2 max_hp
  - notes: fragile lifestealer

## Bosses
- Dragon King
  - size: 2x2
  - glyphs: [D, D, D, D]
  - color: (255, 80, 80)
  - max_hp: 50
  - defense: 6
  - dodge: 6
  - resistance: 10
  - conversion_efficacy: 0
  - attacks:
    - type: melee
      damage: 7
      attack_abilities: [Piercing]
    - type: ranged
      damage: 6
      range: "1-3"
      attack_abilities: [Splash]
    - type: magic
      damage: 7
      attack_abilities: [Weakening]
  - abilities: none
  - experience: none
  - notes: moves 1 square in a random direction after attacking each turn
