"""Experience and tier progression system based on GAME_MECHANICS.md."""

from typing import Optional

from game_data import Attack, Creature, Encounter, Player


def calculate_tier_requirement(base_requirement: int, tier: int, hero_int: int) -> int:
    """Calculate battles needed for a specific tier.

    Formula: base + floor((tier - 1) / 2) - floor(INT / 5)
    Minimum 1 battle required.

    tier_requirement increases by 1 every two tiers.
    INT reduces requirement by 1 per +5 INT.
    """
    tier_bonus = (tier - 1) // 2
    int_reduction = hero_int // 5
    return max(1, base_requirement + tier_bonus - int_reduction)


def calculate_total_battles_for_tier(creature: Creature, tier: int, hero_int: int) -> int:
    """Calculate total battles needed to reach a tier.

    Total is the sum of requirements for all tiers up to and including the target tier.
    """
    total = 0
    for t in range(1, tier + 1):
        total += calculate_tier_requirement(creature.base_requirement, t, hero_int)
    return total


def check_tier_upgrade(creature: Creature, hero_int: int) -> bool:
    """Check if creature should upgrade to next tier.

    Returns True if upgrade happened.
    """
    if creature.tier >= 3:
        return False  # Max tier

    # No progression if base_requirement is 0 (like Yeti, Skeleton)
    if creature.base_requirement == 0:
        return False

    next_tier = creature.tier + 1
    required_battles = calculate_total_battles_for_tier(creature, next_tier, hero_int)

    if creature.battles_completed >= required_battles:
        apply_tier_bonuses(creature, next_tier)
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


def apply_tier_bonuses(creature: Creature, tier: int) -> None:
    """Apply stat and ability bonuses for reaching a tier.

    Modifies the creature in-place.
    """
    if not creature.tier_bonuses:
        return

    for bonus in creature.tier_bonuses:
        if bonus.get("tier") != tier:
            continue

        # Stat bonuses
        if "max_health" in bonus:
            creature.max_health += bonus["max_health"]
            creature.current_health += bonus["max_health"]
        if "defense" in bonus:
            creature.defense += bonus["defense"]
        if "dodge" in bonus:
            creature.dodge += bonus["dodge"]
        if "resistance" in bonus:
            creature.resistance += bonus["resistance"]
        if "conversion_efficacy" in bonus:
            creature.conversion_efficacy += bonus["conversion_efficacy"]

        # Attack damage bonuses
        if "melee_damage" in bonus:
            for attack in creature.attacks or []:
                if attack.attack_type == "melee":
                    attack.damage += bonus["melee_damage"]
        if "ranged_damage" in bonus:
            for attack in creature.attacks or []:
                if attack.attack_type == "ranged":
                    attack.damage += bonus["ranged_damage"]
        if "magic_damage" in bonus:
            for attack in creature.attacks or []:
                if attack.attack_type == "magic":
                    attack.damage += bonus["magic_damage"]

        # New attack
        if "new_attack" in bonus:
            new_atk = bonus["new_attack"]
            range_str = new_atk.get("range", "")
            range_min, range_max = None, None
            if range_str and "-" in range_str:
                parts = range_str.split("-")
                range_min = int(parts[0])
                range_max = int(parts[1])

            attack = Attack(
                attack_type=new_atk["type"],
                damage=new_atk["damage"],
                range_min=range_min,
                range_max=range_max,
                abilities=new_atk.get("abilities", []),
            )
            if creature.attacks is None:
                creature.attacks = []
            creature.attacks.append(attack)

        # Attack ability additions
        if "attack_abilities" in bonus:
            for attack_type, abilities in bonus["attack_abilities"].items():
                for attack in creature.attacks or []:
                    if attack.attack_type == attack_type:
                        if attack.abilities is None:
                            attack.abilities = []
                        attack.abilities.extend(abilities)

        # Ability unlocks
        if "abilities" in bonus:
            if creature.abilities is None:
                creature.abilities = []
            for ability in bonus["abilities"]:
                if ability not in creature.abilities:
                    creature.abilities.append(ability)

        # Healing bonus (increases Healing X amount)
        if "healing_bonus" in bonus:
            if creature.abilities:
                for i, ability in enumerate(creature.abilities):
                    if ability.startswith("Healing"):
                        parts = ability.split()
                        if len(parts) >= 2:
                            try:
                                current_val = int(parts[1])
                                creature.abilities[i] = f"Healing {current_val + bonus['healing_bonus']}"
                            except ValueError:
                                pass

        # Size change (Spider, Slime grow to 2x2)
        if "size" in bonus and bonus["size"] == "2x2":
            creature.size = "2x2"
            if "glyphs" in bonus:
                creature.glyphs = bonus["glyphs"]


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
    """
    if creature.base_requirement == 0:
        return {
            "tier": creature.tier,
            "battles": creature.battles_completed,
            "next_tier_battles": None,
            "progress_percent": 100,
        }

    if creature.tier >= 3:
        return {
            "tier": creature.tier,
            "battles": creature.battles_completed,
            "next_tier_battles": None,
            "progress_percent": 100,
        }

    next_tier = creature.tier + 1
    battles_needed = calculate_total_battles_for_tier(creature, next_tier, hero_int)
    current_tier_battles = calculate_total_battles_for_tier(creature, creature.tier, hero_int) if creature.tier > 0 else 0
    battles_for_tier = battles_needed - current_tier_battles

    battles_into_tier = creature.battles_completed - current_tier_battles
    progress = min(100, int((battles_into_tier / battles_for_tier) * 100)) if battles_for_tier > 0 else 0

    return {
        "tier": creature.tier,
        "battles": creature.battles_completed,
        "next_tier_battles": battles_needed,
        "progress_percent": progress,
    }
