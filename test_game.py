#!/usr/bin/env python3
"""Unit tests for the game."""

import pytest
from game import Player, Game, GRID_WIDTH, GRID_HEIGHT


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
