"""Enemy AI implementation based on GAME_MECHANICS.md."""

import random
from typing import Optional, Union

from game_data import Attack, Creature, Encounter, GameState, Player
from combat import (
    calculate_damage,
    get_melee_target,
    get_ranged_targets,
    get_magic_targets,
    grid_index_to_coords,
)
from abilities import (
    check_flying,
    get_effective_attack_damage,
    has_piercing,
    has_splash,
)


def calculate_potential_damage(
    encounter: Encounter,
    target_col: int,
    target_row: int,
) -> int:
    """Calculate total damage enemy team would deal to a target square.

    Each unit uses best attack. 2x2 units count once.
    """
    from gameplay import get_2x2_primary_position

    total_damage = 0
    processed_units = set()

    for idx, unit in enumerate(encounter.enemy_team or []):
        if unit is None:
            continue

        # Skip if already processed (2x2 units)
        if id(unit) in processed_units:
            continue
        processed_units.add(id(unit))

        # For 2x2 units, use primary position
        if getattr(unit, "size", "1x1") == "2x2":
            primary_pos = get_2x2_primary_position(encounter.enemy_team, unit)
            if primary_pos:
                attacker_col, attacker_row = primary_pos
            else:
                attacker_col, attacker_row = grid_index_to_coords(idx)
        else:
            attacker_col, attacker_row = grid_index_to_coords(idx)

        attacks = getattr(unit, "attacks", []) or []
        is_2x2 = getattr(unit, "size", "1x1") == "2x2"

        # Select best attack that can hit the target
        best_damage = 0
        for attack in attacks:
            # For 2x2 units with melee, try both rows they occupy
            rows_to_try = [attacker_row]
            if is_2x2 and attack.attack_type == "melee" and attacker_row < 2:
                rows_to_try.append(attacker_row + 1)

            for try_row in rows_to_try:
                targets = get_enemy_attack_targets(
                    encounter, attack, attacker_col, try_row, target_col, target_row
                )

                for target, _, _ in targets:
                    # Get effective damage
                    effective_damage = get_effective_attack_damage(
                        unit, attack, encounter, is_player_side=False
                    )
                    modified_attack = Attack(
                        attack_type=attack.attack_type,
                        damage=effective_damage,
                        range_min=attack.range_min,
                        range_max=attack.range_max,
                        abilities=attack.abilities,
                    )

                    # Calculate damage considering target's Flying
                    defender_has_flying = check_flying(target)
                    attacker_debuffs = getattr(unit, "debuffs", {}) or {}

                    damage = calculate_damage(
                        modified_attack, unit, target, attacker_debuffs, defender_has_flying
                    )
                    if damage > best_damage:
                        best_damage = damage

        total_damage += best_damage

    return total_damage


def get_enemy_attack_targets(
    encounter: Encounter,
    attack: Attack,
    attacker_col: int,
    attacker_row: int,
    target_col: int,
    target_row: int,
) -> list[tuple[Union[Creature, Player], int, int]]:
    """Get all valid targets for an enemy attack against player team."""
    targets = []

    if attack.attack_type == "melee":
        # Enemy attacks player side (attacker_is_player=False)
        target = get_melee_target(
            encounter, attacker_col, attacker_row, False, target_col, target_row
        )
        if target:
            if has_piercing(attack):
                # Piercing hits all units in the same row
                processed = set()
                for col in range(3):
                    idx = target_row * 3 + col
                    player_unit = encounter.player_team[idx] if encounter.player_team else None
                    if player_unit is not None and id(player_unit) not in processed:
                        targets.append((player_unit, col, target_row))
                        processed.add(id(player_unit))
            else:
                targets.append((target, target_col, target_row))

    elif attack.attack_type == "ranged":
        range_min = attack.range_min or 1
        range_max = attack.range_max or 3
        targets = get_ranged_targets(
            encounter,
            attacker_col,
            attacker_row,
            False,  # Enemy attacking
            target_col,
            target_row,
            range_min,
            range_max,
            has_splash(attack),
        )

    elif attack.attack_type == "magic":
        targets = get_magic_targets(encounter, attacker_col, False)

    return targets


def choose_enemy_target(encounter: Encounter) -> tuple[int, int]:
    """Choose the target square that yields highest total damage.

    Enemy AI always chooses Attack and targets optimally.
    Considers empty squares for Splash attacks.
    Returns (col, row) of target square.
    """
    best_target = (1, 1)  # Default to center
    best_damage = -1

    for row in range(3):
        for col in range(3):
            # Consider all squares (including empty for Splash)
            damage = calculate_potential_damage(encounter, col, row)

            if damage > best_damage:
                best_damage = damage
                best_target = (col, row)

    return best_target


def execute_enemy_turn(gamestate: GameState) -> list[dict]:
    """Execute the enemy team's turn.

    Enemies always attack (no convert).
    Dragon King moves randomly after attacking.

    Returns list of action results for animation/logging.
    """
    from gameplay import resolve_team_attack, move_2x2_unit, add_combat_log

    encounter = gamestate.active_encounter
    if encounter is None:
        return []

    # Find player for buff calculations
    player = None
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            player = placeable
            break

    if player is None:
        return []

    # Log turn start
    add_combat_log(encounter, "--- Enemy Turn ---")

    # Choose target square
    target_col, target_row = choose_enemy_target(encounter)

    # Execute attack
    results = resolve_team_attack(gamestate, player, target_col, target_row, is_player_turn=False)

    # Dragon King special: move randomly after attacking
    handle_dragon_king_movement(encounter)

    return results


def handle_dragon_king_movement(encounter: Encounter) -> None:
    """Dragon King moves 1 square in a random direction after attacking."""
    from gameplay import move_2x2_unit, get_2x2_primary_position, add_combat_log

    processed = set()
    for unit in encounter.enemy_team or []:
        if unit is None or id(unit) in processed:
            continue
        processed.add(id(unit))

        if getattr(unit, "name", "") == "Dragon King":
            # Get current position before move attempt
            old_pos = get_2x2_primary_position(encounter.enemy_team, unit)

            # Random orthogonal direction
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            random.shuffle(directions)

            # Try each direction until one works
            for direction in directions:
                move_2x2_unit(encounter.enemy_team, unit, direction)
                # Check if position actually changed
                new_pos = get_2x2_primary_position(encounter.enemy_team, unit)
                if new_pos != old_pos:
                    add_combat_log(encounter, "Dragon King shifts position")
                    break  # Move succeeded

            break  # Only one Dragon King


def get_enemy_action_description(encounter: Encounter) -> str:
    """Get a description of what the enemy is about to do (for UI)."""
    target_col, target_row = choose_enemy_target(encounter)
    damage = calculate_potential_damage(encounter, target_col, target_row)

    # Count attacking units
    attacking_units = 0
    for unit in encounter.enemy_team or []:
        if unit is not None:
            attacking_units += 1

    # Unique units only (for 2x2)
    unique_units = len(set(id(u) for u in (encounter.enemy_team or []) if u is not None))

    return f"Enemy attacks ({unique_units} units targeting position ({target_col}, {target_row}), ~{damage} damage)"
