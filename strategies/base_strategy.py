import numpy as np

from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    def __init__(self, debug=True):
        self._debug = debug

    @abstractmethod
    def find_best_move(self, board, next_tile, depth=2):
        pass

    @abstractmethod
    def evaluate_position(self, board):
        pass

    def can_merge(self, a, b):
        if a == 0 or b == 0:
            return False

        if (a == 1 and b == 2) or (a == 2 and b == 1):
            return True

        if a >= 3 and a == b:
            return True

        return False

    def simulate_move(self, board, direction):
        new_board = board.copy()
        changed = False

        if direction == 'left':
            for i in range(4):
                original = new_board[i].copy()
                new_board[i] = self._process_line_left(new_board[i])
                if not np.array_equal(original, new_board[i]):
                    changed = True

        elif direction == 'right':
            for i in range(4):
                original = new_board[i].copy()
                new_board[i] = self._process_line_right(new_board[i])
                if not np.array_equal(original, new_board[i]):
                    changed = True

        elif direction == 'up':
            for j in range(4):
                original = [new_board[i, j] for i in range(4)]
                new_col = self._process_line_left(original)
                for i in range(4):
                    if new_board[i, j] != new_col[i]:
                        changed = True
                    new_board[i, j] = new_col[i]

        elif direction == 'down':
            for j in range(4):
                original = [new_board[i, j] for i in range(4)]
                new_col = self._process_line_right(original)
                for i in range(4):
                    if new_board[i, j] != new_col[i]:
                        changed = True
                    new_board[i, j] = new_col[i]

        return new_board, changed

    def _process_line_left(self, line):
        line = line.copy()

        for j in range(1, 4):
            if line[j] != 0:
                if line[j-1] == 0:
                    line[j-1] = line[j]
                    line[j] = 0
                elif self.can_merge(line[j-1], line[j]):
                    line[j-1] = line[j-1] + line[j]
                    line[j] = 0

        return line

    def _process_line_right(self, line):
        line = line.copy()

        for j in range(2, -1, -1):
            if line[j] != 0:
                if line[j+1] == 0:
                    line[j+1] = line[j]
                    line[j] = 0
                elif self.can_merge(line[j], line[j+1]):
                    line[j+1] = line[j] + line[j+1]
                    line[j] = 0

        return line

    def is_game_over(self, board):
        if np.any(board == 0):
            return False

        for direction in ['left', 'right', 'up', 'down']:
            _, changed = self.simulate_move(board, direction)
            if changed:
                return False

        return True
