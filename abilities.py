"""Special ability implementations based on GAME_MECHANICS.md."""

import random
from typing import Optional, Union

from game_data import Attack, Creature, Encounter, Player


# === PASSIVE ABILITIES ===


def check_evasion(creature: Union[Creature, Player]) -> bool:
    """Check if the creature evades damage due to Evasion ability.

    Evasion X%: percent chance to avoid all damage.
    Returns True if damage is evaded.
    """
    abilities = getattr(creature, "abilities", []) or []
    for ability in abilities:
        if ability.startswith("Evasion"):
            # Parse "Evasion 50%" -> 50
            parts = ability.split()
            if len(parts) >= 2:
                try:
                    percent = int(parts[1].rstrip("%"))
                    return random.randint(1, 100) <= percent
                except ValueError:
                    pass
    return False


def check_flying(creature: Union[Creature, Player]) -> bool:
    """Check if creature has Flying ability (immune to melee damage)."""
    abilities = getattr(creature, "abilities", []) or []
    return "Flying" in abilities


def check_haste(creature: Union[Creature, Player]) -> bool:
    """Check if creature has Haste ability."""
    abilities = getattr(creature, "abilities", []) or []
    return "Haste" in abilities


def process_lifelink(attacker: Union[Creature, Player], damage_dealt: int) -> None:
    """Process Lifelink: heal attacker for damage dealt.

    Lifelink: whenever this creature deals damage, it gains that amount of HP.
    """
    abilities = getattr(attacker, "abilities", []) or []
    if "Lifelink" in abilities:
        attacker.current_health = min(
            attacker.max_health, attacker.current_health + damage_dealt
        )


# === ATTACK DEBUFFS ===


def apply_debuffs(attack: Attack, target: Union[Creature, Player]) -> list[str]:
    """Apply debuffs from attack abilities to the target.

    Returns list of debuff names applied.

    Debuffs:
    - Weakening: -3 attack strength, removed when unit attacks
    - Defanging: -6 melee attack strength
    - Blinding: -6 ranged attack strength
    - Silencing: -6 magic attack strength

    All debuffs stack and one stack is removed each time the unit attacks.
    """
    if not hasattr(target, "debuffs") or target.debuffs is None:
        target.debuffs = {}

    applied = []
    attack_abilities = attack.abilities or []

    if "Weakening" in attack_abilities:
        target.debuffs["weakened"] = target.debuffs.get("weakened", 0) + 1
        applied.append("weakened")
    if "Defanging" in attack_abilities:
        target.debuffs["defanged"] = target.debuffs.get("defanged", 0) + 1
        applied.append("defanged")
    if "Blinding" in attack_abilities:
        target.debuffs["blinded"] = target.debuffs.get("blinded", 0) + 1
        applied.append("blinded")
    if "Silencing" in attack_abilities:
        target.debuffs["silenced"] = target.debuffs.get("silenced", 0) + 1
        applied.append("silenced")

    return applied


def clear_debuff_stacks(unit: Union[Creature, Player]) -> list[str]:
    """Remove one stack of each debuff after the unit attacks.

    Returns list of debuff names that were reduced.
    """
    cleared = []
    if not hasattr(unit, "debuffs") or unit.debuffs is None:
        return cleared

    for debuff in list(unit.debuffs.keys()):
        unit.debuffs[debuff] -= 1
        cleared.append(debuff)
        if unit.debuffs[debuff] <= 0:
            del unit.debuffs[debuff]

    return cleared


# === ATTACK MODIFIERS ===


def has_piercing(attack: Attack) -> bool:
    """Check if attack has Piercing ability.

    Piercing: melee attacks hit all squares on the horizontal (same row) of the target.
    """
    return "Piercing" in (attack.abilities or [])


def has_splash(attack: Attack) -> bool:
    """Check if attack has Splash ability.

    Splash: ranged attacks target normally; any hit square also hits its
    orthogonally adjacent squares.
    """
    return "Splash" in (attack.abilities or [])


# === SUPPORT ABILITIES ===


def get_healing_amount(unit: Union[Creature, Player]) -> int:
    """Get the healing amount from Healing X ability.

    Healing X: when this creature makes a magic attack, it also heals allies
    on the same column as itself (including self) for X.
    """
    abilities = getattr(unit, "abilities", []) or []
    for ability in abilities:
        if ability.startswith("Healing"):
            parts = ability.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
    return 0


