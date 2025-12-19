import os
import pygame
import pygame.freetype
from typing import Dict, Optional, Tuple

# Default BDF font path (relative to this file)
DEFAULT_FONT_PATH = os.path.join(os.path.dirname(__file__), "ucs-fonts", "10x20.bdf")


class SpriteManager:
    def __init__(self, font_path: str = DEFAULT_FONT_PATH, scale: int = 1):
        self.scale = scale
        pygame.freetype.init()
        self.font = pygame.freetype.Font(font_path)
        # BDF fonts have fixed size - get it from a rendered character
        surf, rect = self.font.render("█", (255, 255, 255))
        self.tile_width = surf.get_width() * scale
        self.tile_height = surf.get_height() * scale
        self.cache: Dict[
            Tuple[str, Tuple[int, int, int], Optional[Tuple[int, int, int]]],
            pygame.Surface,
        ] = {}

    def get_sprite(
        self,
        symbol: str,
        color: Tuple[int, int, int],
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> pygame.Surface:
        """
        Generates or retrieves a cached sprite surface for a given symbol and color.
        """
        key = (symbol, color, bg_color)
        if key in self.cache:
            return self.cache[key]

        # Render at font's natural size
        text_surf, _ = self.font.render(symbol, color, bg_color)

        # Scale by integer factor if needed
        if self.scale != 1:
            text_surf = pygame.transform.scale_by(text_surf, self.scale)

        self.cache[key] = text_surf
        return text_surf

    def draw(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        symbol: str,
        color: Tuple[int, int, int],
        bg_color: Optional[Tuple[int, int, int]] = None,
    ):
        """
        Draws a symbol at the specified grid coordinates.
        """
        sprite = self.get_sprite(symbol, color, bg_color)
        screen_x = x * self.tile_width
        screen_y = y * self.tile_height
        screen.blit(sprite, (screen_x, screen_y))
