import numpy as np
import os
import pyautogui
import random
import time

from datetime import datetime
from board_parser import BoardParser
from strategies.simple_strategy import SimpleStrategy


class ThreesSolver:
    def __init__(self, strategy=None, debug=True, log_dir='./logs', screenshots_dir='./screenshots'):
        self._debug = debug
        self._board_parser = BoardParser(debug=debug, calibration_dir='./')

        self._strategy = strategy or SimpleStrategy(debug=self._debug)

        self._move_count = 0
        self._last_moves = []
        self._consecutive_failures = 0
        self._max_tile_reached = 0
        self._consecutive_no_change = 0
        self._valid_next_tiles = [1, 2, 3, 6, 12]

        self._screenshots_dir = screenshots_dir
        self._log_dir = log_dir
        self._log_file = None

        self.setup_directories()
        self.setup_logging()

    def setup_directories(self):
        for directory in [self._log_dir, self._screenshots_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def setup_logging(self):
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'threes_game_{timestamp}.log'
        self._log_file = open(os.path.join(self._log_dir, log_filename), 'w', encoding='utf-8')

        self.log('=== THREES SOLVER LOG ===')
        self.log(f'Started at: {datetime.now()}')
        self.log(f'Strategy: {self._strategy.__class__.__name__}')

    def log(self, message, console=True, level='INFO'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f'[{timestamp}] {level}: {message}'

        if self._log_file:
            self._log_file.write(f'{log_message}\n')
            self._log_file.flush()

        if console and self._debug and level != 'DEBUG':
            print(log_message)

    def close_logging(self):
        if self._log_file:
            self.log('=== GAME FINISHED ===')
            self.log(f'Finished at: {datetime.now()}')
            self._log_file.close()

    def save_final_screenshot(self):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = os.path.join(self._screenshots_dir, f'game_over_{timestamp}.png')

            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)

            self.log(f'Final screenshot saved: {screenshot_path}')

            return True
        except Exception as e:
            self.log(f'Failed to save final screenshot: {e}', level='ERROR')
            return False

    def restart_game(self):
        self.log('Restarting game...')

        try:
            pyautogui.keyDown('enter')
            time.sleep(0.1)
            pyautogui.keyUp('enter')

            time.sleep(1)

            pyautogui.keyDown('z')
            time.sleep(0.1)
            pyautogui.keyUp('z')

            time.sleep(1)

            pyautogui.keyDown('enter')
            time.sleep(0.1)
            pyautogui.keyUp('enter')

            time.sleep(1)

            pyautogui.keyDown('down')
            time.sleep(0.1)
            pyautogui.keyUp('down')

            time.sleep(2.0)

            self.log('Game restarted successfully')

            return True

        except Exception as e:
            self.log(f'Failed to restart game: {e}', level='ERROR')
            return False

    def reset_game_stats(self):
        self._move_count = 0
        self._last_moves = []
        self._consecutive_failures = 0
        self._max_tile_reached = 0
        self._consecutive_no_change = 0

    def get_game_phase(self, max_tile):
        if hasattr(self._strategy, 'get_game_phase'):
            return self._strategy.get_game_phase(max_tile)
        return 'mid'

    def get_board_state(self):
        board, _ = self._board_parser.parse_board()
        return board

    def get_next_tile(self):
        next_tile, parse_time = self._board_parser.parse_next_tile()

        self.log(f'Raw next_tile: {next_tile} (type: {type(next_tile)})', level='DEBUG')

        if isinstance(next_tile, str):
            try:
                next_tile = int(next_tile)
                self.log(f'Converted next_tile to int: {next_tile}', level='DEBUG')
            except (ValueError, TypeError):
                self.log(
                    f'Next tile recognition failed (cannot convert "{next_tile}" to int), using fallback',
                    level='WARNING'
                )
                return random.choice([1, 2])

        if next_tile == 0 or next_tile not in self._valid_next_tiles:
            self.log(f'Next tile recognition failed (invalid value: {next_tile}), using fallback', level='WARNING')
            return random.choice([1, 2])

        return next_tile

    def make_move(self, direction):
        self.log(f'Executing: {direction}', level='DEBUG')

        for _ in range(1):
            pyautogui.keyDown(direction)
            time.sleep(0.05)
            pyautogui.keyUp(direction)
            time.sleep(0.05)

        self._move_count += 1
        self._last_moves.append(direction)

        if len(self._last_moves) > 10:
            self._last_moves.pop(0)

        time.sleep(0.1)

    def has_reached_target(self, board, target=384):
        reached = np.any(board >= target)
        if reached:
            self.log(f'🎉 TARGET {target} REACHED! 🎉')
        return reached

    def is_game_over(self, board):
        return self._strategy.is_game_over(board)

    def print_compact_board(self, board):
        board_str = ''
        for i in range(4):
            row = [f'{cell:2}' if cell > 0 else ' .' for cell in board[i]]
            board_str += ' '.join(row) + '\n'
        return board_str.strip()

    def play_single_game(self, target_score=384):
        self.log(f'Starting new game - target: {target_score}')
        self._board_parser.countdown_timer(3)

        max_failures = 5
        aggressive_mode = False

        try:
            while True:
                try:
                    board = self.get_board_state()
                    next_tile = self.get_next_tile()

                    if (hasattr(self._strategy, 'start_new_game') and not hasattr(self, 'game_initialized')):
                        self._strategy.start_new_game(board)
                        self.game_initialized = True

                    current_max = np.max(board)
                    free_cells = np.sum(board == 0)

                    phase = self.get_game_phase(current_max)
                    self.log(
                        f'Move {self._move_count+1:2d} | Max: {current_max:3d} | Free: {free_cells} '
                        f'| Next: {next_tile:2d} | Phase: {phase}'
                    )

                    if self._debug:
                        print(self.print_compact_board(board))
                        print()

                    if self.has_reached_target(board, target_score):
                        break

                    if self.is_game_over(board):
                        self.log('GAME OVER - NO MOVES LEFT')
                        break

                    score_before = self._strategy.evaluate_position(board) if hasattr(self._strategy, 'evaluate_position') else 0  # noqa: E501

                    if free_cells <= 3 and current_max >= 48:
                        aggressive_mode = True
                        self.log('ACTIVATING AGGRESSIVE MODE - few free cells and high tiles')

                    if aggressive_mode and hasattr(self._strategy, 'find_aggressive_move'):
                        aggressive_dir = self._strategy.find_aggressive_move(board, next_tile)
                        self.make_move(aggressive_dir)
                        aggressive_mode = False
                    else:
                        depth = 3 if free_cells <= 4 else 2
                        _, best_direction = self._strategy.find_best_move(board, next_tile, depth=depth)
                        self.make_move(best_direction)

                    new_board = self.get_board_state()
                    score_after = self._strategy.evaluate_position(new_board) if hasattr(self._strategy, 'evaluate_position') else 0  # noqa: E501

                    if hasattr(self._strategy, 'record_move'):
                        self._strategy.record_move(
                            board, next_tile, best_direction,
                            new_board, score_before, score_after,
                            self._move_count
                        )

                    self._consecutive_failures = 0

                except Exception as e:
                    self.log(f'Error: {e}', level='ERROR')
                    self._consecutive_failures += 1
                    if self._consecutive_failures >= max_failures:
                        self.log('Too many consecutive errors, stopping')
                        break
                    time.sleep(1)

        finally:
            final_score = np.max(board)
            final_stats = f'Game finished - Moves: {self._move_count}, Max tile: {final_score}'

            self.log(final_stats)
            print(f'\n{final_stats}')

            if hasattr(self._strategy, 'end_game'):
                self._strategy.end_game(final_score, final_score, self._move_count)
                if hasattr(self._strategy, 'get_memory_stats'):
                    stats = self._strategy.get_memory_stats()
                    self.log(f'Memory stats: {stats}')

            if hasattr(self, 'game_initialized'):
                del self.game_initialized

            self.save_final_screenshot()

            return np.max(board), self._move_count

    def play(self, target_score=384, max_games=None):
        game_count = 0
        best_score = 0
        total_moves = 0

        try:
            while max_games is None or game_count < max_games:
                game_count += 1
                self.log(f'=== STARTING GAME {game_count} ===')

                max_tile, moves = self.play_single_game(target_score)

                if max_tile > best_score:
                    best_score = max_tile
                total_moves += moves

                self.log(f'Game {game_count} completed: Max tile = {max_tile}, Moves = {moves}')
                self.log(f'Best score so far: {best_score}')

                self.restart_game()
                self.reset_game_stats()

                time.sleep(1)

        except KeyboardInterrupt:
            self.log('Game interrupted by user')

        finally:
            if game_count > 0:
                avg_moves = total_moves / game_count
                self.log('=== FINAL STATISTICS ===')
                self.log(f'Games played: {game_count}')
                self.log(f'Best score: {best_score}')
                self.log(f'Average moves per game: {avg_moves:.1f}')

            self.close_logging()
