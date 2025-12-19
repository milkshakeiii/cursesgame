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

    Considers all enemy units and their attacks.
    """
    total_damage = 0

    for idx, unit in enumerate(encounter.enemy_team or []):
        if unit is None:
            continue

        attacker_col, attacker_row = grid_index_to_coords(idx)
        attacks = getattr(unit, "attacks", []) or []

        for attack in attacks:
            targets = get_enemy_attack_targets(
                encounter, attack, attacker_col, attacker_row, target_col, target_row
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
                total_damage += damage

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
            encounter, attacker_row, False, target_col, target_row
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
    Returns (col, row) of target square.
    """
    best_target = (1, 1)  # Default to center
    best_damage = -1

    for row in range(3):
        for col in range(3):
            # Check if there's a player unit at this position
            idx = row * 3 + col
            target = encounter.player_team[idx] if encounter.player_team else None

            if target is None:
                continue

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
    from gameplay import resolve_team_attack, move_2x2_unit

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

    # Choose target square
    target_col, target_row = choose_enemy_target(encounter)

    # Execute attack
    results = resolve_team_attack(gamestate, player, target_col, target_row, is_player_turn=False)

    # Dragon King special: move randomly after attacking
    handle_dragon_king_movement(encounter)

    return results


def handle_dragon_king_movement(encounter: Encounter) -> None:
    """Dragon King moves 1 square in a random direction after attacking."""
    from gameplay import move_2x2_unit

    for unit in encounter.enemy_team or []:
        if unit is not None and getattr(unit, "name", "") == "Dragon King":
            # Random orthogonal direction
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            random.shuffle(directions)

            # Try each direction until one works
            for direction in directions:
                displaced = move_2x2_unit(encounter.enemy_team, unit, direction)
                if displaced is not None:
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
