# cursesgame

A D&D-Pokémon hybrid game using Pygame where the player explores a procedural world, encounters creatures, and builds a team.

## Features
- **Biomes:** Explore 4 distinct biomes (Forest, Plains, Snow, Underground) in a randomized order.
- **Team Building:** Convert enemies to join your side.
- **Tactical Combat:** Position your team in a 3x3 grid to maximize effectiveness.
- **Drafting:** After each battle, arrange your team and manage new recruits.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python game.py
```

## Controls

### General
- **Arrow Keys / Numpad**: Navigation
- **Enter**: Confirm / Select
- **Esc**: Back / Cancel / Quit

### Map View
- **Arrow Keys / Numpad**: Move player
- **Esc**: Quit

### Encounter Screen
- **A**: Attack
- **C**: Convert
- **Q**: Select Ally
- **E**: Select Enemy
- **F**: Flee
- **Numpad 1-9**: Select target grid slot

### Team Arrangement
- **Arrow Keys / Numpad**: Move cursor between Grid and Pending list
- **Enter**: Pick up / Place / Swap unit
- **Delete / Backspace**: Dismiss unit (Permanently!)