def process_healing_ability(
    attacker: Union[Creature, Player],
    encounter: Encounter,
    is_player_side: bool,
) -> list[tuple[Union[Creature, Player], int]]:
    """Process Healing ability after a magic attack.

    Returns list of (healed_unit, amount) tuples.
    """
    heal_amount = get_healing_amount(attacker)
    if heal_amount == 0:
        return []

    team = encounter.player_team if is_player_side else encounter.enemy_team
    healed = []

    # Find attacker's column
    attacker_col = None
    for idx, unit in enumerate(team or []):
        if unit is attacker:
            attacker_col = idx % 3
            break

    if attacker_col is None:
        return []

    # Heal all allies in same column (including self)
    for row in range(3):
        idx = row * 3 + attacker_col
        ally = team[idx] if team else None
        if ally is not None:
            old_health = ally.current_health
            ally.current_health = min(ally.max_health, ally.current_health + heal_amount)
            actual_heal = ally.current_health - old_health
            if actual_heal > 0:
                healed.append((ally, actual_heal))

    return healed


def calculate_guardian_bonus(
    unit: Union[Creature, Player],
    encounter: Encounter,
    is_player_side: bool,
) -> dict[str, int]:
    """Calculate defense bonuses from adjacent Guardian units.

    Guardian: this unit adds 50% of its defense and dodge to orthogonally adjacent allies.

    Returns dict with 'defense' and 'dodge' bonus values.
    """
    bonuses = {"defense": 0, "dodge": 0}
    team = encounter.player_team if is_player_side else encounter.enemy_team

    # Find this unit's index
    unit_idx = None
    for idx, u in enumerate(team or []):
        if u is unit:
            unit_idx = idx
            break

    if unit_idx is None:
        return bonuses

    row, col = unit_idx // 3, unit_idx % 3
    adjacent_indices = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            adjacent_indices.append(nr * 3 + nc)

    # Check each adjacent unit for Guardian ability
    for adj_idx in adjacent_indices:
        adj_unit = team[adj_idx] if team else None
        if adj_unit is not None:
            adj_abilities = getattr(adj_unit, "abilities", []) or []
            if "Guardian" in adj_abilities:
                bonuses["defense"] += int(getattr(adj_unit, "defense", 0) * 0.5)
                bonuses["dodge"] += int(getattr(adj_unit, "dodge", 0) * 0.5)

    return bonuses


def calculate_protector_bonus(
    unit: Union[Creature, Player],
    encounter: Encounter,
    is_player_side: bool,
) -> int:
    """Calculate resistance bonus from adjacent Protector units.

    Protector: this unit adds 50% of its resistance to orthogonally adjacent allies.

    Returns resistance bonus value.
    """
    bonus = 0
    team = encounter.player_team if is_player_side else encounter.enemy_team

    # Find this unit's index
    unit_idx = None
    for idx, u in enumerate(team or []):
        if u is unit:
            unit_idx = idx
            break

    if unit_idx is None:
        return bonus

    row, col = unit_idx // 3, unit_idx % 3
    adjacent_indices = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            adjacent_indices.append(nr * 3 + nc)

    # Check each adjacent unit for Protector ability
    for adj_idx in adjacent_indices:
        adj_unit = team[adj_idx] if team else None
        if adj_unit is not None:
            adj_abilities = getattr(adj_unit, "abilities", []) or []
            if "Protector" in adj_abilities:
                bonus += int(getattr(adj_unit, "resistance", 0) * 0.5)

    return bonus


def calculate_shield_wall_bonus(
    unit: Union[Creature, Player],
    encounter: Encounter,
    is_player_side: bool,
) -> dict[str, int]:
    """Calculate bonuses from Shield Wall ability.

    Shield Wall: this unit gains 50% * x extra dodge and defense for each unit
    of the same unit type on your team.

    Returns dict with 'defense' and 'dodge' bonus values.
    """
    bonuses = {"defense": 0, "dodge": 0}

    unit_abilities = getattr(unit, "abilities", []) or []
    if "Shield Wall" not in unit_abilities:
        return bonuses

    team = encounter.player_team if is_player_side else encounter.enemy_team
    unit_name = getattr(unit, "name", None)

    if unit_name is None:
        return bonuses

    # Count same-type units (excluding self)
    same_type_count = sum(
        1 for u in (team or []) if u is not None and u is not unit and getattr(u, "name", None) == unit_name
    )

    if same_type_count > 0:
        base_defense = getattr(unit, "defense", 0)
        base_dodge = getattr(unit, "dodge", 0)
        bonuses["defense"] = int(base_defense * 0.5 * same_type_count)
        bonuses["dodge"] = int(base_dodge * 0.5 * same_type_count)

    return bonuses


