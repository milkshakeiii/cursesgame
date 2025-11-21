# cursesgame

A D&D-Pokémon hybrid game using python-tcod where the player explores a 50x25 grid, encounters creatures, and can battle or convert them to join their team.

The game features a screen system with multiple screens:
- **Main Menu**: Navigate menu options to start a new game or exit
- **Map View**: Play the game by moving the player around the map with terrain
- **Encounter Screen**: Triggered when the player steps on an encounter tile, where the player can battle and convert creatures

## Game Mechanics

### Player
The player has the following attributes:
- **Ability Scores**: STR, DEX, CON, INT, WIS, CHA
- **Health**: Current health and max health
- **Level and Class**: Starting as level 1 Adventurer
- **Team**: Can collect creatures by converting them during encounters

### Creatures
Creatures have the following attributes:
- **Ability Scores**: STR, DEX, CON (no INT, WIS, CHA)
- **Health**: Current health (100 max) and max health
- **Convert Progress**: 0-100 scale indicating how close they are to joining the player's team
- **Level**: Starting at level 1

### Encounters
When stepping on an encounter tile, the player enters battle with a creature. The player can:
- **Attack**: Press 'A' to attack, reducing the creature's health by 5
- **Convert**: Press 'C' to convert, increasing the convert progress by 5
- **Flee**: Press 'F' to return to the map

When a creature's health reaches 0, it is defeated and removed. When convert reaches 100, the creature joins the player's team.

## Installation

```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python game.py
```

## Controls

### Main Menu
- **UP/DOWN** or **Numpad 8/2**: Navigate menu options
- **ENTER**: Select menu option
- **ESC**: Quit the game

### Map View (In-Game)
- **Numpad 4**: Move left
- **Numpad 6**: Move right
- **Numpad 8**: Move up
- **Numpad 2**: Move down
- **Numpad 7**: Move up-left
- **Numpad 9**: Move up-right
- **Numpad 1**: Move down-left
- **Numpad 3**: Move down-right
- **ESC**: Quit the game

### Encounter Screen
- **A**: Enter attack mode (then use numpad 1-9 to select target)
- **C**: Enter convert mode (then use numpad 1-9 to select target)
- **F**: Flee back to map
- **ESC**: Cancel action selection or quit the game

During attack/convert mode:
- **Numpad 1-9**: Select target square in the 3x3 grid
- **ESC**: Cancel action selection

### Global Controls (All Screens)
- **Alt+Enter**: Toggle fullscreen/windowed mode

## Running Tests

```bash
python -m pytest test_game.py -v
```
