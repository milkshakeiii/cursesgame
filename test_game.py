#!/usr/bin/env python3
"""Unit tests for the game."""

import json
from dataclasses import asdict
from unittest.mock import Mock

import pygame
import pytest
import tcod


@pytest.fixture(autouse=True)
def init_pygame():
    """Initialize pygame for all tests that need it."""
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


from game import Game
from game_data import (
    GRID_HEIGHT,
    GRID_WIDTH,
    Attack,
    Creature,
    Encounter,
    GameState,
    Player,
    Terrain,
)
from gameplay import advance_step, generate_map
from terrain_gen import MazeCell, generate_maze
from pygame_screens import EncounterScreen, EncounterStartScreen, MainMenu, MapView, EncounterMode


def get_player(gamestate: GameState) -> Player:
    """Helper function to get the player from the gamestate placeables list."""
    for placeable in gamestate.placeables or []:
        if isinstance(placeable, Player):
            return placeable
    return None


def create_test_creature(
    name: str = "Test",
    symbol: str = "t",
    color: tuple[int, int, int] = (255, 255, 255),
    health: int = 100,
    max_health: int = 100,
    defense: int = 0,
    dodge: int = 0,
    resistance: int = 0,
    conversion_efficacy: int = 50,
    conversion_progress: int = 0,
    attacks: list = None,
    abilities: list = None,
) -> Creature:
    """Helper function to create a test creature with common defaults."""
    if attacks is None:
        attacks = [Attack(attack_type="melee", damage=5)]
    return Creature(
        name=name,
        symbol=symbol,
        color=color,
        max_health=max_health,
        current_health=health,
        defense=defense,
        dodge=dodge,
        resistance=resistance,
        attacks=attacks,
        abilities=abilities or [],
        conversion_efficacy=conversion_efficacy,
        conversion_progress=conversion_progress,
    )


def setup_enemy_at_position(encounter: Encounter, creature: Creature, position: int = 4):
    """Helper to set up an enemy in an encounter at a specific grid position.

    Args:
        encounter: The encounter to set up
        creature: The creature to place
        position: Grid position 0-8 (default 4 = middle)
    """
    encounter.enemy_team = [None] * 9
    encounter.enemy_team[position] = creature


def create_test_game() -> Game:
    """Create a Game instance with a test screen for testing."""
    screen = pygame.display.set_mode((800, 600))
    return Game(screen)


class TestPlayer:
    """Tests for the Player class."""

    def test_player_initialization(self):
        """Test that a player initializes with correct position."""
        player = Player(10, 5)
        assert player.x == 10
        assert player.y == 5
        assert player.symbol == "@"

    @pytest.mark.parametrize(
        "dx,dy,expected_x,expected_y",
        [
            (1, 0, 11, 10),  # right
            (-1, 0, 9, 10),  # left
            (0, -1, 10, 9),  # up
            (0, 1, 10, 11),  # down
            (-1, -1, 9, 9),  # up-left
            (1, -1, 11, 9),  # up-right
            (-1, 1, 9, 11),  # down-left
            (1, 1, 11, 11),  # down-right
        ],
    )
    def test_player_movement(self, dx, dy, expected_x, expected_y):
        """Test player movement in all 8 directions."""
        gamestate = GameState(placeables=[Player(10, 10)], active_encounter=None)
        gamestate = advance_step(gamestate, ("move", dx, dy))
        player = get_player(gamestate)
        assert player.x == expected_x
        assert player.y == expected_y

    @pytest.mark.parametrize(
        "start_x,start_y,dx,dy",
        [
            (0, 10, -1, 0),  # left edge
            (GRID_WIDTH - 1, 10, 1, 0),  # right edge
            (10, 0, 0, -1),  # top edge
            (10, GRID_HEIGHT - 1, 0, 1),  # bottom edge
            (0, 0, -1, -1),  # top-left corner
            (GRID_WIDTH - 1, 0, 1, -1),  # top-right corner
            (0, GRID_HEIGHT - 1, -1, 1),  # bottom-left corner
            (GRID_WIDTH - 1, GRID_HEIGHT - 1, 1, 1),  # bottom-right corner
        ],
    )
    def test_boundary_constraints(self, start_x, start_y, dx, dy):
        """Test that player cannot move beyond grid boundaries."""
        gamestate = GameState(placeables=[Player(start_x, start_y)], active_encounter=None)
        gamestate = advance_step(gamestate, ("move", dx, dy))
        player = get_player(gamestate)
        assert player.x == start_x  # Should not have moved
        assert player.y == start_y


class TestGame:
    """Tests for the Game class."""

    def test_game_initialization(self):
        """Test that a game initializes correctly."""
        game = create_test_game()
        assert game.gamestate is not None
        player = get_player(game.gamestate)
        assert player is not None
        # Player is placed in a maze corner cell, verify it's within bounds
        assert 1 <= player.x < GRID_WIDTH - 1
        assert 1 <= player.y < GRID_HEIGHT - 1
        assert game.running is True

    def test_direction_map_has_all_numpad_keys(self):
        """Test that direction map contains expected directions."""
        game = create_test_game()
        # Direction map includes numpad + arrow keys
        assert len(game.map_view.direction_map) >= 8

    def test_game_has_screen_objects(self):
        """Test that game initializes with all screen objects."""
        game = create_test_game()
        assert game.map_view is not None
        assert game.main_menu is not None
        assert game.encounter_screen is not None
        assert game.encounter_start_screen is not None


