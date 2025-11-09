import numpy as np
import pyautogui
import time

from datetime import datetime
from board_parser import BoardParser
from strategies.base_strategy import BaseStrategy


class TestStrategy(BaseStrategy):
    def find_best_move(self):
        return 0, 'right'

    def evaluate_position(self):
        return 0


class SimulationTester:
    def __init__(self, debug=True):
        self._debug = debug
        self._parser = BoardParser(debug=debug, calibration_dir='./')
        self._strategy = TestStrategy(debug=debug)
        self._log = []

    def _make_move(self, direction):
        pyautogui.keyDown(direction)
        time.sleep(0.05)
        pyautogui.keyUp(direction)
        time.sleep(0.05)

    def _compare(self, real_board, sim_board):
        modified_sim = sim_board.copy()

        for i in range(4):
            for j in range(4):
                if real_board[i, j] != 0 and sim_board[i, j] == 0:
                    modified_sim[i, j] = real_board[i, j]

        return np.array_equal(real_board, modified_sim)

    def capture_game_state(self, move_number, direction):
        try:
            board_before, _ = self._parser.parse_board()
            next_tile, _ = self._parser.parse_next_tile()

            self._make_move(direction)
            time.sleep(0.8)

            board_after, _ = self._parser.parse_board()
            simulated_board, changed = self._strategy.simulate_move(board_before, direction)

            desc = {
                'move_number': move_number,
                'direction': direction,
                'board_before': board_before.tolist(),
                'board_after': board_after.tolist(),
                'simulated_board': simulated_board.tolist(),
                'next_tile': next_tile,
                'changed': changed,
                'timestamp': datetime.now().isoformat()
            }

            match = self._compare(board_after, simulated_board)
            desc['match'] = bool(match)

            self._log.append(desc)

            if self._debug:
                self._print_comparison(desc, match)

            return match

        except Exception as e:
            print(f'Error capturing state: {e}')
            return False

    def run_autonomous_test(self, moves=10):
        print('=== AUTONOMOUS SIMULATION TEST ===')
        print('Make sure the game is active for the next 30 seconds...')

        for i in range(5, 0, -1):
            print(f'Starting in {i}...')
            time.sleep(1)

        print('Starting test!')

        move_count = 0
        matches = 0

        directions = ['right', 'down', 'left', 'up', 'right', 'down', 'left', 'up', 'right', 'down']

        for i, direction in enumerate(directions[:moves]):
            print(f'\nMove {i+1}/{moves}: {direction}')
            time.sleep(0.5)
            if self.capture_game_state(i+1, direction):
                matches += 1
            move_count += 1

        accuracy = matches / move_count if move_count > 0 else 0

        print('\n=== TEST RESULTS ===')
        print(f'Moves tested: {move_count}')
        print(f'Matches: {matches}')
        print(f'Simulation accuracy: {accuracy:.1%}')

        self.save_test_results()

        return accuracy

    def _print_board(self, board):
        board_array = np.array(board)
        for i in range(4):
            row = [f'{cell:3}' if cell != 0 else '  .' for cell in board_array[i]]
            print(' '.join(row))
        print()

    def _print_comparison(self, desc, match):
        print(f"\n=== Move {desc['move_number']}: {desc['direction']} ===")
        print(f"Next tile: {desc['next_tile']}")
        print(f'Match: {"✅" if match else "❌"}')

        print('\nVISUAL COMPARISON:')
        print('BEFORE move:')
        self._print_board(desc['board_before'])

        print('ACTUAL result:')
        self._print_board(desc['board_after'])

        print('SIMULATED result:')
        self._print_board(desc['simulated_board'])

    def save_test_results(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._create_visual_report(f'simulation_test_{timestamp}_visual.txt')

    def _create_visual_report(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('=== VISUAL TESTING REPORT ===\n\n')

            for case in self._log:
                f.write(f"MOVE {case['move_number']}: {case['direction']}\n")
                f.write(f"Next tile: {case['next_tile']}\n")
                f.write(f"Match: {'✅' if case['match'] else '❌'}\n\n")

                f.write('BEFORE move:\n')
                self._write_board(f, case['board_before'])

                f.write('ACTUAL result:\n')
                self._write_board(f, case['board_after'])

                f.write('SIMULATED result:\n')
                self._write_board(f, case['simulated_board'])

                f.write('\n' + '='*50 + '\n\n')

    def _write_board(self, file, board):
        for i in range(4):
            row = [f'{cell:3}' if cell != 0 else '  .' for cell in board[i]]
            file.write(' '.join(row) + '\n')
        file.write('\n')


def main():
    tester = SimulationTester(debug=True)

    print('AUTONOMOUS SIMULATION COMPATIBILITY TEST')
    print('=' * 50)

    print('Make sure that:')
    print('1. Threes game is running and visible on screen')
    print('2. The game is in initial state')
    print('3. Do not touch the computer during the test (30 seconds)')

    print('\nTest will start automatically in 5 seconds...')

    try:
        accuracy = tester.run_autonomous_test(moves=10)

        if accuracy < 1.0:
            print('\n⚠️  Discrepancies detected between simulation and actual game!')
            print('This means simulate_move is working incorrectly.')
        else:
            print('\n🎉 Simulation completely matches the actual game!')

    except Exception as e:
        print(f'Error during test: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
