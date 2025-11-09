import argparse

from board_parser import BoardParser
from calibration import Calibrator
from solver import ThreesSolver
from strategies.simple_strategy import SimpleStrategy
from strategies.memory_strategy import MemoryStrategy


def main():
    parser = argparse.ArgumentParser(description='Automatic Threes player')
    parser.add_argument(
        '-c', '--calibrate', action='store_true', help='Run calibration mode')
    parser.add_argument(
        '-p', '--parse', action='store_true', help='Run parsing mode (only recognize game state)')
    parser.add_argument(
        '-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument(
        '-s', '--strategy', choices=['simple', 'memory'], default='simple',
        help='Strategy to use (default: simple)')
    parser.add_argument(
        '-g', '--games', type=int, default=None,
        help='Maximum number of games to play (default: unlimited)')
    parser.add_argument(
        '-t', '--target', type=int, default=384,
        help='Target tile value to reach (default: 384)')

    args = parser.parse_args()

    if args.calibrate:
        Calibrator().calibrate()
    elif args.parse:
        try:
            BoardParser(debug=True, calibration_dir='./').parse_board_state()
        except Exception as e:
            print(f'Parsing error: {e}')
    else:
        if args.strategy == 'simple':
            strategy = SimpleStrategy(debug=args.debug)
        elif args.strategy == 'memory':
            strategy = MemoryStrategy(debug=args.debug)

        solver = ThreesSolver(strategy=strategy, debug=args.debug)
        solver.play(target_score=args.target, max_games=args.games)


if __name__ == "__main__":
    main()
