"""Core combat system implementation based on GAME_MECHANICS.md."""

import math
from typing import Optional, Union

from game_data import Attack, Creature, Encounter, Player


# Grid layout constants
# Player grid: columns 0-2 (back=0, middle=1, front=2)
# Enemy grid: columns 3-5 (front=3, middle=4, back=5)
# Global column distance used for range calculations


def get_global_column(is_player_side: bool, local_col: int) -> int:
    """Convert local column (0-2) to global column (0-5).

    Player side: back=0, middle=1, front=2 -> global 0, 1, 2
    Enemy side: front=0, middle=1, back=2 -> global 3, 4, 5
    """
    if is_player_side:
        return local_col  # Player columns map directly to 0-2
    else:
        return 3 + local_col  # Enemy columns map to 3-5


def calculate_column_distance(attacker_global_col: int, target_global_col: int) -> int:
    """Calculate column distance for range checks."""
    return abs(attacker_global_col - target_global_col)


def grid_index_to_coords(index: int) -> tuple[int, int]:
    """Convert 1D index (0-8) to (col, row) coordinates."""
    return index % 3, index // 3


def coords_to_grid_index(col: int, row: int) -> int:
    """Convert (col, row) to 1D index (0-8)."""
    return row * 3 + col


# === TARGETING FUNCTIONS ===


def get_melee_target(
    encounter: Encounter,
    attacker_col: int,
    attacker_row: int,
    attacker_is_player: bool,
    target_col: int,
    target_row: int,
) -> Optional[Creature]:
    """Get the valid melee target for an attacker.

    Melee attacks hit the closest enemy horizontally in the same row.
    Units cannot melee attack if an ally is in front of them (blocking).
    Returns the target if the specified target position matches the closest enemy.
    Returns None if the attacker cannot hit that target.
    """
    ally_team = encounter.player_team if attacker_is_player else encounter.enemy_team
    enemy_team = encounter.enemy_team if attacker_is_player else encounter.player_team

    # Only consider targets in the same row as the attacker
    if target_row != attacker_row:
        return None

    # Check if an ally is blocking (in front of the attacker)
    # For player: front is column 2, so check columns > attacker_col
    # For enemy: front is column 0, so check columns < attacker_col
    for col in range(3):
        if attacker_is_player:
            # Player front is column 2; allies in columns > attacker block
            if col > attacker_col:
                idx = attacker_row * 3 + col
                if ally_team[idx] is not None:
                    return None  # Blocked by ally
        else:
            # Enemy front is column 0; allies in columns < attacker block
            if col < attacker_col:
                idx = attacker_row * 3 + col
                if ally_team[idx] is not None:
                    return None  # Blocked by ally

    # Find the closest enemy in the attacker's row
    closest_enemy = None
    closest_col = None

    for col in range(3):
        idx = attacker_row * 3 + col
        enemy = enemy_team[idx]
        if enemy is not None:
            if attacker_is_player:
                # For player, lower column = front = closer to enemy
                # Enemy front column (0 for them) is closest to player
                if closest_enemy is None or col < closest_col:
                    closest_enemy = enemy
                    closest_col = col
            else:
                # For enemy attacking player, higher column = front = closer
                if closest_enemy is None or col > closest_col:
                    closest_enemy = enemy
                    closest_col = col

    # Check if selected target matches closest
    if closest_enemy is not None and target_col == closest_col:
        return closest_enemy

    return None


def get_ranged_targets(
    encounter: Encounter,
    attacker_col: int,
    attacker_row: int,
    attacker_is_player: bool,
    target_col: int,
    target_row: int,
    range_min: int,
    range_max: int,
    has_splash: bool = False,
) -> list[tuple[Union[Creature, Player], int, int]]:
    """Get valid ranged targets.

    Ranged attacks hit targets within range (column distance).
    If Splash, also hits orthogonally adjacent squares.
    Returns list of (creature, col, row) tuples.
    """
    enemy_team = encounter.enemy_team if attacker_is_player else encounter.player_team

    attacker_global = get_global_column(attacker_is_player, attacker_col)
    target_global = get_global_column(not attacker_is_player, target_col)

    distance = calculate_column_distance(attacker_global, target_global)

    if not (range_min <= distance <= range_max):
        return []  # Out of range

    targets = []
    squares_to_check = [(target_col, target_row)]

    if has_splash:
        # Add orthogonally adjacent squares
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            adj_col = target_col + dx
            adj_row = target_row + dy
            if 0 <= adj_col < 3 and 0 <= adj_row < 3:
                squares_to_check.append((adj_col, adj_row))

    # Track 2x2 units to avoid double-hitting
    processed_units = set()

    for col, row in squares_to_check:
        idx = row * 3 + col
        creature = enemy_team[idx]
        if creature is not None and id(creature) not in processed_units:
            targets.append((creature, col, row))
            processed_units.add(id(creature))

    return targets