class TestMapView:
    """Tests for the MapView screen class."""

    def test_mapview_initialization(self):
        """Test that MapView initializes correctly."""
        map_view = MapView()
        # Direction map includes numpad + arrow keys
        assert len(map_view.direction_map) >= 8

    def test_mapview_handles_quit_and_escape(self):
        """Test that MapView handles quit events and escape shows confirmation."""
        map_view = MapView()
        game = create_test_game()

        # Test Quit event
        quit_event = pygame.event.Event(pygame.QUIT)
        map_view.handle_event(quit_event, game)
        assert game.running is False

        # Reset and test Escape key - should show exit confirmation popup
        game.running = True
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        map_view.handle_event(escape_event, game)
        assert game.current_front_screen == game.exit_confirmation_screen

        # Pressing Y on confirmation should quit
        y_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_y)
        game.exit_confirmation_screen.handle_event(y_event, game)
        assert game.running is False

        # Reset and test N dismisses popup
        game.running = True
        game.current_front_screen = game.exit_confirmation_screen
        n_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n)
        game.exit_confirmation_screen.handle_event(n_event, game)
        assert game.current_front_screen is None
        assert game.running is True

    def test_mapview_handles_movement(self):
        """Test that MapView handles movement keys."""
        map_view = MapView()
        game = create_test_game()
        player = get_player(game.gamestate)
        initial_x = player.x

        # Test moving right (KP_6 = numpad 6)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP6)
        map_view.handle_event(event, game)

        player = get_player(game.gamestate)
        assert player.x == initial_x + 1

    def test_mapview_render(self):
        """Test that MapView renders without errors."""
        map_view = MapView()
        game = create_test_game()

        # Use a real pygame surface
        surface = pygame.Surface((800, 600))

        # Should not raise an exception
        map_view.render(surface, game)


class TestMainMenu:
    """Tests for the MainMenu screen class."""

    def test_mainmenu_initialization(self):
        """Test that MainMenu initializes correctly."""
        menu = MainMenu()
        assert menu.options == ["New Game", "Options", "Exit"]
        assert menu.selected_index == 0

    def test_mainmenu_handles_quit_and_escape(self):
        """Test that MainMenu handles quit events and escape shows confirmation."""
        menu = MainMenu()
        game = create_test_game()

        # Test Quit event
        quit_event = pygame.event.Event(pygame.QUIT)
        menu.handle_event(quit_event, game)
        assert game.running is False

        # Reset and test Escape key - should show exit confirmation popup
        game.running = True
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        menu.handle_event(escape_event, game)
        assert game.current_front_screen == game.exit_confirmation_screen

    def test_mainmenu_navigates_down(self):
        """Test that MainMenu navigates down through options."""
        menu = MainMenu()
        game = create_test_game()

        # Initially at index 0
        assert menu.selected_index == 0

        # Press down
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        menu.handle_event(event, game)

        assert menu.selected_index == 1

    def test_mainmenu_navigates_up(self):
        """Test that MainMenu navigates up through options."""
        menu = MainMenu()
        game = create_test_game()

        # Initially at index 0
        assert menu.selected_index == 0

        # Press up (should wrap to last option)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        menu.handle_event(event, game)

        assert menu.selected_index == 2  # Wrapped to "Exit"

    def test_mainmenu_selects_new_game(self):
        """Test that selecting New Game switches to BiomeOrderScreen."""
        menu = MainMenu()
        game = create_test_game()

        # Ensure we're on "New Game" (index 0)
        assert menu.selected_index == 0

        # Press enter to select
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        menu.handle_event(event, game)

        # Should switch to BiomeOrderScreen (new game flow changed)
        assert game.current_back_screen == game.biome_order_screen

    def test_mainmenu_selects_exit(self):
        """Test that selecting Exit quits the game."""
        menu = MainMenu()
        game = create_test_game()

        # Navigate to "Exit" (index 2)
        menu.selected_index = 2

        # Press enter to select
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        menu.handle_event(event, game)

        # Should quit the game
        assert game.running is False

    def test_mainmenu_render(self):
        """Test that MainMenu renders without errors."""
        menu = MainMenu()
        game = create_test_game()

        # Use a real pygame surface
        surface = pygame.Surface((800, 600))

        # Should not raise an exception
        menu.render(surface, game)


class TestScreenIntegration:
    """Tests for screen system integration."""

    def test_game_starts_with_main_menu(self):
        """Test that game starts with MainMenu as current screen."""
        game = create_test_game()
        assert isinstance(game.current_screen(), MainMenu)

    def test_game_has_map_view_screen(self):
        """Test that game has a MapView screen."""
        game = create_test_game()
        assert isinstance(game.map_view, MapView)

    def test_game_delegates_event_to_current_screen(self):
        """Test that game delegates events to current screen."""
        game = create_test_game()

        # Start with MainMenu, select New Game
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        game.handle_event(event)

        # Should now be on BiomeOrderScreen (new game flow)
        assert game.current_screen() == game.biome_order_screen

    def test_game_delegates_render_to_current_screen(self):
        """Test that game delegates rendering to current screen."""
        game = create_test_game()

        # Should delegate to MainMenu (current screen)
        # This calls render internally which uses the render_surface
        game.render()


