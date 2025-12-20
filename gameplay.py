"""Gameplay logic for the curses game."""

from typing import Optional, Union
import random

from game_data import GRID_HEIGHT, GRID_WIDTH, Attack, Creature, Encounter, Exit, GameState, Player, Terrain
from terrain_gen import generate_biome_terrain, generate_maze, maze_to_grid_walls, get_corner_cell_center
from creatures import spawn_creature, get_creature_for_terrain, BIOME_TERRAIN_CREATURES
from combat import (
    calculate_damage,
    calculate_effective_efficacy,
    get_melee_target,
    get_ranged_targets,
    get_magic_targets,
    get_hero_attacks,
    check_haste,
    has_ability,
    coords_to_grid_index,
    grid_index_to_coords,
)
from abilities import (
    check_evasion,
    check_flying,
    process_lifelink,
    apply_debuffs,
    clear_debuff_stacks,
    has_piercing,
    has_splash,
    process_healing_ability,
    get_effective_defense,
    get_effective_attack_damage,
    calculate_pack_hunter_bonus,
)
from experience import end_battle_experience, award_floor_stats


def add_combat_log(encounter: Encounter, message: str) -> None:
    """Add a message to the encounter's combat log."""
    if encounter is not None and encounter.combat_log is not None:
        encounter.combat_log.append(message)


BIOME_DATA = {
    "forest": {
        "name": "Forest",
        "base_tile": "grass",
        "tiles": {
            "grass": {"symbol": "░", "color": (60, 120, 60), "bg_color": (20, 50, 20)},
            "trees": {"symbol": "█", "color": (10, 60, 10), "bg_color": (20, 40, 20)},
            "bushes": {"symbol": "▒", "color": (50, 120, 60), "bg_color": (25, 60, 30)},
            "hill": {"symbol": "▓", "color": (110, 90, 60), "bg_color": (60, 40, 20)},
            "wall": {"symbol": "█", "color": (60, 80, 50), "bg_color": (30, 40, 25)},
        },
        "layers": [
            {"tile_id": "bushes", "threshold": 0.55, "seed_offset": 1000, "priority": 1},
            {"tile_id": "trees", "threshold": 0.6, "seed_offset": 2000, "priority": 2},
            {"tile_id": "hill", "threshold": 0.7, "seed_offset": 3000, "priority": 3},
        ],
        "terrain_creatures": BIOME_TERRAIN_CREATURES["forest"],
    },
    "plains": {
        "name": "Plains",
        "base_tile": "short_grass",
        "tiles": {
            "short_grass": {"symbol": "░", "color": (80, 140, 60), "bg_color": (40, 80, 30)},
            "tall_grass": {"symbol": "▒", "color": (100, 170, 70), "bg_color": (50, 100, 40)},
            "wall": {"symbol": "█", "color": (100, 90, 70), "bg_color": (50, 45, 35)},
        },
        "layers": [
            {"tile_id": "tall_grass", "threshold": 0.55, "seed_offset": 1000, "priority": 1},
        ],
        "terrain_creatures": BIOME_TERRAIN_CREATURES["plains"],
    },
    "snow": {
        "name": "Snowy Mountain",
        "base_tile": "snow",
        "tiles": {
            "snow": {"symbol": "░", "color": (230, 240, 245), "bg_color": (180, 205, 215)},
            "rocky": {"symbol": "▓", "color": (140, 150, 160), "bg_color": (90, 100, 110)},
            "trees": {"symbol": "█", "color": (40, 90, 50), "bg_color": (25, 55, 35)},
            "wall": {"symbol": "█", "color": (160, 170, 180), "bg_color": (100, 110, 120)},
        },
        "layers": [
            {"tile_id": "rocky", "threshold": 0.6, "seed_offset": 1000, "priority": 1},
            {"tile_id": "trees", "threshold": 0.65, "seed_offset": 2000, "priority": 2},
        ],
        "terrain_creatures": BIOME_TERRAIN_CREATURES["snow"],
    },
    "underground": {
        "name": "Underground",
        "base_tile": "dirt",
        "tiles": {
            "dirt": {"symbol": "░", "color": (110, 80, 50), "bg_color": (60, 40, 25)},
            "moss": {"symbol": "▒", "color": (70, 110, 70), "bg_color": (35, 65, 35)},
            "mushrooms": {"symbol": "▓", "color": (170, 100, 60), "bg_color": (70, 40, 30)},
            "stalactite": {"symbol": "█", "color": (120, 120, 130), "bg_color": (60, 60, 70)},
            "wall": {"symbol": "█", "color": (90, 80, 70), "bg_color": (50, 40, 35)},
        },
        "layers": [
            {"tile_id": "moss", "threshold": 0.55, "seed_offset": 1000, "priority": 1},
            {"tile_id": "mushrooms", "threshold": 0.65, "seed_offset": 2000, "priority": 2},
            {"tile_id": "stalactite", "threshold": 0.75, "seed_offset": 3000, "priority": 3},
        ],
        "terrain_creatures": BIOME_TERRAIN_CREATURES["underground"],
    },
}

def grid_coords_to_index(x: int, y: int) -> Optional[int]:
    """Convert 2D grid coordinates (0-2, 0-2) to 1D index (0-8)."""
    if not (0 <= x <= 2 and 0 <= y <= 2):
        return None
    return y * 3 + x


