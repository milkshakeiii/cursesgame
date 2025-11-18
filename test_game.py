#!/usr/bin/env python3
"""Unit tests for the game."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from game import Player, Game, GRID_WIDTH, GRID_HEIGHT, DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE, FONT_SIZE_INCREMENT
import tcod.event


class TestPlayer:
    """Tests for the Player class."""
    
    def test_player_initialization(self):
        """Test that a player initializes with correct position."""
        player = Player(10, 5)
        assert player.x == 10
        assert player.y == 5
        assert player.symbol == '@'
    
    def test_move_right(self):
        """Test moving right."""
        player = Player(10, 10)
        result = player.move(1, 0)
        assert result is True
        assert player.x == 11
        assert player.y == 10
    
    def test_move_left(self):
        """Test moving left."""
        player = Player(10, 10)
        result = player.move(-1, 0)
        assert result is True
        assert player.x == 9
        assert player.y == 10
    
    def test_move_up(self):
        """Test moving up."""
        player = Player(10, 10)
        result = player.move(0, -1)
        assert result is True
        assert player.x == 10
        assert player.y == 9
    
    def test_move_down(self):
        """Test moving down."""
        player = Player(10, 10)
        result = player.move(0, 1)
        assert result is True
        assert player.x == 10
        assert player.y == 11
    
    def test_move_upleft(self):
        """Test moving diagonally up-left."""
        player = Player(10, 10)
        result = player.move(-1, -1)
        assert result is True
        assert player.x == 9
        assert player.y == 9
    
    def test_move_upright(self):
        """Test moving diagonally up-right."""
        player = Player(10, 10)
        result = player.move(1, -1)
        assert result is True
        assert player.x == 11
        assert player.y == 9
    
    def test_move_downleft(self):
        """Test moving diagonally down-left."""
        player = Player(10, 10)
        result = player.move(-1, 1)
        assert result is True
        assert player.x == 9
        assert player.y == 11
    
    def test_move_downright(self):
        """Test moving diagonally down-right."""
        player = Player(10, 10)
        result = player.move(1, 1)
        assert result is True
        assert player.x == 11
        assert player.y == 11
    
    def test_move_out_of_bounds_left(self):
        """Test that moving out of bounds to the left is prevented."""
        player = Player(0, 10)
        result = player.move(-1, 0)
        assert result is False
        assert player.x == 0
        assert player.y == 10
    
    def test_move_out_of_bounds_right(self):
        """Test that moving out of bounds to the right is prevented."""
        player = Player(GRID_WIDTH - 1, 10)
        result = player.move(1, 0)
        assert result is False
        assert player.x == GRID_WIDTH - 1
        assert player.y == 10
    
    def test_move_out_of_bounds_up(self):
        """Test that moving out of bounds upward is prevented."""
        player = Player(10, 0)
        result = player.move(0, -1)
        assert result is False
        assert player.x == 10
        assert player.y == 0
    
    def test_move_out_of_bounds_down(self):
        """Test that moving out of bounds downward is prevented."""
        player = Player(10, GRID_HEIGHT - 1)
        result = player.move(0, 1)
        assert result is False
        assert player.x == 10
        assert player.y == GRID_HEIGHT - 1
    
    def test_move_out_of_bounds_topleft_corner(self):
        """Test that moving out of bounds from top-left corner is prevented."""
        player = Player(0, 0)
        result = player.move(-1, -1)
        assert result is False
        assert player.x == 0
        assert player.y == 0
    
    def test_move_out_of_bounds_topright_corner(self):
        """Test that moving out of bounds from top-right corner is prevented."""
        player = Player(GRID_WIDTH - 1, 0)
        result = player.move(1, -1)
        assert result is False
        assert player.x == GRID_WIDTH - 1
        assert player.y == 0
    
    def test_move_out_of_bounds_bottomleft_corner(self):
        """Test that moving out of bounds from bottom-left corner is prevented."""
        player = Player(0, GRID_HEIGHT - 1)
        result = player.move(-1, 1)
        assert result is False
        assert player.x == 0
        assert player.y == GRID_HEIGHT - 1
    
    def test_move_out_of_bounds_bottomright_corner(self):
        """Test that moving out of bounds from bottom-right corner is prevented."""
        player = Player(GRID_WIDTH - 1, GRID_HEIGHT - 1)
        result = player.move(1, 1)
        assert result is False
        assert player.x == GRID_WIDTH - 1
        assert player.y == GRID_HEIGHT - 1


class TestGame:
    """Tests for the Game class."""
    
    def test_game_initialization(self):
        """Test that a game initializes correctly."""
        game = Game()
        assert game.width == GRID_WIDTH
        assert game.height == GRID_HEIGHT
        assert game.player is not None
        assert game.player.x == GRID_WIDTH // 2
        assert game.player.y == GRID_HEIGHT // 2
        assert game.running is True
    
    def test_direction_map_has_all_numpad_keys(self):
        """Test that direction map contains all 8 numpad directions."""
        game = Game()
        assert len(game.direction_map) == 8
    
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
    
    def test_toggle_fullscreen_to_fullscreen(self):
        """Test toggling from windowed to fullscreen mode."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        game.toggle_fullscreen()
        
        # Should set fullscreen to True
        assert mock_window.fullscreen is True
    
    def test_toggle_fullscreen_to_windowed(self):
        """Test toggling from fullscreen to windowed mode."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = True
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        game.toggle_fullscreen()
        
        # Should set fullscreen to False
        assert mock_window.fullscreen is False
    
    def test_increase_font_size(self):
        """Test increasing font size."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        
        with patch('tcod.tileset.load_truetype_font') as mock_load:
            mock_tileset = Mock()
            mock_load.return_value = mock_tileset
            
            initial_size = game.font_size
            game.increase_font_size()
            
            assert game.font_size == initial_size + FONT_SIZE_INCREMENT
            # VT323 font uses 5:8 width-to-height ratio
            expected_width = int(game.font_size * 0.625)
            expected_height = game.font_size
            mock_load.assert_called_once_with(font_path, expected_width, expected_height)
            mock_context.change_tileset.assert_called_once_with(mock_tileset)
    
    def test_increase_font_size_at_max(self):
        """Test that font size doesn't increase beyond maximum."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        game.font_size = MAX_FONT_SIZE
        
        with patch('tcod.tileset.load_truetype_font') as mock_load:
            game.increase_font_size()
            
            assert game.font_size == MAX_FONT_SIZE
            mock_load.assert_not_called()
            mock_context.change_tileset.assert_not_called()
    
    def test_decrease_font_size(self):
        """Test decreasing font size."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        
        with patch('tcod.tileset.load_truetype_font') as mock_load:
            mock_tileset = Mock()
            mock_load.return_value = mock_tileset
            
            initial_size = game.font_size
            game.decrease_font_size()
            
            assert game.font_size == initial_size - FONT_SIZE_INCREMENT
            # VT323 font uses 5:8 width-to-height ratio
            expected_width = int(game.font_size * 0.625)
            expected_height = game.font_size
            mock_load.assert_called_once_with(font_path, expected_width, expected_height)
            mock_context.change_tileset.assert_called_once_with(mock_tileset)
    
    def test_decrease_font_size_at_min(self):
        """Test that font size doesn't decrease beyond minimum."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        game.font_size = MIN_FONT_SIZE
        
        with patch('tcod.tileset.load_truetype_font') as mock_load:
            game.decrease_font_size()
            
            assert game.font_size == MIN_FONT_SIZE
            mock_load.assert_not_called()
            mock_context.change_tileset.assert_not_called()
    
    def test_handle_alt_enter_event(self):
        """Test that Alt+Enter triggers fullscreen toggle."""
        mock_context = Mock()
        mock_window = Mock()
        mock_window.fullscreen = False
        mock_context.sdl_window = mock_window
        
        game = Game(context=mock_context)
        
        # Create Alt+Enter event
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.LALT
        )
        
        game.handle_event(event)
        
        assert mock_window.fullscreen is True
    
    def test_handle_ctrl_equals_event(self):
        """Test that Ctrl+= triggers font size increase."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        
        with patch('tcod.tileset.load_truetype_font') as mock_load:
            mock_tileset = Mock()
            mock_load.return_value = mock_tileset
            
            initial_size = game.font_size
            
            # Create Ctrl+= event
            event = tcod.event.KeyDown(
                scancode=0,
                sym=tcod.event.KeySym.EQUALS,
                mod=tcod.event.Modifier.LCTRL
            )
            
            game.handle_event(event)
            
            assert game.font_size == initial_size + FONT_SIZE_INCREMENT
    
    def test_handle_ctrl_minus_event(self):
        """Test that Ctrl+- triggers font size decrease."""
        mock_context = Mock()
        font_path = "/path/to/font.ttf"
        game = Game(context=mock_context, font_path=font_path)
        
        with patch('tcod.tileset.load_truetype_font') as mock_load:
            mock_tileset = Mock()
            mock_load.return_value = mock_tileset
            
            initial_size = game.font_size
            
            # Create Ctrl+- event
            event = tcod.event.KeyDown(
                scancode=0,
                sym=tcod.event.KeySym.MINUS,
                mod=tcod.event.Modifier.LCTRL
            )
            
            game.handle_event(event)
            
            assert game.font_size == initial_size - FONT_SIZE_INCREMENT
