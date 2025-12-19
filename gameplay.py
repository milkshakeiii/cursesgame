"""Gameplay logic for the curses game."""

from typing import Optional, Union
import random

from game_data import GRID_HEIGHT, GRID_WIDTH, Attack, Creature, Encounter, Exit, GameState, Player, Terrain
from terrain_gen import generate_biome_terrain
from creatures import spawn_creature, get_creature_for_terrain, BIOME_TERRAIN_CREATURES
from combat import (
    calculate_damage,
    calculate_conversion,
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
)

BIOME_DATA = {
    "forest": {
        "name": "Forest",
        "base_tile": "grass",
        "tiles": {
            "grass": {"symbol": "░", "color": (60, 120, 60), "bg_color": (20, 50, 20)},
            "trees": {"symbol": "█", "color": (10, 60, 10), "bg_color": (20, 40, 20)},
            "bushes": {"symbol": "▒", "color": (50, 120, 60), "bg_color": (25, 60, 30)},
            "hill": {"symbol": "▓", "color": (110, 90, 60), "bg_color": (60, 40, 20)},
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
            player.x = new_x
            player.y = new_y

            # Check collision with placeables
            for placeable in gamestate.placeables or []:
                if placeable.x == player.x and placeable.y == player.y:
                    # Encounter Trigger
                    if isinstance(placeable, Encounter):
                        gamestate.active_encounter = placeable
                        # Initialize encounter grids
                        placeable.player_team = list(player.creatures)
                        # Place player in the center slot
                        placeable.player_team[4] = player

                        placeable.enemy_team = [None] * 9
                        if placeable.creature:
                            placeable.enemy_team[4] = placeable.creature
                        break
                    
                    # Exit Trigger
                    elif isinstance(placeable, Exit):
                        if gamestate.current_stage < gamestate.max_stages:
                            return generate_map(
                                player,
                                gamestate.current_stage + 1,
                                gamestate.biome_order,
                                gamestate.run_seed,
                            )
                        # No exit on last stage (Boss handles win)

    elif action_type == "attack" and gamestate.active_encounter is not None:
        target_x, target_y = action[1], action[2]
        resolve_team_attack(gamestate, player, target_x, target_y, is_player_turn=True)
        check_encounter_end(gamestate)

    elif action_type == "convert" and gamestate.active_encounter is not None:
        target_x, target_y = action[1], action[2]
        resolve_team_convert(gamestate, player, target_x, target_y)
        check_encounter_end(gamestate)

    elif action_type == "move_unit" and gamestate.active_encounter is not None:
        # Move action: move one unit one square, consumes entire team's turn
        unit_idx, direction = action[1], action[2]
        resolve_move_action(gamestate.active_encounter, unit_idx, direction, is_player=True)

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
    """
    encounter = gamestate.active_encounter
    if encounter is None:
        return []

    acting_team = encounter.player_team if is_player_turn else encounter.enemy_team
    enemy_team = encounter.enemy_team if is_player_turn else encounter.player_team
    results = []

    # Track units that attacked (for debuff clearing)
    attackers = []

    for idx, unit in enumerate(acting_team or []):
        if unit is None:
            continue

        attacker_col, attacker_row = grid_index_to_coords(idx)

        # Get unit's attacks
        if isinstance(unit, Player):
            attacks = get_hero_attacks(unit)
        else:
            attacks = unit.attacks or []

        for attack in attacks:
            targets = get_attack_targets(
                encounter, attack, attacker_col, attacker_row, target_col, target_row, is_player_turn
            )

            for target, tcol, trow in targets:
                # Check evasion
                if check_evasion(target):
                    results.append({"attacker": unit, "target": target, "evaded": True})
                    continue

                # Check flying immunity
                defender_has_flying = check_flying(target)

                # Get effective damage with all bonuses
                effective_damage = get_effective_attack_damage(unit, attack, encounter, is_player_turn)
                modified_attack = Attack(
                    attack_type=attack.attack_type,
                    damage=effective_damage,
                    range_min=attack.range_min,
                    range_max=attack.range_max,
                    abilities=attack.abilities,
                )

                # Calculate final damage
                attacker_debuffs = getattr(unit, "debuffs", {}) or {}
                damage = calculate_damage(
                    modified_attack, unit, target, attacker_debuffs, defender_has_flying
                )

                # Apply damage
                if damage > 0:
                    target.current_health = max(0, target.current_health - damage)
                    attackers.append(unit)

                    # Process Lifelink
                    process_lifelink(unit, damage)

                    # Apply debuffs from attack
                    applied_debuffs = apply_debuffs(attack, target)

                    results.append({
                        "attacker": unit,
                        "target": target,
                        "damage": damage,
                        "debuffs": applied_debuffs,
                    })

            # Process Healing ability for magic attacks
            if attack.attack_type == "magic":
                healed = process_healing_ability(unit, encounter, is_player_turn)
                if healed:
                    results.append({"attacker": unit, "healed": healed})

    # Clear debuff stacks from attackers (use id() to track unique units)
    seen_ids = set()
    for attacker in attackers:
        if id(attacker) not in seen_ids:
            seen_ids.add(id(attacker))
            clear_debuff_stacks(attacker)

    # Remove dead enemies
    remove_dead_units(encounter, is_player_turn)

    return results


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
            encounter, attacker_row, attacker_is_player, target_col, target_row
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
    """Resolve all units' convert actions for the team turn."""
    encounter = gamestate.active_encounter
    if encounter is None:
        return []

    results = []

    for idx, unit in enumerate(encounter.player_team or []):
        if unit is None:
            continue

        attacker_col, attacker_row = grid_index_to_coords(idx)

        # Get unit's attacks (conversion uses same targeting)
        if isinstance(unit, Player):
            attacks = get_hero_attacks(unit)
            base_efficacy = 50  # Hero base efficacy
        else:
            attacks = unit.attacks or []
            base_efficacy = unit.conversion_efficacy

        # Calculate effective efficacy with CHA bonus
        effective_efficacy = calculate_effective_efficacy(player, base_efficacy)

        for attack in attacks:
            targets = get_attack_targets(
                encounter, attack, attacker_col, attacker_row, target_col, target_row, True
            )

            for target, tcol, trow in targets:
                if not isinstance(target, Creature):
                    continue  # Can only convert creatures

                # Calculate conversion points
                conversion = calculate_conversion(attack, unit, target, effective_efficacy)

                if conversion > 0:
                    target.conversion_progress = getattr(target, "conversion_progress", 0) + conversion

                    results.append({
                        "converter": unit,
                        "target": target,
                        "conversion": conversion,
                        "total": target.conversion_progress,
                    })

                    # Check if fully converted
                    if target.conversion_progress >= target.max_health:
                        # Add to pending recruits
                        if gamestate.pending_recruits is None:
                            gamestate.pending_recruits = []
                        gamestate.pending_recruits.append(target)

                        # Remove from enemy team
                        target_idx = trow * 3 + tcol
                        remove_unit_from_grid(encounter.enemy_team, target, target_idx)

    return results


def resolve_move_action(
    encounter: Encounter,
    unit_idx: int,
    direction: tuple[int, int],
    is_player: bool,
) -> bool:
    """Move one unit one square (orthogonal only).

    Can swap with an ally. Consumes the entire team's turn.
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

    unit_col, unit_row = grid_index_to_coords(unit_idx)
    new_col = unit_col + dx
    new_row = unit_row + dy

    # Check bounds
    if not (0 <= new_col < 3 and 0 <= new_row < 3):
        return False

    new_idx = coords_to_grid_index(new_col, new_row)

    # Swap with ally if present, or move to empty square
    other_unit = team[new_idx]
    team[new_idx] = unit
    team[unit_idx] = other_unit

    return True


def remove_dead_units(encounter: Encounter, is_player_turn: bool) -> list[Creature]:
    """Remove dead units from the battlefield. Returns list of removed units."""
    enemy_team = encounter.enemy_team if is_player_turn else encounter.player_team
    removed = []

    for idx in range(9):
        unit = enemy_team[idx] if enemy_team else None
        if unit is not None and unit.current_health <= 0:
            removed.append(unit)
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

    # Check if all enemies are gone
    if all(enemy is None for enemy in (encounter.enemy_team or [])):
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
        return True

    return False


def initialize_encounter(encounter: Encounter, player: Player) -> None:
    """Initialize encounter state when triggered."""
    encounter.player_team = list(player.creatures)
    # Place player in the center slot
    encounter.player_team[4] = player
    encounter.enemy_team = [None] * 9

    if encounter.creature:
        # Place enemy creature(s) based on size
        if encounter.creature.size == "2x2":
            # Place 2x2 unit in positions 0,1,3,4 (top-left corner)
            for idx in [0, 1, 3, 4]:
                encounter.enemy_team[idx] = encounter.creature
        else:
            # Place 1x1 unit in center
            encounter.enemy_team[4] = encounter.creature

    # Determine first turn based on Haste
    encounter.current_turn = "enemy" if check_haste(encounter) else "player"
    encounter.turn_number = 0


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

    # Player Setup
    if current_player:
        player = current_player
        player.x = GRID_WIDTH // 2
        player.y = GRID_HEIGHT // 2
    else:
        player = Player(x=GRID_WIDTH // 2, y=GRID_HEIGHT // 2)
        # Ensure player is in the team grid (center)
        player.creatures[4] = player
    
    placeables.append(player)

    # Terrain Generation
    seed = run_seed + stage * 10000 + biome_index * 1000
    terrain_map = generate_biome_terrain(
        seed=seed,
        width=GRID_WIDTH,
        height=GRID_HEIGHT,
        base_tile=biome_info["base_tile"],
        layers=biome_info["layers"],
        scale=biome_info.get("noise_scale", 0.1),
    )

    base_tile = biome_info["base_tile"]
    for y in range(1, GRID_HEIGHT - 1):
        for x in range(1, GRID_WIDTH - 1):
            tile_id = terrain_map[(x, y)]
            tile_def = terrain_tiles.get(tile_id, terrain_tiles[base_tile])
            placeables.append(
                Terrain(
                    x=x,
                    y=y,
                    symbol=tile_def["symbol"],
                    color=tile_def["color"],
                    bg_color=tile_def["bg_color"],
                )
            )

    # Level Specific Generation
    if stage == 20:
        # Boss Level - spawn Dragon King from registry
        boss = spawn_creature("Dragon King")
        # Place boss
        placeables.append(Encounter(x=GRID_WIDTH - 10, y=GRID_HEIGHT // 2, symbol="D", color=(255, 80, 80), creature=boss))
    else:
        # Standard Level
        # Place Exit
        placeables.append(Exit(x=GRID_WIDTH - 2, y=GRID_HEIGHT // 2, symbol=">", color=(255, 255, 255), visible=True))

        # Encounters - spawn creatures based on terrain
        encounter_positions = [(10, 10), (15, 12), (30, 8), (20, 15), (35, 18), (8, 20)]

        # Build list of available creature names for this biome
        available_creatures = []
        for terrain_type, creature_names in terrain_creatures.items():
            available_creatures.extend(creature_names)

        if not available_creatures:
            # Fallback - shouldn't happen with proper data
            available_creatures = ["Wolf"]

        # Simple randomization: shift positions based on stage to make levels look slightly different
        for i, (base_x, base_y) in enumerate(encounter_positions):
            # rudimentary procedural generation variation
            x = (base_x + stage * 3) % (GRID_WIDTH - 2) + 1
            y = (base_y + stage * 2) % (GRID_HEIGHT - 2) + 1

            # Ensure not on player start or exit
            if abs(x - player.x) < 2 and abs(y - player.y) < 2:
                continue
            if x == GRID_WIDTH - 2 and y == GRID_HEIGHT // 2:
                continue

            # Get creature from registry
            creature_name = available_creatures[(i + stage) % len(available_creatures)]
            creature = spawn_creature(creature_name)
            placeables.append(Encounter(x=x, y=y, symbol=creature.symbol, color=creature.color, creature=creature))

    return GameState(
        placeables=placeables,
        active_encounter=None,
        current_stage=stage,
        biome_order=biome_order,
        run_seed=run_seed,
    )