def get_enemy_at_grid_position(encounter: Encounter, target_x: int, target_y: int) -> Optional[Creature]:
    """Get the enemy creature at a grid position if it exists."""
    grid_index = grid_coords_to_index(target_x, target_y)
    if grid_index is None:
        return None
    
    target = encounter.enemy_team[grid_index]
    if target is not None and isinstance(target, Creature):
        return target
    return None


def advance_step(
    gamestate: GameState, action: Optional[tuple[str, ...]]
) -> GameState:
    """Advance the game by one step based on the player action."""
    # Import here to avoid circular imports
    from ai import execute_enemy_turn

    if action is None:
        return gamestate

    action_type = action[0]

    player = None
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            player = placeable
            break
    if player is None:
        raise ValueError("No player found in gamestate.")

    if action_type == "move":
        dx, dy = action[1], action[2]
        new_x = player.x + dx
        new_y = player.y + dy

        # Check bounds and update position if valid
        if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
            # Check for wall collision
            is_wall = False
            for placeable in gamestate.placeables or []:
                if isinstance(placeable, Terrain) and placeable.x == new_x and placeable.y == new_y:
                    if placeable.tile_type == "wall":
                        is_wall = True
                        break

            if is_wall:
                return gamestate  # Can't move into wall

            player.x = new_x
            player.y = new_y

            # Check collision with placeables
            for placeable in gamestate.placeables or []:
                if placeable.x == player.x and placeable.y == player.y:
                    # Encounter Trigger
                    if isinstance(placeable, Encounter):
                        gamestate.active_encounter = placeable
                        # Use initialize_encounter for proper setup
                        initialize_encounter(placeable, player)

                        # If enemy has Haste, execute their turn first
                        if placeable.current_turn == "enemy":
                            execute_enemy_turn(gamestate)
                            placeable.current_turn = "player"
                            check_encounter_end(gamestate)
                        break

                    # Exit Trigger
                    elif isinstance(placeable, Exit):
                        if gamestate.current_stage < gamestate.max_stages:
                            # Award stat points for completing the floor
                            award_floor_stats(player)
                            # Mark that we need to advance after stat allocation
                            gamestate.pending_next_stage = True
                            # Don't generate new map yet - will happen after stat allocation
                        # No exit on last stage (Boss handles win)

    elif action_type == "attack" and gamestate.active_encounter is not None:
        encounter = gamestate.active_encounter
        # Only allow action on player's turn
        if encounter.current_turn != "player":
            return gamestate

        add_combat_log(encounter, "--- Player Turn ---")
        target_x, target_y = action[1], action[2]
        resolve_team_attack(gamestate, player, target_x, target_y, is_player_turn=True)

        if not check_encounter_end(gamestate):
            # Toggle to enemy turn and execute
            encounter.current_turn = "enemy"
            encounter.turn_number += 1
            execute_enemy_turn(gamestate)
            if not check_encounter_end(gamestate):
                encounter.current_turn = "player"

    elif action_type == "convert" and gamestate.active_encounter is not None:
        encounter = gamestate.active_encounter
        # Only allow action on player's turn
        if encounter.current_turn != "player":
            return gamestate

        add_combat_log(encounter, "--- Player Turn ---")
        target_x, target_y = action[1], action[2]
        resolve_team_convert(gamestate, player, target_x, target_y)

        if not check_encounter_end(gamestate):
            # Toggle to enemy turn and execute
            encounter.current_turn = "enemy"
            encounter.turn_number += 1
            execute_enemy_turn(gamestate)
            if not check_encounter_end(gamestate):
                encounter.current_turn = "player"

    elif action_type == "move_unit" and gamestate.active_encounter is not None:
        encounter = gamestate.active_encounter
        # Only allow action on player's turn
        if encounter.current_turn != "player":
            return gamestate

        add_combat_log(encounter, "--- Player Turn ---")
        # Move action: move one unit one square, consumes entire team's turn
        unit_idx, direction = action[1], action[2]
        moved = resolve_move_action(gamestate.active_encounter, unit_idx, direction, is_player=True)

        if moved and not check_encounter_end(gamestate):
            # Toggle to enemy turn and execute
            encounter.current_turn = "enemy"
            encounter.turn_number += 1
            execute_enemy_turn(gamestate)
            if not check_encounter_end(gamestate):
                encounter.current_turn = "player"

    return gamestate