def calculate_pack_hunter_bonus(
    unit: Union[Creature, Player],
    encounter: Encounter,
    is_player_side: bool,
) -> dict[str, int]:
    """Calculate damage bonuses from Pack Hunter ability.

    Pack Hunter: this unit gains 50% * x extra melee and ranged damage for each
    unit of the same unit type on your team.

    Returns dict with 'melee' and 'ranged' bonus damage values.
    """
    bonuses = {"melee": 0, "ranged": 0}

    unit_abilities = getattr(unit, "abilities", []) or []
    if "Pack Hunter" not in unit_abilities:
        return bonuses

    team = encounter.player_team if is_player_side else encounter.enemy_team
    unit_name = getattr(unit, "name", None)

    if unit_name is None:
        return bonuses

    # Count same-type units (excluding self)
    same_type_count = sum(
        1 for u in (team or []) if u is not None and u is not unit and getattr(u, "name", None) == unit_name
    )

    if same_type_count > 0:
        # Calculate bonus based on base attack damage
        unit_attacks = getattr(unit, "attacks", []) or []
        for attack in unit_attacks:
            if attack.attack_type == "melee":
                bonuses["melee"] = int(attack.damage * 0.5 * same_type_count)
            elif attack.attack_type == "ranged":
                bonuses["ranged"] = int(attack.damage * 0.5 * same_type_count)

    return bonuses


# === COMBINED STAT CALCULATIONS ===


def get_effective_defense(
    unit: Union[Creature, Player],
    defense_type: str,
    encounter: Encounter,
    is_player_side: bool,
    player: Optional[Player] = None,
) -> int:
    """Get unit's total effective defense including all bonuses.

    Includes:
    - Base defense
    - WIS bonus from hero (for allies)
    - Guardian bonus (defense, dodge)
    - Protector bonus (resistance)
    - Shield Wall bonus (defense, dodge)
    """
    # Base defense
    if isinstance(unit, Player):
        if defense_type == "defense":
            base = unit.base_defense
        elif defense_type == "dodge":
            base = unit.base_dodge
        else:
            base = unit.base_resistance
    else:
        base = getattr(unit, defense_type, 0)

    # WIS bonus from hero (only for non-player allies)
    wis_bonus = 0
    if player is not None and unit is not player:
        wis_bonus = player.wisdom // 4

    # Guardian/Protector bonuses
    guardian_bonus = calculate_guardian_bonus(unit, encounter, is_player_side)
    protector_bonus = calculate_protector_bonus(unit, encounter, is_player_side)

    # Shield Wall bonus
    shield_wall_bonus = calculate_shield_wall_bonus(unit, encounter, is_player_side)

    if defense_type == "defense":
        return base + wis_bonus + guardian_bonus["defense"] + shield_wall_bonus["defense"]
    elif defense_type == "dodge":
        return base + wis_bonus + guardian_bonus["dodge"] + shield_wall_bonus["dodge"]
    else:  # resistance
        return base + wis_bonus + protector_bonus


def get_effective_attack_damage(
    unit: Union[Creature, Player],
    attack: Attack,
    encounter: Encounter,
    is_player_side: bool,
) -> int:
    """Get unit's effective attack damage including all bonuses.

    Includes:
    - Base attack damage
    - Pack Hunter bonus
    - (Debuff reductions are applied separately in damage calculation)
    """
    base_damage = attack.damage

    # Pack Hunter bonus
    pack_hunter_bonus = calculate_pack_hunter_bonus(unit, encounter, is_player_side)

    if attack.attack_type == "melee":
        return base_damage + pack_hunter_bonus["melee"]
    elif attack.attack_type == "ranged":
        return base_damage + pack_hunter_bonus["ranged"]
    else:
        return base_damage  # Magic doesn't benefit from Pack Hunter
