"""Gameplay logic for the curses game."""

from typing import Optional

from game_data import GRID_HEIGHT, GRID_WIDTH, Creature, Encounter, GameState, Player, Terrain


def grid_coords_to_index(x: int, y: int) -> Optional[int]:
    """Convert 2D grid coordinates (0-2, 0-2) to 1D index (0-8).
    
    Args:
        x: Grid x coordinate (0-2)
        y: Grid y coordinate (0-2)
    
    Returns:
        1D index (0-8) or None if coordinates are out of bounds
    """
    if not (0 <= x <= 2 and 0 <= y <= 2):
        return None
    return y * 3 + x


def get_enemy_at_grid_position(encounter: Encounter, target_x: int, target_y: int) -> Optional[Creature]:
    """Get the enemy creature at a grid position if it exists.
    
    Args:
        encounter: The active encounter
        target_x: Grid x coordinate (0-2)
        target_y: Grid y coordinate (0-2)
    
    Returns:
        The Creature at that position, or None if position is invalid or empty
    """
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
    """Advance the game by one step based on the player action.

    Important: all gameplay logic should flow through this function.
    Non-gameplay logic such as UI state should be handled through screens.

    Args:
        gamestate: The current game state
        action: A tuple where the first element is the action type:
                - ("move", dx, dy) for movement
                - ("attack", target_x, target_y) for attacking
                - ("convert", target_x, target_y) for converting
                - None for no action

    Returns:
        The updated game state
    """
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

            # Check if player stepped on an encounter
            for placeable in gamestate.placeables or []:
                if isinstance(placeable, Encounter):
                    if placeable.x == player.x and placeable.y == player.y:
                        gamestate.active_encounter = placeable
                        # Initialize encounter grids
                        # Player team: player in middle (index 4), then player's creatures
                        placeable.player_team = [None] * 9
                        placeable.player_team[4] = player  # Middle position
                        # Place player's creatures around them
                        creature_positions = [0, 1, 2, 3, 5, 6, 7, 8]  # All positions except middle
                        for i, creature in enumerate(player.creatures):
                            if i < len(creature_positions):
                                placeable.player_team[creature_positions[i]] = creature
                        
                        # Enemy team: encounter creature in middle (index 4)
                        placeable.enemy_team = [None] * 9
                        if placeable.creature:
                            placeable.enemy_team[4] = placeable.creature  # Middle position
                        break

    elif action_type == "attack" and gamestate.active_encounter is not None:
        # Attack action during encounter - target_x, target_y are grid coordinates (0-2, 0-2)
        target_x, target_y = action[1], action[2]
        
        # Get the target from enemy team
        target = get_enemy_at_grid_position(gamestate.active_encounter, target_x, target_y)
        if target is not None:
            target.current_health = max(0, target.current_health - 5)
            
            # Check if creature was defeated
            if target.current_health <= 0:
                grid_index = grid_coords_to_index(target_x, target_y)
                gamestate.active_encounter.enemy_team[grid_index] = None
                
                # Check if all enemies defeated
                if all(enemy is None for enemy in gamestate.active_encounter.enemy_team):
                    # Remove the encounter from the map
                    gamestate.placeables = [
                        p for p in gamestate.placeables if p != gamestate.active_encounter
                    ]
                    gamestate.active_encounter = None

    elif action_type == "convert" and gamestate.active_encounter is not None:
        # Convert action during encounter - target_x, target_y are grid coordinates (0-2, 0-2)
        target_x, target_y = action[1], action[2]
        
        # Get the target from enemy team
        target = get_enemy_at_grid_position(gamestate.active_encounter, target_x, target_y)
        if target is not None:
            target.current_convert = min(100, target.current_convert + 5)
            
            # Check if creature was converted
            if target.current_convert >= 100:
                # Add creature to player's team
                player.creatures.append(target)
                # Remove from enemy team
                grid_index = grid_coords_to_index(target_x, target_y)
                gamestate.active_encounter.enemy_team[grid_index] = None
                
                # Check if all enemies defeated/converted
                if all(enemy is None for enemy in gamestate.active_encounter.enemy_team):
                    # Remove the encounter from the map
                    gamestate.placeables = [
                        p for p in gamestate.placeables if p != gamestate.active_encounter
                    ]
                    gamestate.active_encounter = None

    return gamestate


def generate_map() -> GameState:
    """Generate a map with terrain, encounters, and a player.

    Returns:
        A GameState with placeables including terrain, encounters, and player.
    """
    placeables = []

    # Add player at center
    placeables.append(Player(x=GRID_WIDTH // 2, y=GRID_HEIGHT // 2))

    # Add terrain tiles throughout the map
    # Create a pattern of grass (,) and rocky (.) terrain
    for y in range(1, GRID_HEIGHT - 1):
        for x in range(1, GRID_WIDTH - 1):
            # Create a pattern: grass in some areas, rocky in others
            if (x + y) % 3 == 0:
                placeables.append(Terrain(x=x, y=y, symbol=",", color=(50, 150, 50)))
            else:
                placeables.append(Terrain(x=x, y=y, symbol=".", color=(150, 150, 150)))

    # Add some encounters on random tiles
    # Place encounters at specific locations for now
    encounter_positions = [(10, 10), (15, 12), (30, 8), (20, 15), (35, 18), (8, 20)]
    creature_types = [
        ("Goblin", "g", (255, 100, 100)),
        ("Wolf", "w", (200, 200, 255)),
        ("Slime", "s", (100, 255, 100)),
        ("Bat", "b", (150, 150, 255)),
        ("Spider", "p", (200, 100, 200)),
        ("Rat", "r", (150, 150, 150)),
    ]
    for i, (x, y) in enumerate(encounter_positions):
        name, symbol, color = creature_types[i % len(creature_types)]
        creature = Creature(
            name=name,
            symbol=symbol,
            color=color,
            strength=8,
            dexterity=8,
            constitution=8,
            active_abilities=[],
            passive_abilities=[],
            max_health=100,
            current_health=100,
            current_convert=0,
            level=1,
        )
        placeables.append(Encounter(x=x, y=y, symbol="#", color=(255, 255, 255), creature=creature))

    return GameState(placeables=placeables, active_encounter=None)