def resolve_team_attack(
    gamestate: GameState,
    player: Player,
    target_col: int,
    target_row: int,
    is_player_turn: bool,
) -> list[dict]:
    """Resolve all units' attack actions for the team turn.

    All units that can attack the target square do so simultaneously.
    Each unit uses its best attack (highest damage) rather than all attacks.
    2x2 units attack once using their top-left position.
    """
    encounter = gamestate.active_encounter
    if encounter is None:
        return []

    acting_team = encounter.player_team if is_player_turn else encounter.enemy_team
    enemy_team = encounter.enemy_team if is_player_turn else encounter.player_team
    results = []

    # Track units that have acted (for 2x2 deduplication)
    processed_units = set()
    # Track units that attacked (for debuff clearing)
    attackers = []

    for idx, unit in enumerate(acting_team or []):
        if unit is None:
            continue

        # Skip if already processed (2x2 units appear in multiple slots)
        if id(unit) in processed_units:
            continue
        processed_units.add(id(unit))

        # For 2x2 units, use primary (top-left) position
        if getattr(unit, "size", "1x1") == "2x2":
            primary_pos = get_2x2_primary_position(acting_team, unit)
            if primary_pos:
                attacker_col, attacker_row = primary_pos
            else:
                attacker_col, attacker_row = grid_index_to_coords(idx)
        else:
            attacker_col, attacker_row = grid_index_to_coords(idx)

        # Get unit's attacks
        if isinstance(unit, Player):
            attacks = get_hero_attacks(unit)
        else:
            attacks = unit.attacks or []

        # For 2x2 units, try both rows they occupy for melee attacks
        is_2x2 = getattr(unit, "size", "1x1") == "2x2"
        rows_to_try = [attacker_row]
        if is_2x2 and attacker_row < 2:
            rows_to_try.append(attacker_row + 1)

        # Select best attack (highest potential damage that can hit the target)
        best_attack = None
        best_attack_row = attacker_row
        for try_row in rows_to_try:
            candidate = select_best_attack(
                encounter, unit, attacks, attacker_col, try_row,
                target_col, target_row, is_player_turn, player
            )
            if candidate is not None:
                # For 2x2 melee, prefer the row that can actually hit
                if best_attack is None:
                    best_attack = candidate
                    best_attack_row = try_row

        if best_attack is None:
            continue

        targets = get_attack_targets(
            encounter, best_attack, attacker_col, best_attack_row, target_col, target_row, is_player_turn
        )

        # Track if unit attacked for debuff clearing
        unit_attacked = False

        for target, tcol, trow in targets:
            attacker_name = getattr(unit, "name", "Unknown")
            target_name = getattr(target, "name", "Unknown")

            # Check evasion
            if check_evasion(target):
                results.append({"attacker": unit, "target": target, "evaded": True})
                add_combat_log(encounter, f"{target_name} evades {attacker_name}'s attack!")
                unit_attacked = True
                continue

            # Get effective damage with all bonuses
            effective_damage = get_effective_attack_damage(unit, best_attack, encounter, is_player_turn)
            modified_attack = Attack(
                attack_type=best_attack.attack_type,
                damage=effective_damage,
                range_min=best_attack.range_min,
                range_max=best_attack.range_max,
                abilities=best_attack.abilities,
            )

            # Calculate final damage (includes Flying immunity, defense bonuses)
            damage = calculate_attack_result(
                modified_attack, unit, target, encounter, is_player_turn, player
            )

            # Apply damage
            target.current_health = max(0, target.current_health - damage)
            unit_attacked = True

            # Log the attack
            if damage > 0:
                add_combat_log(encounter, f"{attacker_name} hits {target_name} for {damage} dmg")
                # Process Lifelink
                process_lifelink(unit, damage)
            else:
                add_combat_log(encounter, f"{attacker_name}'s attack deals 0 dmg to {target_name}")

            # Apply debuffs from attack
            applied_debuffs = apply_debuffs(best_attack, target)
            if applied_debuffs:
                for debuff in applied_debuffs:
                    add_combat_log(encounter, f"{target_name} gains {debuff}!")

            results.append({
                "attacker": unit,
                "target": target,
                "damage": damage,
                "debuffs": applied_debuffs,
            })

        # Clear debuff stacks when unit attacks (regardless of damage dealt)
        if unit_attacked:
            attackers.append(unit)

        # Process Healing ability for magic attacks
        if best_attack.attack_type == "magic":
            healed = process_healing_ability(unit, encounter, is_player_turn)
            if healed:
                unit_name = getattr(unit, "name", "Unknown")
                add_combat_log(encounter, f"{unit_name} heals ally for {healed} HP")
                results.append({"attacker": unit, "healed": healed})

    # Clear debuff stacks from attackers
    for attacker in attackers:
        clear_debuff_stacks(attacker)

    # Remove dead units (and update player.creatures if ally dies)
    remove_dead_units(encounter, is_player_turn, player)

    return results


def calculate_expected_result(
    encounter: Encounter,
    unit: Union[Creature, Player],
    attack: Attack,
    attacker_col: int,
    attacker_row: int,
    target_col: int,
    target_row: int,
    is_player_turn: bool,
    player: Player,
    for_conversion: bool = False,
    effective_efficacy: int = 100,
) -> int:
    """Calculate total expected damage or conversion points for an attack.

    Uses calculate_attack_result to account for Flying, defense, etc.
    Does not account for Evasion (random) or apply any actual changes.
    """
    targets = get_attack_targets(
        encounter, attack, attacker_col, attacker_row, target_col, target_row, is_player_turn
    )
    if not targets:
        return 0

    total = 0
    for target, _, _ in targets:
        # Get effective damage with all bonuses
        effective_damage = get_effective_attack_damage(unit, attack, encounter, is_player_turn)
        modified_attack = Attack(
            attack_type=attack.attack_type,
            damage=effective_damage,
            range_min=attack.range_min,
            range_max=attack.range_max,
            abilities=attack.abilities,
        )

        result = calculate_attack_result(
            modified_attack, unit, target, encounter, is_player_turn, player,
            for_conversion, effective_efficacy
        )
        total += result

    return total