def get_magic_targets(
    encounter: Encounter,
    attacker_col: int,
    attacker_is_player: bool,
) -> list[tuple[Union[Creature, Player], int, int]]:
    """Get valid magic targets.

    Magic attacks hit all enemies in the mirror column.
    Front hits front, middle hits middle, back hits back (relative to each team).

    Column mapping for magic (mirror):
    - Player front (col 2) -> Enemy front (col 0)
    - Player middle (col 1) -> Enemy middle (col 1)
    - Player back (col 0) -> Enemy back (col 2)
    """
    enemy_team = encounter.enemy_team if attacker_is_player else encounter.player_team

    # Mirror column: player col 0 (back) hits enemy col 2 (back), etc.
    mirror_col = 2 - attacker_col

    targets = []
    processed_units = set()

    for row in range(3):
        idx = row * 3 + mirror_col
        creature = enemy_team[idx]
        if creature is not None and id(creature) not in processed_units:
            targets.append((creature, mirror_col, row))
            processed_units.add(id(creature))

    return targets


def can_attack_target(
    encounter: Encounter,
    attacker: Union[Creature, Player],
    attacker_idx: int,
    target_col: int,
    target_row: int,
    attack: Attack,
    attacker_is_player: bool,
) -> bool:
    """Check if an attacker can hit a target with the given attack."""
    attacker_col, attacker_row = grid_index_to_coords(attacker_idx)

    if attack.attack_type == "melee":
        target = get_melee_target(
            encounter, attacker_col, attacker_row, attacker_is_player, target_col, target_row
        )
        return target is not None
    elif attack.attack_type == "ranged":
        range_min = attack.range_min or 1
        range_max = attack.range_max or 3
        targets = get_ranged_targets(
            encounter,
            attacker_col,
            attacker_row,
            attacker_is_player,
            target_col,
            target_row,
            range_min,
            range_max,
        )
        return len(targets) > 0
    elif attack.attack_type == "magic":
        targets = get_magic_targets(encounter, attacker_col, attacker_is_player)
        # Magic hits if any target exists in the mirror column
        return len(targets) > 0

    return False


# === DAMAGE CALCULATION ===


def calculate_damage(
    attack: Attack,
    attacker: Union[Creature, Player],
    defender: Union[Creature, Player],
    attacker_debuffs: Optional[dict[str, int]] = None,
    defender_has_flying: bool = False,
) -> int:
    """Calculate final damage: max(1, attack_damage - relevant_defense).

    Applies debuff reductions to attack damage.
    Returns 0 if defender has Flying and attack is melee.
    """
    if attacker_debuffs is None:
        attacker_debuffs = {}

    base_damage = attack.damage

    # Flying immunity to melee
    if attack.attack_type == "melee" and defender_has_flying:
        return 0

    # Apply debuffs to attack damage
    debuff_reduction = 0
    if attack.attack_type == "melee":
        debuff_reduction = attacker_debuffs.get("defanged", 0) * 6
        debuff_reduction += attacker_debuffs.get("weakened", 0) * 3
    elif attack.attack_type == "ranged":
        debuff_reduction = attacker_debuffs.get("blinded", 0) * 6
        debuff_reduction += attacker_debuffs.get("weakened", 0) * 3
    elif attack.attack_type == "magic":
        debuff_reduction = attacker_debuffs.get("silenced", 0) * 6
        debuff_reduction += attacker_debuffs.get("weakened", 0) * 3

    effective_damage = max(0, base_damage - debuff_reduction)

    # Get relevant defense
    if attack.attack_type == "melee":
        defense = getattr(defender, "defense", 0)
        if isinstance(defender, Player):
            defense = defender.base_defense
    elif attack.attack_type == "ranged":
        defense = getattr(defender, "dodge", 0)
        if isinstance(defender, Player):
            defense = defender.base_dodge
    else:  # magic
        defense = getattr(defender, "resistance", 0)
        if isinstance(defender, Player):
            defense = defender.base_resistance

    return max(1, effective_damage - defense) if effective_damage > 0 else 0


