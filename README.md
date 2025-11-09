# Threes AI Solver

An automated bot that plays the 3rees game for Fairchild Channel F emulator using computer vision and strategic decision-making. The bot can consistently achieve the 384 tile and has potential for higher scores.

## Overview

This project combines several components to create an autonomous 3rees player for the Fairchild Channel F emulator:
- **Computer Vision** for board state recognition from emulator screen
- **Game Simulation** for move prediction based on 3rees mechanics
- **AI Strategies** for decision making
- **Memory System** for learning from repeated games

## Components

### 1. Calibration System (`calibration.py`)

The calibration process is crucial for accurate board recognition from the emulator:

#### Calibration Steps:
1. **Full Screen Capture**: Takes a screenshot of the entire display with emulator
2. **Region Definition**: Manually specify board and next tile regions within emulator window
3. **Grid Calculation**: Automatically calculates tile positions and gaps for 3rees
4. **Color Analysis**: Learns tile colors through user input
5. **Data Persistence**: Saves calibration to `calibration_data.json`

#### Important Calibration Notes for Fairchild Channel F Emulator:

**Sample Coordinates (MacBook Pro):**
- **Board Region**: `95 251 1806 1874`
- **Next Tile Region**: `2250 487 2633 870`

**Important**: These coordinates are specific to my MacBook Pro setup. On other systems and screen configurations, you MUST manually determine the correct coordinates during calibration.

#### Calibration Tips:
1. **Consistent Window Placement**: Always position the emulator window in the same location
2. **Full Screen Reference**: Use the full screenshot to identify your specific coordinates
3. **Coordinate Format**: Use `left top right bottom` format (pixels from top-left corner)
4. **Verification**: Test parsing after calibration to ensure accurate recognition
5. **Multiple Displays**: If using multiple monitors, ensure the emulator is on the primary display

#### Finding Your Coordinates:
1. Run `python main.py --calibrate`
2. Examine the saved `01_full_screen.png`
3. Use an image editor or screenshot tool to find:
   - **Board**: The entire 4x4 grid of tiles
   - **Next Tile**: The preview of the next tile to appear
4. Enter the coordinates when prompted during calibration

### 2. Board Parser (`board_parser.py`)

Handles real-time game state recognition from emulator:

#### Features:
- **Multi-scale Processing**: Handles different emulator window sizes
- **Color-based Recognition**: Uses calibrated colors to identify 3rees tiles
- **Fast Processing**: Optimized for real-time gameplay
- **Debug Visualization**: Saves intermediate images for verification

#### Process:
1. Captures screen region based on calibration
2. Extracts individual tile images from 3rees board
3. Compares colors against calibrated values
4. Returns 4x4 board matrix and next tile value

### 3. Move Simulation Testing (`test_move_simulation.py`)

Validates that the game simulation matches actual 3rees game mechanics:

#### Test Procedure:
1. **Autonomous Testing**: Runs predefined move sequences on emulator
2. **State Comparison**: Compares simulated vs actual board states
3. **Accuracy Calculation**: Measures simulation reliability
4. **Visual Reporting**: Generates detailed comparison logs

#### Key Findings:
- The current simulation correctly handles 3rees mechanics:
  - Tile merging (1+2=3, 3+3=6, etc.)
  - Movement mechanics in all directions
  - Empty space filling

### 4. Game Solver (`solver.py`)

Main orchestrator that combines all components for 3rees gameplay:

#### Game Loop:
1. **State Capture**: Gets current board and next tile from emulator
2. **Strategy Decision**: Uses selected AI strategy to choose move
3. **Move Execution**: Sends keyboard commands to the emulator
4. **Progress Tracking**: Monitors game state and achievements

#### Features:
- **Adaptive Timing**: Adjusts delays based on game phase
- **Error Recovery**: Handles recognition failures gracefully
- **Multi-game Support**: Plays multiple games sequentially
- **Comprehensive Logging**: Detailed game statistics and debugging