def select_best_attack(
    encounter: Encounter,
    unit: Union[Creature, Player],
    attacks: list[Attack],
    attacker_col: int,
    attacker_row: int,
    target_col: int,
    target_row: int,
    is_player_turn: bool,
    player: Optional[Player] = None,
    for_conversion: bool = False,
    effective_efficacy: int = 100,
) -> Optional[Attack]:
    """Select the best attack that can hit the target.

    Returns the attack with highest expected result (damage or conversion points).
    """
    best_attack = None
    best_result = -1

    for attack in attacks:
        expected = calculate_expected_result(
            encounter, unit, attack, attacker_col, attacker_row,
            target_col, target_row, is_player_turn, player,
            for_conversion, effective_efficacy
        )
        if expected > best_result:
            best_result = expected
            best_attack = attack

    return best_attack


def calculate_attack_result(
    attack: Attack,
    attacker: Union[Creature, Player],
    defender: Union[Creature, Player],
    encounter: Encounter,
    is_player_turn: bool,
    player: Player,
    for_conversion: bool = False,
    effective_efficacy: int = 100,
) -> int:
    """Calculate attack damage or conversion points.

    Shared logic:
    - Flying immunity to melee (returns 0)
    - Debuff reductions (defanged/blinded/silenced/weakened)

    Attack-specific (for_conversion=False):
    - Minimum 1 damage guarantee
    - Attack-type specific defense with get_effective_defense

    Conversion-specific (for_conversion=True):
    - Efficacy multiplier
    - 50% bonus for low HP targets
    - Uses highest of all defenses
    """
    import math

    base_value = attack.damage

    # Flying immunity to melee (shared)
    if attack.attack_type == "melee" and check_flying(defender):
        return 0

    # Apply debuffs to damage (shared)
    attacker_debuffs = getattr(attacker, "debuffs", {}) or {}
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

    base_value = max(0, base_value - debuff_reduction)

    # If debuffs reduce to 0, still deal minimum 1
    if attack.damage > 0 and base_value == 0:
        base_value = 1

    if base_value == 0:
        return 0

    if for_conversion:
        # Apply efficacy
        base_value = math.floor(base_value * (effective_efficacy / 100))

        # 50% bonus if target below 50% HP
        if defender.current_health < defender.max_health / 2:
            base_value = math.floor(base_value * 1.5)

        # Highest defense stat
        defense = max(
            getattr(defender, "defense", 0),
            getattr(defender, "dodge", 0),
            getattr(defender, "resistance", 0)
        )

        return max(0, base_value - defense)
    else:
        # Get effective defense with all bonuses
        defender_is_player_side = not is_player_turn
        if attack.attack_type == "melee":
            defense = get_effective_defense(defender, "defense", encounter, defender_is_player_side, player)
        elif attack.attack_type == "ranged":
            defense = get_effective_defense(defender, "dodge", encounter, defender_is_player_side, player)
        else:  # magic
            defense = get_effective_defense(defender, "resistance", encounter, defender_is_player_side, player)

        return max(1, base_value - defense)


def get_attack_targets(
    encounter: Encounter,
    attack: Attack,
    attacker_col: int,
    attacker_row: int,
    target_col: int,
    target_row: int,
    attacker_is_player: bool,
) -> list[tuple[Union[Creature, Player], int, int]]:
    """Get all valid targets for an attack."""
    targets = []
    enemy_team = encounter.enemy_team if attacker_is_player else encounter.player_team

    if attack.attack_type == "melee":
        target = get_melee_target(
            encounter, attacker_col, attacker_row, attacker_is_player, target_col, target_row
        )
        if target:
            if has_piercing(attack):
                # Piercing hits all enemies in the same row
                processed = set()
                for col in range(3):
                    idx = target_row * 3 + col
                    enemy = enemy_team[idx] if enemy_team else None
                    if enemy is not None and id(enemy) not in processed:
                        targets.append((enemy, col, target_row))
                        processed.add(id(enemy))
            else:
                targets.append((target, target_col, target_row))

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
            has_splash(attack),
        )

    elif attack.attack_type == "magic":
        targets = get_magic_targets(encounter, attacker_col, attacker_is_player)

    return targets


