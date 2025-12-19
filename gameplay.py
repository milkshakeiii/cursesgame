"""Gameplay logic for the curses game."""

from typing import Optional
import random

from game_data import GRID_HEIGHT, GRID_WIDTH, Creature, Encounter, Exit, GameState, Player, Terrain
from terrain_gen import generate_biome_terrain

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
        "monsters": [("Goblin", "g", (100, 200, 100)), ("Wolf", "w", (150, 150, 150)), ("Spider", "s", (50, 50, 50))]
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
        "monsters": [("Lion", "L", (255, 215, 0)), ("Eagle", "E", (255, 255, 255)), ("Bandit", "B", (100, 100, 255))]
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
        "monsters": [("Yeti", "Y", (255, 255, 255)), ("Ice Wolf", "w", (200, 255, 255)), ("Frost Giant", "F", (100, 200, 255))]
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
        "monsters": [("Slime", "S", (0, 255, 0)), ("Bat", "b", (100, 100, 100)), ("Skeleton", "k", (200, 200, 200))]
    }
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
        target = get_enemy_at_grid_position(gamestate.active_encounter, target_x, target_y)
        if target is not None:
            target.current_health = max(0, target.current_health - 5)
            
            if target.current_health <= 0:
                grid_index = grid_coords_to_index(target_x, target_y)
                gamestate.active_encounter.enemy_team[grid_index] = None
                
                if all(enemy is None for enemy in gamestate.active_encounter.enemy_team):
                    gamestate.placeables = [
                        p for p in gamestate.placeables if p != gamestate.active_encounter
                    ]
                    gamestate.active_encounter = None
                    
                    # Boss Win Condition
                    if gamestate.current_stage == gamestate.max_stages:
                        gamestate.status = "won"

    elif action_type == "convert" and gamestate.active_encounter is not None:
        target_x, target_y = action[1], action[2]
        target = get_enemy_at_grid_position(gamestate.active_encounter, target_x, target_y)
        if target is not None:
            target.current_convert = min(100, target.current_convert + 5)
            
            if target.current_convert >= 100:
                # Add to pending recruits
                if gamestate.pending_recruits is None:
                    gamestate.pending_recruits = []
                gamestate.pending_recruits.append(target)
                
                grid_index = grid_coords_to_index(target_x, target_y)
                gamestate.active_encounter.enemy_team[grid_index] = None
                
                if all(enemy is None for enemy in gamestate.active_encounter.enemy_team):
                    gamestate.placeables = [
                        p for p in gamestate.placeables if p != gamestate.active_encounter
                    ]
                    gamestate.active_encounter = None
                    
                    # Boss Win Condition (if you convert the boss, you win!)
                    if gamestate.current_stage == gamestate.max_stages:
                        gamestate.status = "won"

    return gamestate


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
    monster_list = biome_info["monsters"]

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
        # Boss Level
        boss = Creature(
            name="Dragon King", symbol="D", color=(255, 0, 0),
            strength=20, dexterity=15, constitution=20,
            active_abilities=[], passive_abilities=[],
            max_health=500, current_health=500,
            current_convert=0, level=20
        )
        # Place boss
        placeables.append(Encounter(x=GRID_WIDTH - 10, y=GRID_HEIGHT // 2, symbol="D", color=(255, 0, 0), creature=boss))
    else:
        # Standard Level
        # Place Exit
        placeables.append(Exit(x=GRID_WIDTH - 2, y=GRID_HEIGHT // 2, symbol=">", color=(255, 255, 255), visible=True))

        # Encounters
        encounter_positions = [(10, 10), (15, 12), (30, 8), (20, 15), (35, 18), (8, 20)]
        
        # Simple randomization: shift positions based on stage to make levels look slightly different
        for i, (base_x, base_y) in enumerate(encounter_positions):
            # rudimentary procedural generation variation
            x = (base_x + stage * 3) % (GRID_WIDTH - 2) + 1
            y = (base_y + stage * 2) % (GRID_HEIGHT - 2) + 1
            
            # Ensure not on player start or exit
            if abs(x - player.x) < 2 and abs(y - player.y) < 2: continue
            if x == GRID_WIDTH - 2 and y == GRID_HEIGHT // 2: continue

            name, symbol, color = monster_list[(i + stage) % len(monster_list)]
            creature = Creature(
                name=name, symbol=symbol, color=color,
                strength=8, dexterity=8, constitution=8,
                active_abilities=[], passive_abilities=[],
                max_health=100, current_health=100,
                current_convert=0, level=stage, 
            )
            placeables.append(Encounter(x=x, y=y, symbol="#", color=(255, 255, 255), creature=creature))

    return GameState(
        placeables=placeables,
        active_encounter=None,
        current_stage=stage,
        biome_order=biome_order,
        run_seed=run_seed,
    )