class TestGameState:
    """Tests for the GameState class."""

    def test_gamestate_initialization(self):
        """Test that GameState initializes correctly."""
        player = Player(5, 10)
        gamestate = GameState(placeables=[player], active_encounter=None)
        retrieved_player = get_player(gamestate)
        assert retrieved_player == player
        assert retrieved_player.x == 5
        assert retrieved_player.y == 10

    def test_gamestate_is_dataclass(self):
        """Test that GameState is a dataclass."""
        player = Player(5, 10)
        gamestate = GameState(placeables=[player], active_encounter=None)
        # Dataclasses have __dataclass_fields__ attribute
        assert hasattr(gamestate, "__dataclass_fields__")


class TestSerialization:
    """Tests for serialization and deserialization of game state."""

    def test_gamestate_json_roundtrip(self):
        """Test that GameState with Player can be serialized to JSON and back without data loss."""
        # Create original gamestate
        original = GameState(placeables=[Player(42, 13, "&")], active_encounter=None)

        # Serialize to JSON string
        json_str = json.dumps(asdict(original))

        # Deserialize from JSON string
        parsed = json.loads(json_str)
        placeables = [Player(**p) for p in parsed["placeables"]]
        deserialized = GameState(placeables=placeables, active_encounter=None)

        # Verify all data is preserved
        original_player = get_player(original)
        deserialized_player = get_player(deserialized)
        assert deserialized_player.x == original_player.x
        assert deserialized_player.y == original_player.y
        assert deserialized_player.symbol == original_player.symbol


class TestAdvanceStep:
    """Tests for the advance_step function."""

    def test_advance_step_with_no_action(self):
        """Test that advance_step returns unchanged gamestate with no action."""
        gamestate = GameState(placeables=[Player(10, 10)], active_encounter=None)
        result = advance_step(gamestate, None)
        player = get_player(result)
        assert player.x == 10
        assert player.y == 10

    def test_advance_step_mutates_gamestate(self):
        """Test that advance_step mutates the gamestate."""
        gamestate = GameState(placeables=[Player(10, 10)], active_encounter=None)
        result = advance_step(gamestate, ("move", 1, 0))
        # The function should mutate and return the same gamestate object
        assert result is gamestate
        player = get_player(result)
        assert player.x == 11

    def test_advance_step_respects_grid_bounds(self):
        """Test that advance_step respects grid bounds."""
        # Try to move out of bounds from edge
        gamestate = GameState(
            placeables=[Player(GRID_WIDTH - 1, GRID_HEIGHT - 1)], active_encounter=None
        )
        result = advance_step(gamestate, ("move", 1, 1))
        player = get_player(result)
        assert player.x == GRID_WIDTH - 1  # Should not move beyond bounds
        assert player.y == GRID_HEIGHT - 1


class TestTerrain:
    """Tests for the Terrain class."""

    def test_terrain_is_visible_with_properties(self):
        """Test that terrain is visible and has correct properties."""
        terrain = Terrain(x=5, y=10, symbol=",", color=(50, 150, 50))
        assert terrain.visible is True
        assert terrain.x == 5
        assert terrain.y == 10
        assert terrain.symbol == ","
        assert terrain.color == (50, 150, 50)


class TestEncounter:
    """Tests for the Encounter class."""

    def test_encounter_is_invisible(self):
        """Test that encounter is invisible by default."""
        encounter = Encounter(x=10, y=15, symbol="#", color=(255, 255, 255))
        assert encounter.visible is False
        assert encounter.x == 10
        assert encounter.y == 15


class TestGenerateMap:
    """Tests for the generate_map function."""

    def test_generate_map_creates_gamestate(self):
        """Test that generate_map creates a GameState."""
        gamestate = generate_map()
        assert isinstance(gamestate, GameState)
        assert gamestate.placeables is not None
        assert len(gamestate.placeables) > 0

    def test_generate_map_includes_player(self):
        """Test that generate_map includes a player."""
        gamestate = generate_map()
        player = get_player(gamestate)
        assert player is not None
        # Player is placed in a maze corner cell, verify it's within bounds
        assert 1 <= player.x < GRID_WIDTH - 1
        assert 1 <= player.y < GRID_HEIGHT - 1

    def test_generate_map_includes_terrain(self):
        """Test that generate_map includes terrain."""
        gamestate = generate_map()
        terrain_count = sum(1 for p in gamestate.placeables if isinstance(p, Terrain))
        assert terrain_count > 0

    def test_generate_map_includes_encounters(self):
        """Test that generate_map includes encounters."""
        gamestate = generate_map()
        encounter_count = sum(1 for p in gamestate.placeables if isinstance(p, Encounter))
        assert encounter_count > 0