## AI Strategies

### SimpleStrategy
Basic strategy for 3rees focusing on:
- Maximizing free cells
- Keeping largest tile in corner
- Maintaining row/column monotonicity
- Avoiding isolated 1s and 2s

### MemoryStrategy (Currently Incomplete)

**Note**: The MemoryStrategy is partially implemented but not fully integrated. The memory recording methods exist but are not being called during gameplay.

#### Planned Features:
- **State Recognition**: Identifies repeated game positions in 3rees
- **Move Memory**: Remembers successful moves for each state
- **Learning**: Improves performance over multiple games
- **Persistence**: Saves memory between sessions

#### Current Implementation Status:
- Memory storage structure is defined
- Move recording methods are written but not invoked
- Memory recall system is functional
- Automatic optimization for memory size

#### Integration Needed:
To complete the MemoryStrategy, the following needs to be added:
- Call `record_move()` after each move in the main game loop
- Invoke memory saving at game end
- Add memory-based decision weighting in `find_best_move()`

## Usage

### Prerequisites:
- Fairchild Channel F emulator with [3rees game](https://arlagames.itch.io/3rees-for-fairchild-channel-f)
- Python 3.7+ with required dependencies

### Initial Setup:
```bash
# Run calibration first (ensure emulator is visible)
python main.py --calibrate

# Test board recognition
python main.py --parse

# Test move simulation
python test_move_simulation.py
```

### Gameplay:
```bash
# Simple strategy
python main.py --strategy simple --target 384 --debug

# Memory strategy
python main.py --strategy memory --target 384 --debug
```

### Command Line Options:
- `--calibrate` or `-c`: Run calibration mode to set up board recognition
- `--parse` or `-p`: Test board recognition only without playing
- `--debug` or `-d`: Enable detailed debug output and logging
- `--strategy` or `-s`: Choose AI strategy (`simple` or `memory`) - default: `simple`
- `--target` or `-t`: Target tile value to achieve - default: `384`
- `--games` or `-g`: Maximum number of games to play - default: unlimited

## Performance

### Current Capabilities:
- **Consistent 384 Achievement**: Regularly reaches target tile in 3rees
- **Fast Execution**: ~0.5-1 second per move
- **High Accuracy**: >95% move simulation accuracy
- **Error Resilience**: Recovers from recognition failures gracefully

### Optimization Opportunities:
1. **Memory Strategy Completion**: Implement full learning system (currently partial)
2. **Deeper Search**: Increase simulation depth for better decision making
3. **Pattern Recognition**: Add specialized handling for common 3rees situations
4. **Performance Tuning**: Further reduce move execution time

## Technical Details

### 3rees Game Mechanics Implementation:
- **Move Simulation**: Correctly models 3rees merging rules (1+2=3, matching tiles merge)
- **Game Over Detection**: Accurate end-game state recognition when no moves remain
- **Next Tile Handling**: Properly accounts for upcoming tiles in decision making

### Computer Vision for Emulator:
- **Color Thresholding**: Robust tile recognition under varying lighting conditions
- **Region Adaptation**: Handles different emulator window sizes and positions
- **Error Handling**: Graceful degradation on recognition failures with fallback options

## Future Improvements

### Short-term Goals:
1. Complete MemoryStrategy implementation with full move recording
2. Add more sophisticated evaluation functions optimized for 3rees
3. Implement opening book strategies for early game optimization

### Long-term Vision:
1. Machine learning-based strategy using reinforcement learning
2. Neural network for advanced position evaluation
3. Cloud-based memory sharing between different bot instances
4. Advanced pattern recognition specific to 3rees gameplay

## Contributing

This project welcomes contributions, particularly in these areas:
- Completing the MemoryStrategy implementation (move recording integration)
- Developing more advanced AI strategies specifically for 3rees mechanics
- Optimizing performance for higher tile achievement (768+)
- Enhancing computer vision reliability across different emulator configurations
- Adding support for other Threes-like game variants
