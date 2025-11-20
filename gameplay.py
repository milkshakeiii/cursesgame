from typing import Optional

from game_data import *

def advance_step(gamestate: GameState, action: Optional[tuple[int, int]]) -> GameState:
    """Advance the game by one step based on the player action.
    
    Args:
        gamestate: The current game state
        action: A tuple of (dx, dy) representing the player's movement, or None for no action
        
    Returns:
        The updated game state
    """
    if action is None:
        return gamestate

    player = None
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            player = placeable
            break
    if player is None:
        raise ValueError("No player found in gamestate.")
    
    dx, dy = action
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
                    break
    
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
                placeables.append(Terrain(x=x, y=y, symbol=',', color=(50, 150, 50)))
            else:
                placeables.append(Terrain(x=x, y=y, symbol='.', color=(150, 150, 150)))
    
    # Add some encounters on random tiles
    # Place encounters at specific locations for now
    encounter_positions = [
        (10, 10), (15, 12), (30, 8), (20, 15), (35, 18), (8, 20)
    ]
    for x, y in encounter_positions:
        placeables.append(Encounter(x=x, y=y))
    
    return GameState(placeables=placeables, active_encounter=None)