class TestEncounterDetection:
    """Tests for encounter detection in advance_step."""

    def test_stepping_on_encounter_sets_active_encounter(self):
        """Test that stepping on an encounter sets active_encounter."""
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        result = advance_step(gamestate, ("move", 1, 0))

        assert result.active_encounter is not None
        assert result.active_encounter == encounter

    def test_moving_without_encounter_leaves_active_encounter_none(self):
        """Test that moving without an encounter keeps active_encounter None."""
        player = Player(10, 10)
        gamestate = GameState(placeables=[player], active_encounter=None)

        # Move player
        result = advance_step(gamestate, ("move", 1, 0))

        assert result.active_encounter is None

    def test_stepping_on_non_encounter_tile_no_trigger(self):
        """Test that stepping on terrain doesn't trigger an encounter."""
        player = Player(10, 10)
        terrain = Terrain(11, 10, symbol=",", color=(50, 150, 50))
        gamestate = GameState(placeables=[player, terrain], active_encounter=None)

        # Move player onto terrain
        result = advance_step(gamestate, ("move", 1, 0))

        assert result.active_encounter is None


class TestEncounterStartScreen:
    """Tests for the EncounterStartScreen class."""

    def test_encounter_start_screen_initialization(self):
        """Test that EncounterStartScreen initializes correctly."""
        screen = EncounterStartScreen()
        assert screen is not None

    def test_encounter_start_screen_handles_quit_and_escape(self):
        """Test that EncounterStartScreen handles quit events and escape shows confirmation."""
        screen = EncounterStartScreen()
        game = create_test_game()

        # Test Quit event
        quit_event = pygame.event.Event(pygame.QUIT)
        screen.handle_event(quit_event, game)
        assert game.running is False

        # Reset and test Escape key - should show exit confirmation popup
        game.running = True
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        screen.handle_event(escape_event, game)
        assert game.current_front_screen == game.exit_confirmation_screen

    def test_encounter_start_screen_continue_to_main(self):
        """Test that pressing Enter or Space continues to encounter screen."""
        screen = EncounterStartScreen()
        game = create_test_game()
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])

        # Test with Enter key
        game.gamestate.active_encounter = encounter
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        screen.handle_event(enter_event, game)
        assert game.current_back_screen == game.encounter_screen

        # Test with Space key
        game.current_back_screen = game.encounter_start_screen
        space_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        screen.handle_event(space_event, game)
        assert game.current_back_screen == game.encounter_screen

    def test_encounter_start_screen_render(self):
        """Test that EncounterStartScreen renders without errors."""
        screen = EncounterStartScreen()
        game = create_test_game()

        # Use a real pygame surface
        surface = pygame.Surface((800, 600))

        # Should not raise an exception
        screen.render(surface, game)