def calculate_conversion(
    attack: Attack,
    attacker: Union[Creature, Player],
    defender: Creature,
    effective_efficacy: int,
) -> int:
    """Calculate conversion points.

    Formula: max(0, floor(attack_damage * (efficacy/100)) - highest_defense)
    50% bonus if target below 50% HP (applied before defense).
    """
    base_conversion = math.floor(attack.damage * (effective_efficacy / 100))

    # 50% bonus if target below 50% HP
    if defender.current_health < defender.max_health / 2:
        base_conversion = math.floor(base_conversion * 1.5)

    # Defended by highest defense stat
    highest_defense = max(defender.defense, defender.dodge, defender.resistance)

    return max(0, base_conversion - highest_defense)


# === HERO STAT CALCULATIONS ===


def calculate_hero_combat_stats(player: Player) -> dict:
    """Calculate hero's effective combat stats based on attributes.

    battle_scale = 0.25 + 0.05 * BATTLE
    effective_stat = floor(stat * battle_scale)
    attack_bonus = floor(effective_stat / 2)
    defense_bonus = floor(effective_stat / 3)

    INT affects ranged attack/dodge
    WIS affects melee attack/defense
    CHA affects magic attack/resistance
    """
    battle_scale = 0.25 + 0.05 * player.battle

    # INT affects ranged
    int_effective = math.floor(player.intelligence * battle_scale)
    ranged_attack_bonus = math.floor(int_effective / 2)
    dodge_bonus = math.floor(int_effective / 3)

    # WIS affects melee
    wis_effective = math.floor(player.wisdom * battle_scale)
    melee_attack_bonus = math.floor(wis_effective / 2)
    defense_bonus = math.floor(wis_effective / 3)

    # CHA affects magic
    cha_effective = math.floor(player.charisma * battle_scale)
    magic_attack_bonus = math.floor(cha_effective / 2)
    resistance_bonus = math.floor(cha_effective / 3)

    return {
        "melee_attack": player.base_melee_attack + melee_attack_bonus,
        "ranged_attack": player.base_ranged_attack + ranged_attack_bonus,
        "magic_attack": player.base_magic_attack + magic_attack_bonus,
        "defense": player.base_defense + defense_bonus,
        "dodge": player.base_dodge + dodge_bonus,
        "resistance": player.base_resistance + resistance_bonus,
    }


def calculate_ally_buffs(player: Player) -> dict:
    """Calculate buffs applied to allies from hero WIS.

    +1 defense/dodge/resistance per +4 WIS.
    """
    wis_bonus = player.wisdom // 4
    return {
        "defense": wis_bonus,
        "dodge": wis_bonus,
        "resistance": wis_bonus,
    }


def calculate_effective_efficacy(player: Player, base_efficacy: int) -> int:
    """Calculate effective conversion efficacy with CHA bonus.

    +10% per +4 CHA (multiplicative).
    """
    cha_bonus_multiplier = 1 + 0.10 * (player.charisma // 4)
    return math.floor(base_efficacy * cha_bonus_multiplier)


def get_hero_attacks(player: Player) -> list[Attack]:
    """Get the hero's available attacks with calculated damage values."""
    hero_stats = calculate_hero_combat_stats(player)

    return [
        Attack(attack_type="melee", damage=hero_stats["melee_attack"]),
        Attack(attack_type="ranged", damage=hero_stats["ranged_attack"], range_min=2, range_max=3),
        Attack(attack_type="magic", damage=hero_stats["magic_attack"]),
    ]


# === UTILITY FUNCTIONS ===


def get_creature_effective_defense(
    creature: Creature,
    player: Player,
    defense_type: str,
) -> int:
    """Get creature's effective defense including ally buffs from hero WIS."""
    base_defense = getattr(creature, defense_type, 0)
    ally_buffs = calculate_ally_buffs(player)
    return base_defense + ally_buffs.get(defense_type, 0)


def has_ability(unit: Union[Creature, Player], ability_name: str) -> bool:
    """Check if a unit has a specific ability (exact or prefix match)."""
    abilities = getattr(unit, "abilities", []) or []
    for ability in abilities:
        if ability == ability_name or ability.startswith(ability_name + " "):
            return True
    return False


def get_ability_value(unit: Union[Creature, Player], ability_prefix: str) -> Optional[int]:
    """Get the numeric value from an ability like 'Evasion 50%' or 'Healing 3'."""
    abilities = getattr(unit, "abilities", []) or []
    for ability in abilities:
        if ability.startswith(ability_prefix):
            # Parse "Evasion 50%" or "Healing 3"
            parts = ability.split()
            if len(parts) >= 2:
                value_str = parts[1].rstrip("%")
                try:
                    return int(value_str)
                except ValueError:
                    pass
    return None


def check_haste(encounter: Encounter) -> bool:
    """Check if any enemy has Haste ability - they go first."""
    for unit in encounter.enemy_team or []:
        if unit and has_ability(unit, "Haste"):
            return True
    return False
