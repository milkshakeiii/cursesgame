#!/usr/bin/env python3
"""Unit tests for the game."""

import json
from dataclasses import asdict
from unittest.mock import Mock

import pytest
import tcod

from game import DEFAULT_FONT_SIZE, Game
from game_data import (
    GRID_HEIGHT,
    GRID_WIDTH,
    Creature,
    Encounter,
    GameState,
    Player,
    Terrain,
)
from gameplay import advance_step, generate_map
from screens import EncounterScreen, EncounterStartScreen, MainMenu, MapView


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
    convert: int = 0,
) -> Creature:
    """Helper function to create a test creature with common defaults."""
    return Creature(
        name=name,
        symbol=symbol,
        color=color,
        strength=10,
        dexterity=10,
        constitution=10,
        active_abilities=[],
        passive_abilities=[],
        max_health=100,
        current_health=health,
        current_convert=convert,
        level=1,
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
        game = Game()
        assert game.gamestate is not None
        player = get_player(game.gamestate)
        assert player is not None
        assert player.x == GRID_WIDTH // 2
        assert player.y == GRID_HEIGHT // 2
        assert game.running is True

    def test_direction_map_has_all_numpad_keys(self):
        """Test that direction map contains all 8 numpad directions."""
        game = Game()
        assert len(game.map_view.direction_map) == 8

    def test_game_initialization_with_context_and_font(self):
        """Test that a game initializes correctly with context and font path."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        assert game.context == mock_context
        assert game.font_path == font_path
        assert game.font_size == DEFAULT_FONT_SIZE

    def test_toggle_fullscreen_without_context(self):
        """Test that toggle_fullscreen does nothing without context."""
        game = Game()
        # Should not raise an exception
        game.toggle_fullscreen()

    def test_toggle_fullscreen_switches_modes(self):
        """Test toggling between windowed and fullscreen modes."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window

        game = Game(context=mock_context)

        # Toggle to fullscreen
        game.toggle_fullscreen()
        assert mock_window.fullscreen is True

        # Toggle back to windowed
        game.toggle_fullscreen()
        assert mock_window.fullscreen is False

    def test_handle_alt_enter_event(self):
        """Test that Alt+Enter triggers fullscreen toggle."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window

        game = Game(context=mock_context)

        # Create Alt+Enter event
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.RETURN, mod=tcod.event.Modifier.LALT
        )

        game.handle_event(event)

        assert mock_window.fullscreen is True


class TestMapView:
    """Tests for the MapView screen class."""

    def test_mapview_initialization(self):
        """Test that MapView initializes correctly."""
        map_view = MapView()
        assert len(map_view.direction_map) == 8

    def test_mapview_handles_quit_and_escape(self):
        """Test that MapView handles quit events and escape key."""
        map_view = MapView()
        game = Game()

        # Test Quit event
        map_view.handle_event(tcod.event.Quit(), game)
        assert game.running is False

        # Reset and test Escape key
        game.running = True
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.ESCAPE, mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)
        assert game.running is False

    def test_mapview_handles_movement(self):
        """Test that MapView handles movement keys."""
        map_view = MapView()
        game = Game()
        player = get_player(game.gamestate)
        initial_x = player.x

        # Test moving right
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_6, mod=tcod.event.Modifier.NONE
        )
        map_view.handle_event(event, game)

        player = get_player(game.gamestate)
        assert player.x == initial_x + 1
        assert player.y == player.y

    def test_mapview_render(self):
        """Test that MapView renders without errors."""
        map_view = MapView()
        game = Game()
        console = Mock()

        # Should not raise an exception
        map_view.render(console, game)

        # Verify console.print was called (player, borders, etc.)
        assert console.print.called


class TestMainMenu:
    """Tests for the MainMenu screen class."""

    def test_mainmenu_initialization(self):
        """Test that MainMenu initializes correctly."""
        menu = MainMenu()
        assert menu.options == ["New Game", "Options", "Exit"]
        assert menu.selected_index == 0

    def test_mainmenu_handles_quit_and_escape(self):
        """Test that MainMenu handles quit events and escape key."""
        menu = MainMenu()
        game = Game()

        # Test Quit event
        menu.handle_event(tcod.event.Quit(), game)
        assert game.running is False

        # Reset and test Escape key
        game.running = True
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.ESCAPE, mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)
        assert game.running is False

    def test_mainmenu_navigates_down(self):
        """Test that MainMenu navigates down through options."""
        menu = MainMenu()
        game = Game()

        # Initially at index 0
        assert menu.selected_index == 0

        # Press down
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.DOWN, mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)

        assert menu.selected_index == 1

    def test_mainmenu_navigates_up(self):
        """Test that MainMenu navigates up through options."""
        menu = MainMenu()
        game = Game()

        # Initially at index 0
        assert menu.selected_index == 0

        # Press up (should wrap to last option)
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.UP, mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)

        assert menu.selected_index == 2  # Wrapped to "Exit"

    def test_mainmenu_selects_new_game(self):
        """Test that selecting New Game switches to MapView."""
        menu = MainMenu()
        game = Game()

        # Ensure we're on "New Game" (index 0)
        assert menu.selected_index == 0

        # Press enter to select
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.RETURN, mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)

        # Should switch to MapView
        assert game.current_back_screen == game.map_view

    def test_mainmenu_selects_exit(self):
        """Test that selecting Exit quits the game."""
        menu = MainMenu()
        game = Game()

        # Navigate to "Exit" (index 2)
        menu.selected_index = 2

        # Press enter to select
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.RETURN, mod=tcod.event.Modifier.NONE
        )
        menu.handle_event(event, game)

        # Should quit the game
        assert game.running is False

    def test_mainmenu_render(self):
        """Test that MainMenu renders without errors."""
        menu = MainMenu()
        game = Game()
        console = Mock()

        # Should not raise an exception
        menu.render(console, game)

        # Verify console.print was called
        assert console.print.called


class TestScreenIntegration:
    """Tests for screen system integration."""

    def test_game_starts_with_main_menu(self):
        """Test that game starts with MainMenu as current screen."""
        game = Game()
        assert isinstance(game.current_screen(), MainMenu)

    def test_game_has_map_view_screen(self):
        """Test that game has a MapView screen."""
        game = Game()
        assert isinstance(game.map_view, MapView)

    def test_game_delegates_event_to_current_screen(self):
        """Test that game delegates events to current screen."""
        game = Game()

        # Start with MainMenu, select New Game
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.RETURN, mod=tcod.event.Modifier.NONE
        )
        game.handle_event(event)

        # Should now be on MapView
        assert game.current_screen() == game.map_view

    def test_game_delegates_render_to_current_screen(self):
        """Test that game delegates rendering to current screen."""
        game = Game()
        console = Mock()

        # Should delegate to MainMenu (current screen)
        game.render(console)

        # Verify console was used
        assert console.print.called


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
        assert player.x == GRID_WIDTH // 2
        assert player.y == GRID_HEIGHT // 2

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
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creature=creature)
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
        """Test that EncounterStartScreen handles quit events and escape key."""
        screen = EncounterStartScreen()
        game = Game()

        # Test Quit event
        screen.handle_event(tcod.event.Quit(), game)
        assert game.running is False

        # Reset and test Escape key
        game.running = True
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.ESCAPE, mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        assert game.running is False

    def test_encounter_start_screen_continue_to_main(self):
        """Test that pressing Enter or Space continues to main encounter screen."""
        screen = EncounterStartScreen()
        game = Game()
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)

        # Test with Enter key
        game.gamestate.active_encounter = encounter
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.RETURN, mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        assert game.current_back_screen == game.encounter_screen

        # Test with Space key
        game.current_back_screen = game.encounter_start_screen
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.SPACE, mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        assert game.current_back_screen == game.encounter_screen

    def test_encounter_start_screen_render(self):
        """Test that EncounterStartScreen renders without errors."""
        screen = EncounterStartScreen()
        game = Game()
        console = Mock()

        # Should not raise an exception
        screen.render(console, game)

        # Verify console.print was called
        assert console.print.called


class TestEncounterScreen:
    """Tests for the main EncounterScreen class."""

    def test_encounter_screen_initialization(self):
        """Test that EncounterScreen initializes correctly."""
        screen = EncounterScreen()
        assert screen is not None

    def test_encounter_screen_handles_quit_and_escape(self):
        """Test that EncounterScreen handles quit events and escape key."""
        screen = EncounterScreen()
        game = Game()

        # Test Quit event
        screen.handle_event(tcod.event.Quit(), game)
        assert game.running is False

        # Reset and test Escape key
        game.running = True
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.ESCAPE, mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        assert game.running is False

    def test_encounter_screen_flee_returns_to_map(self):
        """Test that pressing F flees and returns to map."""
        screen = EncounterScreen()
        game = Game()
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)

        # Test with F key (Flee)
        game.gamestate.active_encounter = encounter
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.F, mod=tcod.event.Modifier.NONE
        )
        screen.handle_event(event, game)
        assert game.gamestate.active_encounter is None
        assert game.current_back_screen == game.map_view

    def test_encounter_screen_render(self):
        """Test that EncounterScreen renders without errors."""
        screen = EncounterScreen()
        game = Game()
        console = Mock()

        # Should not raise an exception
        screen.render(console, game)

        # Verify console.print was called
        assert console.print.called


class TestMapViewEncounterIntegration:
    """Tests for MapView encounter integration."""

    def test_mapview_switches_to_encounter_screen_on_encounter(self):
        """Test that MapView switches to encounter start screen when encounter is triggered."""
        game = Game()
        map_view = game.map_view

        # Set up gamestate with player and encounter
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creature=creature)
        game.gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_6, mod=tcod.event.Modifier.NONE  # Move right
        )
        map_view.handle_event(event, game)

        # Should have switched to encounter start screen
        assert game.current_back_screen == game.encounter_start_screen
        assert game.gamestate.active_encounter is not None


class TestNewGameFlow:
    """Tests for the complete 'New Game' flow that the user experiences."""

    def test_new_game_has_player_and_terrain(self):
        """Test that after selecting New Game, the game has player and terrain."""
        game = Game()

        # Simulate selecting "New Game"
        game.main_menu._select_option(game)

        # Verify we switched to MapView
        assert isinstance(game.current_screen(), MapView)

        # Verify gamestate has placeables
        assert game.gamestate.placeables is not None
        assert len(game.gamestate.placeables) > 0

        # Verify we have a player
        player_count = sum(1 for p in game.gamestate.placeables if isinstance(p, Player))
        assert player_count == 1, f"Expected 1 player, found {player_count}"

        # Verify we have terrain
        terrain_count = sum(1 for p in game.gamestate.placeables if isinstance(p, Terrain))
        assert terrain_count > 0, f"Expected terrain, found {terrain_count}"

    def test_can_move_after_new_game(self):
        """Test that player can move after selecting New Game."""
        game = Game()

        # Select New Game
        game.main_menu._select_option(game)

        # Get initial player position
        player = None
        for p in game.gamestate.placeables:
            if isinstance(p, Player):
                player = p
                break
        assert player is not None, "No player found after New Game"
        initial_x = player.x

        # Create a movement event (move right)
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_6, mod=tcod.event.Modifier.NONE
        )

        # Handle the event - should not raise an error
        game.current_screen().handle_event(event, game)

        # Verify player moved
        assert (
            player.x == initial_x + 1
        ), f"Player should have moved from {initial_x} to {initial_x + 1}, but is at {player.x}"

    def test_player_and_terrain_render_after_new_game(self):
        """Test that player and terrain actually render to the console after New Game."""
        game = Game()

        # Select New Game
        game.main_menu._select_option(game)

        # Create a real console and render
        console = tcod.console.Console(GRID_WIDTH, GRID_HEIGHT, order="F")
        game.current_screen().render(console, game)

        # Check that player symbol '@' is in the console
        player_found = False
        terrain_found = False

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                ch = console.ch[x, y]
                if ch == ord("@"):
                    player_found = True
                if ch == ord(",") or ch == ord("."):
                    terrain_found = True

        assert player_found, "Player '@' symbol not found in rendered console"
        assert terrain_found, "Terrain symbols not found in rendered console"


class TestAttackAction:
    """Tests for the attack action."""

    def test_attack_reduces_creature_health(self):
        """Test that attack action reduces creature health by 5."""
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform attack on middle position (1, 1)
        result = advance_step(gamestate, ("attack", 1, 1))

        assert creature.current_health == 95

    def test_attack_defeats_creature_at_zero_health(self):
        """Test that creature is removed when health reaches 0."""
        player = Player(10, 10)
        creature = create_test_creature(health=5)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform attack that should defeat creature on middle position (1, 1)
        result = advance_step(gamestate, ("attack", 1, 1))

        assert creature.current_health == 0
        assert result.active_encounter is None
        assert encounter not in result.placeables


class TestConvertAction:
    """Tests for the convert action."""

    def test_convert_increases_convert_value(self):
        """Test that convert action increases convert by 5."""
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform convert on middle position (1, 1)
        result = advance_step(gamestate, ("convert", 1, 1))

        assert creature.current_convert == 5

    def test_convert_adds_creature_to_team_at_100(self):
        """Test that creature is added to team when convert reaches 100."""
        player = Player(10, 10)
        creature = create_test_creature(convert=95)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform convert that should complete conversion on middle position (1, 1)
        result = advance_step(gamestate, ("convert", 1, 1))

        assert creature.current_convert == 100
        assert creature in player.creatures
        assert result.active_encounter is None
        assert encounter not in result.placeables

    def test_convert_caps_at_100(self):
        """Test that convert value doesn't exceed 100."""
        player = Player(10, 10)
        creature = create_test_creature(convert=98)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        setup_enemy_at_position(encounter, creature)  # Middle position
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Perform convert on middle position (1, 1)
        result = advance_step(gamestate, ("convert", 1, 1))

        assert creature.current_convert == 100


class TestEncounterScreenActions:
    """Tests for encounter screen action handling."""

    def test_encounter_screen_has_action_mode(self):
        """Test that EncounterScreen initializes with action_mode."""
        screen = EncounterScreen()
        assert screen.action_mode is None
        assert len(screen.target_selection_map) == 9

    def test_encounter_screen_enter_attack_mode(self):
        """Test that pressing A enters attack mode."""
        screen = EncounterScreen()
        game = Game()

        # Press A
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.A, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.action_mode == "attack"

    def test_encounter_screen_enter_convert_mode(self):
        """Test that pressing C enters convert mode."""
        screen = EncounterScreen()
        game = Game()

        # Press C
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.C, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.action_mode == "convert"

    def test_encounter_screen_cancel_action_with_escape(self):
        """Test that pressing ESC cancels action selection."""
        screen = EncounterScreen()
        game = Game()

        # Enter attack mode
        screen.action_mode = "attack"

        # Press ESC
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.ESCAPE, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.action_mode is None

    def test_encounter_screen_attack_with_numpad(self):
        """Test that numpad selection performs attack."""
        screen = EncounterScreen()
        game = Game()
        
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        # Initialize enemy team with creature in middle position
        setup_enemy_at_position(encounter, creature)  # Middle position
        game.gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Enter attack mode
        screen.action_mode = "attack"

        # Select target with numpad 5 (center)
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_5, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.action_mode is None  # Should exit action mode
        assert creature.current_health == 95  # Should have dealt 5 damage

    def test_encounter_screen_convert_with_numpad(self):
        """Test that numpad selection performs convert."""
        screen = EncounterScreen()
        game = Game()
        
        player = Player(10, 10)
        creature = create_test_creature()
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        setup_enemy_at_position(encounter, creature)  # Middle position
        game.gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Enter convert mode
        screen.action_mode = "convert"

        # Select target with numpad 5 (center)
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_5, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.action_mode is None  # Should exit action mode
        assert creature.current_convert == 5  # Should have increased convert


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
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creature=creature)
        gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        result = advance_step(gamestate, ("move", 1, 0))

        # Check that grids were initialized
        assert result.active_encounter is not None
        assert result.active_encounter.player_team[4] == player  # Player in middle
        assert result.active_encounter.enemy_team[4] == creature  # Enemy in middle

    def test_player_creatures_placed_in_grid(self):
        """Test that player's creatures are placed in the grid."""
        player = Player(10, 10)
        # Add some creatures to player's team
        ally1 = create_test_creature(name="Ally1")
        ally2 = create_test_creature(name="Ally2")
        player.creatures = [ally1, ally2]
        
        creature = create_test_creature()
        encounter = Encounter(11, 10, symbol="#", color=(255, 255, 255), creature=creature)
        gamestate = GameState(placeables=[player, encounter], active_encounter=None)

        # Move player onto encounter
        result = advance_step(gamestate, ("move", 1, 0))

        # Check that player and allies are placed
        assert result.active_encounter.player_team[4] == player  # Player in middle
        assert ally1 in result.active_encounter.player_team
        assert ally2 in result.active_encounter.player_team

    def test_attack_at_different_grid_positions(self):
        """Test that attacks work at different grid positions."""
        player = Player(10, 10)
        creature1 = create_test_creature(name="Enemy1")
        creature2 = create_test_creature(name="Enemy2")
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature1)
        
        # Place enemies at different positions
        encounter.enemy_team = [None] * 9
        encounter.enemy_team[0] = creature1  # Top-left (0, 0)
        encounter.enemy_team[8] = creature2  # Bottom-right (2, 2)
        gamestate = GameState(placeables=[player, encounter], active_encounter=encounter)

        # Attack top-left
        result = advance_step(gamestate, ("attack", 0, 0))
        assert creature1.current_health == 95
        assert creature2.current_health == 100  # Unchanged

        # Attack bottom-right
        result = advance_step(gamestate, ("attack", 2, 2))
        assert creature2.current_health == 95
        assert creature1.current_health == 95  # Unchanged from previous attack

    def test_encounter_ends_when_all_enemies_defeated(self):
        """Test that encounter ends when all enemies are defeated."""
        player = Player(10, 10)
        creature = create_test_creature(health=5)
        encounter = Encounter(10, 10, symbol="#", color=(255, 255, 255), creature=creature)
        
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
        assert screen.selection_mode is None

    def test_encounter_screen_enter_ally_selection_mode(self):
        """Test that pressing Q enters ally selection mode."""
        screen = EncounterScreen()
        game = Game()

        # Press Q
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.Q, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.selection_mode == "selecting_ally"

    def test_encounter_screen_enter_enemy_selection_mode(self):
        """Test that pressing E enters enemy selection mode."""
        screen = EncounterScreen()
        game = Game()

        # Press E
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.E, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.selection_mode == "selecting_enemy"

    def test_selecting_ally_with_numpad(self):
        """Test selecting an ally with numpad."""
        screen = EncounterScreen()
        game = Game()

        # Enter ally selection mode
        screen.selection_mode = "selecting_ally"

        # Press numpad 7 (top-left)
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_7, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.selected_side == "player"
        assert screen.selected_index == 0  # Top-left
        assert screen.selection_mode is None  # Exit selection mode

    def test_selecting_enemy_with_numpad(self):
        """Test selecting an enemy with numpad."""
        screen = EncounterScreen()
        game = Game()

        # Enter enemy selection mode
        screen.selection_mode = "selecting_enemy"

        # Press numpad 3 (bottom-right)
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.KP_3, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.selected_side == "enemy"
        assert screen.selected_index == 8  # Bottom-right
        assert screen.selection_mode is None  # Exit selection mode

    def test_cancel_selection_with_escape(self):
        """Test that ESC cancels selection mode."""
        screen = EncounterScreen()
        game = Game()

        # Enter ally selection mode
        screen.selection_mode = "selecting_ally"

        # Press ESC
        event = tcod.event.KeyDown(
            scancode=0, sym=tcod.event.KeySym.ESCAPE, mod=tcod.event.Modifier.NONE
        )
        screen.handle_specific_event(event, game)

        assert screen.selection_mode is None