def resolve_team_convert(
    gamestate: GameState,
    player: Player,
    target_col: int,
    target_row: int,
) -> list[dict]:
    """Resolve all units' convert actions for the team turn.

    Each unit uses its best attack for conversion.
    2x2 units convert once using their top-left position.
    Pack Hunter bonus applies to conversion.
    """
    encounter = gamestate.active_encounter
    if encounter is None:
        return []

    results = []
    processed_units = set()  # Track 2x2 units
    converters = []  # Track units that converted for debuff clearing

    for idx, unit in enumerate(encounter.player_team or []):
        if unit is None:
            continue

        # Skip if already processed (2x2 units)
        if id(unit) in processed_units:
            continue
        processed_units.add(id(unit))

        # For 2x2 units, use primary (top-left) position
        if getattr(unit, "size", "1x1") == "2x2":
            primary_pos = get_2x2_primary_position(encounter.player_team, unit)
            if primary_pos:
                attacker_col, attacker_row = primary_pos
            else:
                attacker_col, attacker_row = grid_index_to_coords(idx)
        else:
            attacker_col, attacker_row = grid_index_to_coords(idx)

        # Get unit's attacks (conversion uses same targeting)
        if isinstance(unit, Player):
            attacks = get_hero_attacks(unit)
            base_efficacy = 100  # Hero base efficacy
        else:
            attacks = unit.attacks or []
            base_efficacy = unit.conversion_efficacy

        # Calculate effective efficacy with CHA bonus
        effective_efficacy = calculate_effective_efficacy(player, base_efficacy)

        # Select best attack for conversion (uses conversion logic for expected result)
        best_attack = select_best_attack(
            encounter, unit, attacks, attacker_col, attacker_row,
            target_col, target_row, True, player,
            for_conversion=True, effective_efficacy=effective_efficacy
        )

        if best_attack is None:
            continue

        targets = get_attack_targets(
            encounter, best_attack, attacker_col, attacker_row, target_col, target_row, True
        )

        unit_converted = False

        for target, tcol, trow in targets:
            if not isinstance(target, Creature):
                continue  # Can only convert creatures

            converter_name = getattr(unit, "name", "Unknown")
            target_name = getattr(target, "name", "Unknown")

            # Calculate conversion points with Pack Hunter bonus
            pack_bonus = calculate_pack_hunter_bonus(unit, encounter, True)
            attack_with_bonus = Attack(
                attack_type=best_attack.attack_type,
                damage=best_attack.damage + pack_bonus.get(best_attack.attack_type, 0),
                range_min=best_attack.range_min,
                range_max=best_attack.range_max,
                abilities=best_attack.abilities,
            )
            conversion = calculate_attack_result(
                attack_with_bonus, unit, target, encounter, True, player,
                for_conversion=True, effective_efficacy=effective_efficacy
            )

            if conversion > 0:
                target.conversion_progress = getattr(target, "conversion_progress", 0) + conversion
                unit_converted = True

                add_combat_log(encounter, f"{converter_name} converts {target_name} +{conversion}")

                results.append({
                    "converter": unit,
                    "target": target,
                    "conversion": conversion,
                    "total": target.conversion_progress,
                })

                # Check if fully converted
                if target.conversion_progress >= target.max_health:
                    add_combat_log(encounter, f"{target_name} joins your team!")
                    # Add to pending recruits
                    if gamestate.pending_recruits is None:
                        gamestate.pending_recruits = []
                    gamestate.pending_recruits.append(target)

                    # Remove from enemy team
                    target_idx = trow * 3 + tcol
                    remove_unit_from_grid(encounter.enemy_team, target, target_idx)

        # Clear debuff stacks when unit converts
        if unit_converted:
            converters.append(unit)

    # Clear debuff stacks from converters
    for converter in converters:
        clear_debuff_stacks(converter)

    return results


