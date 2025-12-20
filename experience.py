"""Experience and tier progression system based on GAME_MECHANICS.md."""

from typing import Optional

from game_data import Creature, Encounter, Player


def get_max_tier(creature: Creature) -> int:
    """Get the maximum tier defined for a creature.

    Returns 0 if no tier_bonuses are defined.
    """
    if not creature.tier_bonuses:
        return 0

    max_tier = 0
    for bonus in creature.tier_bonuses:
        tier = bonus.get("tier", 0)
        if tier > max_tier:
            max_tier = tier
    return max_tier


def get_base_battles_for_tier(creature: Creature, tier: int) -> Optional[int]:
    """Get the base battles required to reach a specific tier (without INT reduction).

    Returns None if the tier is not defined in tier_bonuses.
    """
    if not creature.tier_bonuses:
        return None

    for bonus in creature.tier_bonuses:
        if bonus.get("tier") == tier:
            return bonus.get("battles")

    return None


def get_battles_for_tier(creature: Creature, tier: int, hero_int: int = 0) -> Optional[int]:
    """Get the total battles required to reach a specific tier.

    Returns None if the tier is not defined in tier_bonuses.
    Uses the explicit 'battles' field from tier_bonuses, reduced by INT.
    Formula: max(1, battles - floor(INT / 5))
    """
    base_battles = get_base_battles_for_tier(creature, tier)
    if base_battles is None:
        return None

    int_reduction = hero_int // 5
    return max(1, base_battles - int_reduction)


def check_tier_upgrade(creature: Creature, hero_int: int) -> bool:
    """Check if creature should upgrade to next tier.

    Returns True if upgrade happened.
    Uses explicit battle thresholds from tier_bonuses, reduced by INT.
    """
    # No progression if base_requirement is 0 (like Yeti, Skeleton)
    if creature.base_requirement == 0:
        return False

    next_tier = creature.tier + 1

    # Check if next tier is defined
    required_battles = get_battles_for_tier(creature, next_tier, hero_int)
    if required_battles is None:
        # No more tiers defined - can't upgrade
        return False

    if creature.battles_completed >= required_battles:
        creature.apply_tier_bonus(next_tier)
        creature.tier = next_tier
        return True

    return False


def get_tier_bonus_description(creature: Creature, tier: int) -> list[str]:
    """Get human-readable descriptions of bonuses for a tier.

    Returns list of bonus descriptions.
    """
    descriptions = []
    if not creature.tier_bonuses:
        return descriptions

    for bonus in creature.tier_bonuses:
        if bonus.get("tier") != tier:
            continue

        if "max_health" in bonus:
            descriptions.append(f"+{bonus['max_health']} Max HP")
        if "defense" in bonus:
            descriptions.append(f"+{bonus['defense']} Defense")
        if "dodge" in bonus:
            descriptions.append(f"+{bonus['dodge']} Dodge")
        if "resistance" in bonus:
            descriptions.append(f"+{bonus['resistance']} Resistance")
        if "conversion_efficacy" in bonus:
            val = bonus['conversion_efficacy']
            sign = "+" if val >= 0 else ""
            descriptions.append(f"{sign}{val}% Efficacy")
        if "melee_damage" in bonus:
            descriptions.append(f"+{bonus['melee_damage']} Melee Damage")
        if "ranged_damage" in bonus:
            descriptions.append(f"+{bonus['ranged_damage']} Ranged Damage")
        if "magic_damage" in bonus:
            descriptions.append(f"+{bonus['magic_damage']} Magic Damage")
        if "new_attack" in bonus:
            atk = bonus["new_attack"]
            descriptions.append(f"New Attack: {atk['type']} ({atk['damage']})")
        if "attack_abilities" in bonus:
            for atk_type, abilities in bonus["attack_abilities"].items():
                for ability in abilities:
                    descriptions.append(f"{atk_type.title()} gains {ability}")
        if "abilities" in bonus:
            for ability in bonus["abilities"]:
                descriptions.append(f"Ability: {ability}")
        if "healing_bonus" in bonus:
            descriptions.append(f"+{bonus['healing_bonus']} Healing")
        if "size" in bonus and bonus["size"] == "2x2":
            descriptions.append("Grows to 2x2!")

    return descriptions