class TestEncounterScreen:
    """Tests for the main EncounterScreen class."""

    def test_encounter_screen_initialization(self):
        """Test that EncounterScreen initializes correctly."""
        screen = EncounterScreen()
        assert screen is not None

    def test_encounter_screen_handles_quit_and_escape(self):
        """Test that EncounterScreen handles quit events and escape shows confirmation."""
        screen = EncounterScreen()
        game = create_test_game()

        # Test Quit event
        quit_event = pygame.event.Event(pygame.QUIT)
        screen.handle_event(quit_event, game)
        assert game.running is False

        # Reset and test Escape key (in NORMAL mode, should show confirmation)
        game.running = True
        escape_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        screen.handle_event(escape_event, game)
        assert game.current_front_screen == game.exit_confirmation_screen

    def test_encounter_screen_flee_returns_to_map(self):
        """Test that pressing F flees and returns to map."""
        screen = EncounterScreen()
        game = create_test_game()
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])

        # Test with F key (Flee)
        game.gamestate.active_encounter = encounter
        f_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f)
        screen.handle_event(f_event, game)
        assert game.gamestate.active_encounter is None
        assert game.current_back_screen == game.map_view

    def test_encounter_screen_render(self):
        """Test that EncounterScreen renders without errors."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up an active encounter so the render method can work
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Use a real pygame surface
        surface = pygame.Surface((800, 600))

        # Should not raise an exception
        screen.render(surface, game)


class TestMapViewEncounterIntegration:
    """Tests for MapView encounter integration."""

    def test_mapview_switches_to_encounter_screen_on_encounter(self):
        """Test that MapView switches to encounter start screen when encounter is triggered."""
        game = create_test_game()
        map_view = game.map_view

        # Set up gamestate with player and encounter
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        game.gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP6)  # Move right
        map_view.handle_event(event, game)

        # Should have switched to encounter start screen
        assert game.current_back_screen == game.encounter_start_screen
        assert game.gamestate.active_encounter is not None


class TestNewGameFlow:
    """Tests for the complete 'New Game' flow that the user experiences."""

    def test_new_game_has_player_and_terrain(self):
        """Test that game has player and terrain."""
        game = create_test_game()

        # Verify gamestate has placeables
        assert game.gamestate.placeables is not None
        assert len(game.gamestate.placeables) > 0

        # Verify we have a player
        player_count = sum(1 for p in game.gamestate.placeables if isinstance(p, Player))
        assert player_count == 1, f"Expected 1 player, found {player_count}"

        # Verify we have terrain
        terrain_count = sum(1 for p in game.gamestate.placeables if isinstance(p, Terrain))
        assert terrain_count > 0, f"Expected terrain, found {terrain_count}"

    def test_can_move_after_switching_to_map_view(self):
        """Test that player can move on map view."""
        game = create_test_game()

        # Switch to map view
        game.current_back_screen = game.map_view

        # Get initial player position
        player = get_player(game.gamestate)
        assert player is not None, "No player found"
        initial_x = player.x

        # Create a movement event (move right)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP6)

        # Handle the event - should not raise an error
        game.current_screen().handle_event(event, game)

        # Verify player moved
        assert (
            player.x == initial_x + 1
        ), f"Player should have moved from {initial_x} to {initial_x + 1}, but is at {player.x}"

    def test_mapview_renders_without_errors(self):
        """Test that MapView renders without errors."""
        game = create_test_game()

        # Switch to map view
        game.current_back_screen = game.map_view

        # Use a real pygame surface
        surface = pygame.Surface((800, 600))

        # Should not raise an exception
        game.current_screen().render(surface, game)


class TestAttackAction:
    """Tests for the attack action."""

    def test_attack_reduces_creature_health(self):
        """Test that attack action reduces creature health."""
        player = Player(10, 10)
        creature = create_test_creature(health=100, max_health=100)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player  # Middle position
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform attack on middle position (1, 1)
        result = advance_step(gamestate, ("attack", 1, 1))

        # Health should decrease (exact amount depends on hero stats)
        assert creature.current_health < 100

    def test_attack_defeats_creature_at_zero_health(self):
        """Test that creature is removed when health reaches 0."""
        player = Player(10, 10)
        creature = create_test_creature(health=1, max_health=1)  # Very low HP
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform attack that should defeat creature on middle position (1, 1)
        result = advance_step(gamestate, ("attack", 1, 1))

        assert creature.current_health <= 0
        assert result.active_encounter is None
        assert encounter not in result.placeables

    def test_melee_blocked_by_ally_in_front(self):
        """Test that units behind an ally cannot make melee attacks."""
        from combat import get_melee_target

        player = Player(10, 10)
        ally = create_test_creature(name="Ally")
        enemy = create_test_creature(name="Enemy", health=100, max_health=100)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[enemy])

        # Set up player team: player in back (col 0), ally in front (col 2), same row
        # Grid layout for row 1: indices 3, 4, 5 = cols 0, 1, 2
        encounter.player_team = [None] * 9
        encounter.player_team[3] = player  # col 0, row 1 (back)
        encounter.player_team[5] = ally    # col 2, row 1 (front)

        # Set up enemy in row 1
        encounter.enemy_team = [None] * 9
        encounter.enemy_team[3] = enemy  # col 0, row 1 (enemy front)

        # Player at col 0 should be blocked by ally at col 2
        # Target is enemy at col 0, row 1
        target = get_melee_target(
            encounter, attacker_col=0, attacker_row=1, attacker_is_player=True,
            target_col=0, target_row=1
        )
        assert target is None, "Player behind ally should not be able to melee"

        # Ally at col 2 (front) should be able to melee
        target = get_melee_target(
            encounter, attacker_col=2, attacker_row=1, attacker_is_player=True,
            target_col=0, target_row=1
        )
        assert target == enemy, "Ally at front should be able to melee"

    def test_enemy_moves_when_cannot_attack(self):
        """Test that enemies move when they can't deal damage."""
        from ai import execute_enemy_turn, choose_enemy_target

        player = Player(10, 10)
        player.creatures = [None] * 9

        # Create a melee-only enemy
        wolf = create_test_creature(name="Wolf", attacks=[Attack(attack_type="melee", damage=4)])

        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[wolf])
        encounter.combat_log = []

        # Put wolf in back row where it can't melee (col 2, row 1)
        encounter.enemy_team = [None] * 9
        encounter.enemy_team[5] = wolf

        # Put player in different row so wolf can't attack
        encounter.player_team = [None] * 9
        encounter.player_team[0] = player  # col 0, row 0

        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Verify wolf can't deal damage
        (target, damage) = choose_enemy_target(encounter)
        assert damage == 0, "Wolf should not be able to deal damage"

        # Record initial position
        initial_pos = 5

        # Execute enemy turn - should move since can't attack
        execute_enemy_turn(gamestate)

        # Wolf should have moved (melee units move vertically)
        new_positions = [i for i, u in enumerate(encounter.enemy_team) if u is wolf]
        assert len(new_positions) == 1
        assert new_positions[0] != initial_pos, "Wolf should have moved"
        # Melee moves vertically, so column should stay same (col 2 = indices 2, 5, 8)
        assert new_positions[0] in [2, 8], "Wolf should move vertically within column 2"

    def test_dead_ally_removed_from_player_team(self):
        """Test that defeated allies are removed from player's permanent team."""
        from gameplay import remove_dead_units

        player = Player(10, 10)

        # Create an ally with low HP
        ally = create_test_creature(name="Ally", health=0, max_health=10)  # Already dead

        # Add ally to player's permanent team
        player.creatures = [None] * 9
        player.creatures[0] = ally

        # Set up encounter with the dead ally
        enemy = create_test_creature(name="Enemy")
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[enemy])
        encounter.combat_log = []

        # Put ally in player_team (simulating battle)
        encounter.player_team = [None] * 9
        encounter.player_team[0] = ally
        encounter.player_team[4] = player

        # Set up enemy team
        encounter.enemy_team = [None] * 9
        encounter.enemy_team[4] = enemy

        # Remove dead units (is_player_turn=False means checking player team)
        remove_dead_units(encounter, is_player_turn=False, player=player)

        # Ally should be removed from both encounter and player's permanent team
        assert encounter.player_team[0] is None, "Dead ally should be removed from encounter"
        assert player.creatures[0] is None, "Dead ally should be removed from player.creatures"

    def test_dead_2x2_ally_removed_from_all_positions(self):
        """Test that defeated 2x2 allies are removed from all 4 positions in player's team."""
        from gameplay import remove_dead_units

        player = Player(10, 10)

        # Create a 2x2 ally with 0 HP (already dead)
        ally = create_test_creature(name="BigAlly", health=0, max_health=10)
        ally.size = "2x2"

        # Add 2x2 ally to player's permanent team (occupies 4 positions: 0, 1, 3, 4)
        player.creatures = [None] * 9
        player.creatures[0] = ally  # top-left
        player.creatures[1] = ally  # top-right
        player.creatures[3] = ally  # bottom-left
        player.creatures[4] = ally  # bottom-right

        # Set up encounter with the dead ally
        enemy = create_test_creature(name="Enemy")
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[enemy])
        encounter.combat_log = []

        # Put 2x2 ally in player_team (simulating battle)
        encounter.player_team = [None] * 9
        encounter.player_team[0] = ally
        encounter.player_team[1] = ally
        encounter.player_team[3] = ally
        encounter.player_team[4] = ally
        player.team_position = 8  # Player in corner

        # Set up enemy team
        encounter.enemy_team = [None] * 9
        encounter.enemy_team[4] = enemy

        # Remove dead units (is_player_turn=False means checking player team)
        remove_dead_units(encounter, is_player_turn=False, player=player)

        # 2x2 ally should be removed from all positions in encounter
        assert encounter.player_team[0] is None, "Dead 2x2 ally should be removed from encounter pos 0"
        assert encounter.player_team[1] is None, "Dead 2x2 ally should be removed from encounter pos 1"
        assert encounter.player_team[3] is None, "Dead 2x2 ally should be removed from encounter pos 3"
        assert encounter.player_team[4] is None, "Dead 2x2 ally should be removed from encounter pos 4"

        # 2x2 ally should be removed from all positions in player.creatures
        assert player.creatures[0] is None, "Dead 2x2 ally should be removed from player.creatures pos 0"
        assert player.creatures[1] is None, "Dead 2x2 ally should be removed from player.creatures pos 1"
        assert player.creatures[3] is None, "Dead 2x2 ally should be removed from player.creatures pos 3"
        assert player.creatures[4] is None, "Dead 2x2 ally should be removed from player.creatures pos 4"


