import numpy as np

from strategies.base_strategy import BaseStrategy


class SimpleStrategy(BaseStrategy):
    def __init__(self, debug=True):
        super().__init__(debug)

    def find_best_move(self, board):
        best_score = float('-inf')
        best_direction = 'left'

        for direction in ['left', 'right', 'up', 'down']:
            new_board, changed = self.simulate_move(board, direction)

            if not changed:
                continue

            score = self.evaluate_position(new_board)

            if score > best_score:
                best_score = score
                best_direction = direction

        return best_score, best_direction

    def evaluate_position(self, board):
        score = 0

        free_cells = np.sum(board == 0)
        score += free_cells * 20

        if board[0, 0] == np.max(board):
            score += 50

        for i in range(4):
            for j in range(3):
                if board[i, j] >= board[i, j+1] and board[i, j] > 0:
                    score += 5

        for i in range(4):
            for j in range(4):
                if board[i, j] in [1, 2]:
                    has_partner = False
                    for dx, dy in [(0, 1), (1, 0)]:
                        ni, nj = i+dx, j+dy
                        if 0 <= ni < 4 and 0 <= nj < 4:
                            if self.can_merge(board[i, j], board[ni, nj]):
                                has_partner = True
                                break
                    if not has_partner:
                        score -= 10

        return score