def end_battle_experience(
    encounter: Encounter,
    player: Player,
) -> dict:
    """Award experience at battle end.

    Returns dict with:
        - 'participants': list of dicts with creature info and exp gain
        - 'tier_ups': list of dicts with creature, new tier, and bonus descriptions
        - 'grew_to_2x2': list of creatures that grew to 2x2 (need re-placement)
    """
    participants = []
    tier_ups = []
    grew_to_2x2 = []

    # Track unique creatures (for 2x2 units that appear multiple times)
    processed_ids = set()

    for unit in encounter.player_team or []:
        if unit is None or isinstance(unit, Player):
            continue

        if not isinstance(unit, Creature):
            continue

        # Skip if already processed (2x2 units)
        if id(unit) in processed_ids:
            continue
        processed_ids.add(id(unit))

        # Record battles before increment
        old_battles = unit.battles_completed
        old_tier = unit.tier
        old_size = unit.size

        # Increment battle count
        unit.battles_completed += 1

        # Record participant
        participants.append({
            "creature": unit,
            "name": unit.name,
            "battles_before": old_battles,
            "battles_after": unit.battles_completed,
        })

        # Check for tier upgrade
        if check_tier_upgrade(unit, player.intelligence):
            new_tier = unit.tier
            bonuses = get_tier_bonus_description(unit, new_tier)
            tier_ups.append({
                "creature": unit,
                "name": unit.name,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "bonuses": bonuses,
            })

            # Check if grew to 2x2
            if unit.size == "2x2" and old_size == "1x1":
                grew_to_2x2.append(unit)

    return {
        "participants": participants,
        "tier_ups": tier_ups,
        "grew_to_2x2": grew_to_2x2,
    }


def handle_growth_to_2x2(
    creature: Creature,
    encounter: Encounter,
    pending_recruits: list[Creature],
) -> bool:
    """Handle a creature growing from 1x1 to 2x2 during battle.

    If there's space in the grid, expand into adjacent empty tiles.
    Otherwise, move to pending_recruits for re-placement.

    Returns True if creature was moved to pending_recruits.
    """
    from gameplay import is_2x2_placement_valid, place_2x2_unit, grid_index_to_coords

    # Find creature's current position
    current_idx = None
    for idx, unit in enumerate(encounter.player_team or []):
        if unit is creature:
            current_idx = idx
            break

    if current_idx is None:
        return False

    col, row = grid_index_to_coords(current_idx)

    # Try to find a valid 2x2 placement starting from current position
    # Check all four possible 2x2 placements that include current position
    possible_starts = [
        (col, row),           # current is TL
        (col - 1, row),       # current is TR
        (col, row - 1),       # current is BL
        (col - 1, row - 1),   # current is BR
    ]

    for start_col, start_row in possible_starts:
        if start_col < 0 or start_row < 0:
            continue
        if is_2x2_placement_valid(encounter.player_team, start_col, start_row):
            # Remove from current position first
            encounter.player_team[current_idx] = None
            # Place as 2x2
            displaced = place_2x2_unit(encounter.player_team, creature, start_col, start_row)
            # Displaced units go to recruits
            pending_recruits.extend(displaced)
            return False

    # No valid placement - remove and add to pending recruits
    encounter.player_team[current_idx] = None
    pending_recruits.append(creature)
    return True


def award_floor_stats(player: Player) -> None:
    """Award +3 stat points to the hero when completing a floor."""
    player.stat_points += 3


def get_tier_progress(creature: Creature, hero_int: int) -> dict:
    """Get information about creature's tier progression.

    Returns dict with current tier, battles completed, and battles needed for next tier.
    INT reduces thresholds by 1 per 5 INT.
    """
    if creature.base_requirement == 0:
        return {
            "tier": creature.tier,
            "battles": creature.battles_completed,
            "next_tier_battles": None,
            "progress_percent": 100,
        }

    next_tier = creature.tier + 1
    battles_needed = get_battles_for_tier(creature, next_tier, hero_int)

    # If no more tiers defined, show as maxed out
    if battles_needed is None:
        return {
            "tier": creature.tier,
            "battles": creature.battles_completed,
            "next_tier_battles": None,
            "progress_percent": 100,
        }

    current_tier_battles = get_battles_for_tier(creature, creature.tier, hero_int) if creature.tier > 0 else 0
    current_tier_battles = current_tier_battles or 0
    battles_for_tier = battles_needed - current_tier_battles

    battles_into_tier = creature.battles_completed - current_tier_battles
    progress = min(100, int((battles_into_tier / battles_for_tier) * 100)) if battles_for_tier > 0 else 0

    return {
        "tier": creature.tier,
        "battles": creature.battles_completed,
        "next_tier_battles": battles_needed,
        "progress_percent": progress,
    }