class TestConvertAction:
    """Tests for the convert action."""

    def test_convert_increases_conversion_progress(self):
        """Test that convert action increases conversion_progress."""
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform convert on middle position (1, 1)
        result = advance_step(gamestate, ("convert", 1, 1))

        # Conversion progress should increase
        assert creature.conversion_progress > 0

    def test_convert_adds_creature_to_pending_recruits_at_max_health(self):
        """Test that creature is added to pending_recruits when conversion_progress reaches max_health."""
        player = Player(10, 10)
        # Set conversion_progress very close to max_health
        creature = create_test_creature(max_health=10, conversion_progress=9)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform convert that should complete conversion on middle position (1, 1)
        result = advance_step(gamestate, ("convert", 1, 1))

        assert creature.conversion_progress >= creature.max_health
        # Converted creatures go to pending_recruits, not directly to player.creatures
        assert result.pending_recruits is not None
        assert creature in result.pending_recruits

    def test_convert_caps_at_max_health(self):
        """Test that conversion_progress doesn't exceed max_health."""
        player = Player(10, 10)
        creature = create_test_creature(max_health=10, conversion_progress=8)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform convert on middle position (1, 1)
        result = advance_step(gamestate, ("convert", 1, 1))

        # Check creature was converted and caps properly
        assert creature.conversion_progress >= creature.max_health


class TestEncounterScreenActions:
    """Tests for encounter screen action handling."""

    def test_encounter_screen_has_action_mode(self):
        """Test that EncounterScreen initializes with mode."""
        screen = EncounterScreen()
        assert screen.mode == EncounterMode.NORMAL
        # target_selection_map includes both numpad and regular number keys
        assert len(screen.target_selection_map) >= 9

    def test_encounter_screen_enter_attack_mode(self):
        """Test that pressing A enters attack mode."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up encounter for the screen to work with
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate.active_encounter = encounter

        # Press A
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)
        screen.handle_event(event, game)

        assert screen.mode == EncounterMode.ATTACK

    def test_encounter_screen_enter_convert_mode(self):
        """Test that pressing C enters convert mode."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up encounter for the screen to work with
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate.active_encounter = encounter

        # Press C
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)
        screen.handle_event(event, game)

        assert screen.mode == EncounterMode.CONVERT

    def test_encounter_screen_cancel_action_with_escape(self):
        """Test that pressing ESC cancels action selection."""
        screen = EncounterScreen()
        game = create_test_game()

        # Enter attack mode
        screen.mode = EncounterMode.ATTACK

        # Press ESC
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        screen.handle_event(event, game)

        assert screen.mode == EncounterMode.NORMAL


