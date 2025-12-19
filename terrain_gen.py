"""Biome-aware terrain generation using layered simplex noise."""

from typing import Dict, List, Tuple

import tcod.noise


def _build_noise(seed: int) -> tcod.noise.Noise:
    return tcod.noise.Noise(
        dimensions=2,
        algorithm=tcod.noise.Algorithm.SIMPLEX,
        implementation=tcod.noise.Implementation.SIMPLE,
        hurst=0.5,
        lacunarity=2.0,
        octaves=2,
        seed=seed,
    )


def generate_biome_terrain(
    seed: int,
    width: int,
    height: int,
    base_tile: str,
    layers: List[Dict[str, object]],
    *,
    scale: float = 0.1,
    mirror: bool = False,
) -> Dict[Tuple[int, int], str]:
    """Generate terrain tile IDs for a biome using layered noise."""
    ordered_layers = sorted(layers, key=lambda layer: layer.get("priority", 0))
    noise_layers = [
        (layer, _build_noise(seed + int(layer.get("seed_offset", 0))))
        for layer in ordered_layers
    ]

    terrain: Dict[Tuple[int, int], str] = {}
    if mirror:
        half_height = height // 2
        y_range = range(half_height + 1)
    else:
        half_height = None
        y_range = range(height)

    for x in range(width):
        for y in y_range:
            tile_id = base_tile
            for layer, noise in noise_layers:
                threshold = float(layer["threshold"])
                if noise.get_point(x * scale, y * scale) > threshold:
                    tile_id = str(layer["tile_id"])
            terrain[(x, y)] = tile_id

            if mirror and half_height is not None and y < half_height:
                terrain[(x, height - 1 - y)] = tile_id

    return terrain
