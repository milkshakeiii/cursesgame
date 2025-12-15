import pygame
from typing import Dict, Tuple

class SpriteManager:
    def __init__(self, tile_size: int = 24):
        self.tile_size = tile_size
        self.font = pygame.font.SysFont("monospace", int(tile_size * 0.8), bold=True)
        self.cache: Dict[Tuple[str, Tuple[int, int, int]], pygame.Surface] = {}

    def get_sprite(self, symbol: str, color: Tuple[int, int, int], bg_color: Tuple[int, int, int] = None) -> pygame.Surface:
        """
        Generates or retrieves a cached sprite surface for a given symbol and color.
        """
        key = (symbol, color, bg_color)
        if key in self.cache:
            return self.cache[key]

        # Create a transparent surface for the tile
        surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        
        if bg_color:
            surface.fill(bg_color)

        # Render the text
        text_surf = self.font.render(symbol, True, color)
        
        # Center the text on the tile
        text_rect = text_surf.get_rect(center=(self.tile_size // 2, self.tile_size // 2))
        surface.blit(text_surf, text_rect)

        self.cache[key] = surface
        return surface

    def draw(self, screen: pygame.Surface, x: int, y: int, symbol: str, color: Tuple[int, int, int], bg_color: Tuple[int, int, int] = None):
        """
        Draws a symbol at the specified grid coordinates.
        """
        sprite = self.get_sprite(symbol, color, bg_color)
        screen_x = x * self.tile_size
        screen_y = y * self.tile_size
        screen.blit(sprite, (screen_x, screen_y))