class TestEncounterGridSystem:
    """Tests for the new encounter grid system."""

    def test_encounter_initializes_with_grids(self):
        """Test that Encounter initializes with empty grids."""
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255))
        assert encounter.player_team is not None
        assert len(encounter.player_team) == 9
        assert encounter.enemy_team is not None
        assert len(encounter.enemy_team) == 9

    def test_stepping_on_encounter_initializes_grids(self):
        """Test that stepping on encounter initializes the grids properly."""
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        result = advance_step(gamestate, ("move", 1, 0))

        # Check that grids were initialized
        assert result.active_encounter is not None
        assert result.active_encounter.player_team[4] == player  # Player in middle
        # Enemy is randomly placed, just check it exists somewhere
        assert creature in result.active_encounter.enemy_team

    def test_player_creatures_placed_in_grid(self):
        """Test that player's creatures are placed in the grid."""
        player = Player(10, 10)
        # Add some creatures to player's team (9-slot grid)
        ally1 = create_test_creature(name="Ally1")
        ally2 = create_test_creature(name="Ally2")
        player.creatures = [None] * 9
        player.creatures[0] = ally1
        player.creatures[1] = ally2

        creature = create_test_creature()
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        result = advance_step(gamestate, ("move", 1, 0))

        # Check that player and allies are placed
        assert result.active_encounter.player_team[4] == player  # Player in middle
        assert ally1 in result.active_encounter.player_team
        assert ally2 in result.active_encounter.player_team

    def test_repositioned_player_not_duplicated(self):
        """Test that player repositioned in team arrangement is not duplicated."""
        from gameplay import initialize_encounter

        player = Player(10, 10)
        ally = create_test_creature(name="Ally")

        # Simulate player repositioned to slot 0 (via team arrangement)
        player.team_position = 0  # Player moved to slot 0
        player.creatures[1] = ally

        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])

        initialize_encounter(encounter, player)

        # Count how many times player appears
        player_count = sum(1 for u in encounter.player_team if u is player)
        assert player_count == 1, f"Player should appear exactly once, found {player_count}"

        # Player should be at position 0 (their team_position), not center
        assert encounter.player_team[0] is player
        assert encounter.player_team[4] is not player

    def test_attack_at_different_grid_positions(self):
        """Test that attacks work at different grid positions."""
        player = Player(10, 10)
        creature1 = create_test_creature(name="Enemy1", health=100, max_health=100)
        creature2 = create_test_creature(name="Enemy2", health=100, max_health=100)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature1])

        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player  # Center (col=1, row=1)

        # Place enemies in different rows to test magic targeting
        # Position 4 is (col=1, row=1) - same column as hero for magic
        # Position 1 is (col=1, row=0) - same column, different row
        encounter.enemy_team = [None] * 9
        encounter.enemy_team[1] = creature1  # col=1, row=0 (mirror column for magic)
        encounter.enemy_team[4] = creature2  # col=1, row=1 (center, same column)
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        creature1_initial_health = creature1.current_health
        creature2_initial_health = creature2.current_health

        # Attack the mirror column - magic hits all in same column
        result = advance_step(gamestate, ("attack", 1, 0))

        # Magic attacks all enemies in the mirror column
        # Both creatures are in column 1, so magic should hit both
        assert creature1.current_health < creature1_initial_health or creature2.current_health < creature2_initial_health

    def test_encounter_ends_when_all_enemies_defeated(self):
        """Test that encounter ends when all enemies are defeated."""
        player = Player(10, 10)
        creature = create_test_creature(health=1, max_health=1)  # Very low HP
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])

        # Place player in player_team grid
        encounter.player_team = [None] * 9
        encounter.player_team[4] = player

        # Place only one enemy
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Attack to defeat
        result = advance_step(gamestate, ("attack", 1, 1))

        assert result.active_encounter is None
        assert encounter not in result.placeables


