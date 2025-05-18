# The Living Rusted Tankard - Examples

This directory contains example scripts demonstrating various features of The Living Rusted Tankard game.

## Room Management Demo

The `room_demo.py` script provides an interactive demo of the room rental and sleep mechanics.

### Running the Demo

```bash
# From the project root directory
PYTHONPATH=. python examples/room_demo.py
```

### Available Commands

- `look` or `l`: Look around the tavern (advances time by 0.5 hours)
- `wait [hours]`: Wait for a number of hours (default: 1)
- `rooms`: List available rooms for rent
- `rent`: Rent an available room (costs 5 gold)
- `sleep`: Sleep in your rented room (resets tiredness)
- `work`: Work for an hour to earn gold (increases tiredness)
- `help` or `h`: Show available commands
- `quit` or `q`: Quit the game

### Features Demonstrated

- Time advancement with the `GameClock`
- Room rental system
- Sleep mechanics that reset tiredness
- Gold economy (earn gold by working)
- No-sleep quest that unlocks after 48 hours without sleeping (if no room is rented)
- Room-based quest locking (renting a room permanently locks the no-sleep quest)

### Game Mechanics

- Time advances with most actions
- Tiredness increases over time
- Renting a room allows you to sleep and recover energy
- Working earns gold but increases tiredness
- The no-sleep quest unlocks after 48 hours without sleeping (if you don't rent a room)
- Once you rent a room, the no-sleep quest is permanently locked