def resolve_move_action(
    encounter: Encounter,
    unit_idx: int,
    direction: tuple[int, int],
    is_player: bool,
) -> bool:
    """Move one unit one square (orthogonal only).

    For 1x1 units: Can swap with an ally.
    For 2x2 units: Uses move_2x2_unit which displaces 1x1 units.
    Consumes the entire team's turn.
    Returns True if move was successful.
    """
    team = encounter.player_team if is_player else encounter.enemy_team
    if not team or unit_idx < 0 or unit_idx >= 9:
        return False

    unit = team[unit_idx]
    if unit is None:
        return False

    dx, dy = direction
    # Only allow orthogonal movement
    if abs(dx) + abs(dy) != 1:
        return False

    unit_name = getattr(unit, "name", "Unknown")

    # Handle 2x2 units specially
    if getattr(unit, "size", "1x1") == "2x2":
        displaced = move_2x2_unit(team, unit, direction)
        # move_2x2_unit returns [] on failure (no positions found or out of bounds)
        # Need to check if unit actually moved by comparing positions
        current_positions = [i for i, u in enumerate(team) if u is unit]
        if len(current_positions) != 4:
            return False  # Unit not properly placed
        # If we get here, move was attempted. Check if positions changed.
        # move_2x2_unit returns displaced units; empty list could mean success with no displacement
        # The function returns [] on invalid move too, so check if unit is in valid position
        min_row = min(p // 3 for p in current_positions)
        min_col = min(p % 3 for p in current_positions)
        # Valid 2x2 position means top-left is at row 0-1, col 0-1
        if 0 <= min_row <= 1 and 0 <= min_col <= 1:
            add_combat_log(encounter, f"{unit_name} moves")
            return True  # Unit is in valid position after move
        return False

    # Handle 1x1 units - simple swap
    unit_col, unit_row = grid_index_to_coords(unit_idx)
    new_col = unit_col + dx
    new_row = unit_row + dy

    # Check bounds
    if not (0 <= new_col < 3 and 0 <= new_row < 3):
        return False

    new_idx = coords_to_grid_index(new_col, new_row)
    other_unit = team[new_idx]

    # Cannot swap into a 2x2 unit's space (would break it)
    if other_unit is not None and getattr(other_unit, "size", "1x1") == "2x2":
        return False

    # Swap with ally if present, or move to empty square
    team[new_idx] = unit
    team[unit_idx] = other_unit

    if other_unit is not None:
        other_name = getattr(other_unit, "name", "Unknown")
        add_combat_log(encounter, f"{unit_name} swaps with {other_name}")
    else:
        add_combat_log(encounter, f"{unit_name} moves")

    return True


def remove_dead_units(
    encounter: Encounter, is_player_turn: bool, player: Optional[Player] = None
) -> list[Creature]:
    """Remove dead units from the battlefield. Returns list of removed units.

    If player is provided and it's the enemy's turn, also removes dead allies
    from the player's permanent team.
    """
    enemy_team = encounter.enemy_team if is_player_turn else encounter.player_team
    removed = []
    removed_ids = set()  # Track already removed for 2x2

    for idx in range(9):
        unit = enemy_team[idx] if enemy_team else None
        if unit is not None and unit.current_health <= 0:
            if id(unit) not in removed_ids:
                removed.append(unit)
                removed_ids.add(id(unit))
                unit_name = getattr(unit, "name", "Unknown")
                add_combat_log(encounter, f"{unit_name} is defeated!")

                # If a player ally dies, also remove from player's permanent team
                if not is_player_turn and player is not None and isinstance(unit, Creature):
                    if player.creatures:
                        for i, creature in enumerate(player.creatures):
                            if creature is unit:
                                player.creatures[i] = None
                                # Don't break - need to clear all positions for 2x2 units
            remove_unit_from_grid(enemy_team, unit, idx)

    return removed


def remove_unit_from_grid(team: list, unit: Union[Creature, Player], start_idx: int) -> None:
    """Remove a unit from the grid (handles 2x2 units too)."""
    if team is None:
        return

    # For 2x2 units, remove all instances
    if hasattr(unit, "size") and unit.size == "2x2":
        for idx in range(9):
            if team[idx] is unit:
                team[idx] = None
    else:
        team[start_idx] = None


def check_encounter_end(gamestate: GameState) -> bool:
    """Check if encounter has ended. Returns True if ended."""
    if gamestate.active_encounter is None:
        return True

    encounter = gamestate.active_encounter

    # Find player for experience calculation
    player = None
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            player = placeable
            break

    # Check if all enemies are gone (player wins)
    if all(enemy is None for enemy in (encounter.enemy_team or [])):
        # Process experience and tier progression
        battle_results = None
        if player:
            battle_results = end_battle_experience(encounter, player)

        # Store battle results for display
        gamestate.last_battle_results = battle_results

        # Collect any pending recruits (converted creatures)
        # pending_recruits was populated during convert actions

        # Remove encounter from map
        gamestate.placeables = [
            p for p in gamestate.placeables if p != encounter
        ]
        gamestate.active_encounter = None

        # Boss Win Condition
        if gamestate.current_stage == gamestate.max_stages:
            gamestate.status = "won"

        return True

    # Check if all player units are gone (game over)
    if all(ally is None for ally in (encounter.player_team or [])):
        gamestate.status = "lost"
        gamestate.active_encounter = None
        gamestate.last_battle_results = None
        return True

    return False


def initialize_encounter(encounter: Encounter, player: Player) -> None:
    """Initialize encounter state when triggered."""
    encounter.player_team = list(player.creatures)
    encounter.player_team[player.team_position] = player
    encounter.enemy_team = [None] * 9

    # Randomly place enemy creatures
    if encounter.creatures:
        _randomly_place_enemies(encounter.enemy_team, encounter.creatures)

    # Determine first turn based on Haste
    encounter.current_turn = "enemy" if check_haste(encounter) else "player"
    encounter.turn_number = 0


def _randomly_place_enemies(team: list, creatures: list) -> None:
    """Randomly place enemy creatures on a 3x3 grid.

    Only one 2x2 unit can fit, so we place at most one.
    1x1 units fill remaining spaces.
    """
    # Separate 2x2 and 1x1 units
    large_units = [u for u in creatures if getattr(u, "size", "1x1") == "2x2"]
    small_units = [u for u in creatures if getattr(u, "size", "1x1") == "1x1"]

    # Shuffle for randomness
    random.shuffle(large_units)
    random.shuffle(small_units)

    # Place at most ONE 2x2 unit (grid can only fit one)
    # Valid 2x2 top-left positions: (0,0), (1,0), (0,1), (1,1)
    if large_units:
        valid_2x2_starts = [(0, 0), (1, 0), (0, 1), (1, 1)]
        random.shuffle(valid_2x2_starts)

        unit = large_units[0]  # Only place the first one
        for col, row in valid_2x2_starts:
            indices = [
                row * 3 + col,
                row * 3 + col + 1,
                (row + 1) * 3 + col,
                (row + 1) * 3 + col + 1,
            ]
            if all(team[idx] is None for idx in indices):
                for idx in indices:
                    team[idx] = unit
                break

    # Place 1x1 units in remaining empty positions
    empty_positions = [i for i in range(9) if team[i] is None]
    random.shuffle(empty_positions)

    for unit in small_units:
        if empty_positions:
            pos = empty_positions.pop()
            team[pos] = unit


# === 2x2 LARGE UNIT SUPPORT ===


def is_2x2_placement_valid(team: list, start_col: int, start_row: int) -> bool:
    """Check if a 2x2 unit can be placed starting at the given position.

    2x2 occupies: (col, row), (col+1, row), (col, row+1), (col+1, row+1)
    """
    # Must fit in grid (can't start at col 2 or row 2)
    if start_col >= 2 or start_row >= 2:
        return False

    # Get the four indices
    indices = get_2x2_indices(start_col, start_row)

    # Check no existing 2x2 unit conflicts
    existing_2x2 = None
    for idx in indices:
        unit = team[idx] if team else None
        if unit is not None and getattr(unit, "size", "1x1") == "2x2":
            if existing_2x2 is None:
                existing_2x2 = unit
            elif existing_2x2 is not unit:
                return False  # Another 2x2 exists

    return True


def get_2x2_indices(start_col: int, start_row: int) -> list[int]:
    """Get the four grid indices for a 2x2 unit placed at (col, row)."""
    return [
        start_row * 3 + start_col,      # top-left
        start_row * 3 + start_col + 1,  # top-right
        (start_row + 1) * 3 + start_col,      # bottom-left
        (start_row + 1) * 3 + start_col + 1,  # bottom-right
    ]


def place_2x2_unit(team: list, unit: Creature, start_col: int, start_row: int) -> list[Creature]:
    """Place a 2x2 unit in the grid. Displaces existing 1x1 units.

    Returns list of displaced units.
    """
    indices = get_2x2_indices(start_col, start_row)
    displaced = []

    for idx in indices:
        existing = team[idx]
        if existing is not None and existing is not unit:
            if getattr(existing, "size", "1x1") != "2x2":
                displaced.append(existing)
        team[idx] = unit

    return displaced


def move_2x2_unit(team: list, unit: Creature, direction: tuple[int, int]) -> list[Creature]:
    """Move a 2x2 unit one square. Displaces units in the new squares.

    Returns list of displaced units (which move into opened squares).
    """
    # Find current position (top-left corner)
    current_positions = [i for i, u in enumerate(team) if u is unit]
    if len(current_positions) != 4:
        return []

    min_row = min(p // 3 for p in current_positions)
    min_col = min(p % 3 for p in current_positions)

    dx, dy = direction
    new_row = min_row + dy
    new_col = min_col + dx

    # Validate bounds
    if not (0 <= new_row <= 1 and 0 <= new_col <= 1):
        return []  # Invalid move

    new_indices = get_2x2_indices(new_col, new_row)
    old_indices = get_2x2_indices(min_col, min_row)

    # Collect displaced units
    displaced = []
    for idx in new_indices:
        existing = team[idx]
        if existing is not None and existing is not unit:
            displaced.append(existing)

    # Clear old positions
    for idx in old_indices:
        team[idx] = None

    # Place unit at new position
    for idx in new_indices:
        team[idx] = unit

    # Place displaced units in opened slots
    opened = [idx for idx in old_indices if idx not in new_indices]
    for i, disp_unit in enumerate(displaced[:len(opened)]):
        team[opened[i]] = disp_unit

    return displaced


def get_2x2_primary_position(team: list, unit: Creature) -> Optional[tuple[int, int]]:
    """Get the top-left position of a 2x2 unit.

    For ranged/magic targeting, 2x2 units are treated as being at their
    front-top-most square.
    """
    for idx, u in enumerate(team or []):
        if u is unit:
            row, col = idx // 3, idx % 3
            # Return top-left corner
            return col, row
    return None


def generate_map(
    current_player: Optional[Player] = None,
    stage: int = 1,
    biome_order: list[str] = None,
    run_seed: Optional[int] = None,
) -> GameState:
    """Generate a map with terrain, encounters, and a player."""

    # Default biome order if not provided
    if biome_order is None:
        biome_order = ["forest", "plains", "snow", "underground"]

    if run_seed is None:
        run_seed = random.randint(0, 2**31 - 1)

    # Determine biome settings
    biome_index = min((stage - 1) // 5, 3)
    current_biome_key = biome_order[biome_index]
    biome_info = BIOME_DATA[current_biome_key]
    terrain_tiles = biome_info["tiles"]
    terrain_creatures = biome_info.get("terrain_creatures", {})

    placeables = []

    # Seed for this level
    seed = run_seed + stage * 10000 + biome_index * 1000
    maze_rng = random.Random(seed)

    # Determine maze size: higher levels favor 4x4
    # Probability of 4x4 increases with stage: 0% at stage 1, up to 76% at stage 20
    prob_4x4 = min(0.8, (stage - 1) * 0.04)
    maze_size = 4 if maze_rng.random() < prob_4x4 else 3

    # Calculate cell dimensions to fit grid interior (excluding 1-tile border)
    # Interior is (GRID_WIDTH - 2) x (GRID_HEIGHT - 2) = 48 x 23
    # For n cells with (n-1) internal walls: n * cell_size + (n - 1) <= interior
    # cell_size = (interior - n + 1) // n
    interior_width = GRID_WIDTH - 2  # 48
    interior_height = GRID_HEIGHT - 2  # 23
    cell_width = (interior_width - maze_size + 1) // maze_size
    cell_height = (interior_height - maze_size + 1) // maze_size

    # Generate maze and get wall positions
    maze = generate_maze(seed, maze_size)
    wall_positions = maze_to_grid_walls(maze, maze_size, cell_width, cell_height, GRID_WIDTH, GRID_HEIGHT)

    # Choose random corners for player and exit
    corners = ["TL", "TR", "BL", "BR"]
    maze_rng.shuffle(corners)
    player_corner = corners[0]
    exit_corner = corners[1]

    player_x, player_y = get_corner_cell_center(maze_size, cell_width, cell_height, player_corner)
    exit_x, exit_y = get_corner_cell_center(maze_size, cell_width, cell_height, exit_corner)

    # Player Setup
    if current_player:
        player = current_player
        player.x = player_x
        player.y = player_y
    else:
        player = Player(x=player_x, y=player_y)

    placeables.append(player)

    # Terrain Generation - use noise for cell interiors
    terrain_map = generate_biome_terrain(
        seed=seed,
        width=GRID_WIDTH,
        height=GRID_HEIGHT,
        base_tile=biome_info["base_tile"],
        layers=biome_info["layers"],
        scale=biome_info.get("noise_scale", 0.1),
    )

    base_tile = biome_info["base_tile"]
    wall_tile = terrain_tiles["wall"]

    # Place all terrain including border walls
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            # Border walls (edge of map)
            if x == 0 or x == GRID_WIDTH - 1 or y == 0 or y == GRID_HEIGHT - 1:
                placeables.append(
                    Terrain(
                        x=x,
                        y=y,
                        symbol=wall_tile["symbol"],
                        color=wall_tile["color"],
                        bg_color=wall_tile["bg_color"],
                        tile_type="wall",
                    )
                )
            # Maze walls (between cells)
            elif (x, y) in wall_positions:
                placeables.append(
                    Terrain(
                        x=x,
                        y=y,
                        symbol=wall_tile["symbol"],
                        color=wall_tile["color"],
                        bg_color=wall_tile["bg_color"],
                        tile_type="wall",
                    )
                )
            # Regular terrain (cell interiors)
            else:
                tile_id = terrain_map.get((x, y), base_tile)
                tile_def = terrain_tiles.get(tile_id, terrain_tiles[base_tile])
                placeables.append(
                    Terrain(
                        x=x,
                        y=y,
                        symbol=tile_def["symbol"],
                        color=tile_def["color"],
                        bg_color=tile_def["bg_color"],
                        tile_type=tile_id,
                    )
                )

    # Level Specific Generation
    if stage == 20:
        # Boss Level - spawn Dragon King at exit corner
        boss = spawn_creature("Dragon King")
        placeables.append(Encounter(x=exit_x, y=exit_y, symbol="D", color=(255, 80, 80), creatures=[boss]))
    else:
        # Standard Level
        # Place Exit at chosen corner
        placeables.append(Exit(x=exit_x, y=exit_y, symbol=">", color=(255, 255, 255), visible=True))

        # Encounters - each cell has independent chance based on terrain
        encounter_chance = 0.03  # 3% chance per cell

        # Use seeded RNG for reproducible encounter placement
        encounter_rng = random.Random(seed + 999)

        # Enemy count scaling based on stage (deeper = more enemies)
        # Stage 1-5: 1-2 enemies, Stage 6-10: 2-3, Stage 11-15: 3-4, Stage 16-19: 4-5
        biome_idx = (stage - 1) // 5  # 0-3
        min_enemies = 1 + biome_idx
        max_enemies = 2 + biome_idx

        # Enemy tier scaling - chance of higher starting tier in deeper biomes
        tier_chance = biome_idx * 0.15  # 0%, 15%, 30%, 45% chance per enemy

        for y in range(1, GRID_HEIGHT - 1):
            for x in range(1, GRID_WIDTH - 1):
                # Skip wall positions
                if (x, y) in wall_positions:
                    continue

                # Skip cells near player spawn or exit
                if abs(x - player.x) < 3 and abs(y - player.y) < 3:
                    continue
                if abs(x - exit_x) < 2 and abs(y - exit_y) < 2:
                    continue

                # Roll for encounter
                if encounter_rng.random() >= encounter_chance:
                    continue

                # Get terrain at this position
                terrain_at_pos = terrain_map.get((x, y), base_tile)
                creatures_for_terrain = terrain_creatures.get(terrain_at_pos, [])

                # Skip if no creatures defined for this terrain
                if not creatures_for_terrain:
                    continue

                # Spawn multiple enemies for this encounter
                num_enemies = encounter_rng.randint(min_enemies, max_enemies)
                encounter_creatures = []

                for _ in range(num_enemies):
                    creature_name = encounter_rng.choice(creatures_for_terrain)
                    creature = spawn_creature(creature_name)

                    # Roll for starting at higher tier
                    if encounter_rng.random() < tier_chance:
                        bonus_tier = encounter_rng.randint(1, biome_idx)
                        creature.set_tier(bonus_tier)

                    encounter_creatures.append(creature)

                # Use first creature's symbol/color for map display
                first = encounter_creatures[0]
                placeables.append(Encounter(x=x, y=y, symbol=first.symbol, color=first.color, creatures=encounter_creatures))

    return GameState(
        placeables=placeables,
        active_encounter=None,
        current_stage=stage,
        biome_order=biome_order,
        run_seed=run_seed,
    )