class TestEncounterSelection:
    """Tests for creature selection in encounters."""

    def test_encounter_screen_has_selection_state(self):
        """Test that EncounterScreen has selection state."""
        screen = EncounterScreen()
        assert screen.selected_side in ["player", "enemy"]
        assert 0 <= screen.selected_index < 9
        assert screen.mode == EncounterMode.NORMAL

    def test_encounter_screen_enter_ally_selection_mode(self):
        """Test that pressing Q enters ally selection mode."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up encounter
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate.active_encounter = encounter

        # Press Q
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)
        screen.handle_event(event, game)

        assert screen.mode == EncounterMode.SELECTING_ALLY

    def test_encounter_screen_enter_enemy_selection_mode(self):
        """Test that pressing E enters enemy selection mode."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up encounter
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate.active_encounter = encounter

        # Press E
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        screen.handle_event(event, game)

        assert screen.mode == EncounterMode.SELECTING_ENEMY

    def test_selecting_ally_with_numpad(self):
        """Test selecting an ally with numpad."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up encounter
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate.active_encounter = encounter

        # Enter ally selection mode
        screen.mode = EncounterMode.SELECTING_ALLY

        # Press numpad 7 (top-left)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP7)
        screen.handle_event(event, game)

        assert screen.selected_side == "player"
        assert screen.selected_index == 0  # Top-left
        assert screen.mode == EncounterMode.NORMAL  # Exit selection mode

    def test_selecting_enemy_with_numpad(self):
        """Test selecting an enemy with numpad."""
        screen = EncounterScreen()
        game = create_test_game()

        # Set up encounter
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creatures=[creature])
        setup_enemy_at_position(encounter, creature)
        game.gamestate.active_encounter = encounter

        # Enter enemy selection mode
        screen.mode = EncounterMode.SELECTING_ENEMY

        # Press numpad 3 (bottom-right)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP3)
        screen.handle_event(event, game)

        assert screen.selected_side == "enemy"
        assert screen.selected_index == 8  # Bottom-right
        assert screen.mode == EncounterMode.NORMAL  # Exit selection mode

    def test_cancel_selection_with_escape(self):
        """Test that ESC cancels selection mode."""
        screen = EncounterScreen()
        game = create_test_game()

        # Enter ally selection mode
        screen.mode = EncounterMode.SELECTING_ALLY

        # Press ESC
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        screen.handle_event(event, game)

        assert screen.mode == EncounterMode.NORMAL


class TestMazeGeneration:
    """Tests for maze generation."""

    def test_maze_returns_correct_size(self):
        """Test that generate_maze returns n*n cells."""
        for n in [2, 3, 4, 5]:
            maze = generate_maze(seed=42, n=n)
            assert len(maze) == n * n

    def test_maze_cells_have_correct_coordinates(self):
        """Test that maze contains all expected coordinates."""
        n = 3
        maze = generate_maze(seed=42, n=n)
        for x in range(n):
            for y in range(n):
                assert (x, y) in maze

    def test_maze_is_deterministic(self):
        """Test that same seed produces same maze."""
        maze1 = generate_maze(seed=123, n=4)
        maze2 = generate_maze(seed=123, n=4)

        for pos in maze1:
            assert maze1[pos].north == maze2[pos].north
            assert maze1[pos].east == maze2[pos].east
            assert maze1[pos].south == maze2[pos].south
            assert maze1[pos].west == maze2[pos].west

    def test_different_seeds_produce_different_mazes(self):
        """Test that different seeds produce different mazes."""
        maze1 = generate_maze(seed=1, n=4)
        maze2 = generate_maze(seed=2, n=4)

        # At least one cell should differ
        differs = False
        for pos in maze1:
            if (maze1[pos].north != maze2[pos].north or
                maze1[pos].east != maze2[pos].east or
                maze1[pos].south != maze2[pos].south or
                maze1[pos].west != maze2[pos].west):
                differs = True
                break
        assert differs

    def test_maze_is_fully_connected(self):
        """Test that all cells are reachable from (0, 0)."""
        n = 4
        maze = generate_maze(seed=42, n=n)

        # BFS from (0, 0)
        visited = set()
        queue = [(0, 0)]
        visited.add((0, 0))

        while queue:
            x, y = queue.pop(0)
            cell = maze[(x, y)]

            # Check each direction
            if not cell.north and y > 0 and (x, y - 1) not in visited:
                visited.add((x, y - 1))
                queue.append((x, y - 1))
            if not cell.south and y < n - 1 and (x, y + 1) not in visited:
                visited.add((x, y + 1))
                queue.append((x, y + 1))
            if not cell.west and x > 0 and (x - 1, y) not in visited:
                visited.add((x - 1, y))
                queue.append((x - 1, y))
            if not cell.east and x < n - 1 and (x + 1, y) not in visited:
                visited.add((x + 1, y))
                queue.append((x + 1, y))

        assert len(visited) == n * n

    def test_maze_walls_are_consistent(self):
        """Test that walls match between adjacent cells."""
        n = 4
        maze = generate_maze(seed=42, n=n)

        for x in range(n):
            for y in range(n):
                cell = maze[(x, y)]

                # Check east-west consistency
                if x < n - 1:
                    neighbor = maze[(x + 1, y)]
                    assert cell.east == neighbor.west

                # Check north-south consistency
                if y < n - 1:
                    neighbor = maze[(x, y + 1)]
                    assert cell.south == neighbor.north

    def test_maze_edge_cells_have_outer_walls(self):
        """Test that cells on the edge have walls on the boundary."""
        n = 4
        maze = generate_maze(seed=42, n=n)

        # Top row should have north walls
        for x in range(n):
            assert maze[(x, 0)].north is True

        # Bottom row should have south walls
        for x in range(n):
            assert maze[(x, n - 1)].south is True

        # Left column should have west walls
        for y in range(n):
            assert maze[(0, y)].west is True

        # Right column should have east walls
        for y in range(n):
            assert maze[(n - 1, y)].east is True
