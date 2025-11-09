import json
import numpy as np
import os
import random

from strategies.base_strategy import BaseStrategy


class MemoryStrategy(BaseStrategy):
    def __init__(self, debug=True, memory_file='./memory/game_memory.json'):
        super().__init__(debug)

        self._move_history = []

        self._memory_file = memory_file
        self._memory = self.load_memory()

        self._game_states_seen = 0
        self._memory_hits = 0

        self._game_phase_weights = {
            'early': {'free_cells': 2.0, 'max_corner': 3.0, 'monotonicity': 1.0, 'merges': 1.5, 'penalty_12': 1.0},
            'mid': {'free_cells': 1.5, 'max_corner': 2.5, 'monotonicity': 1.5, 'merges': 2.0, 'penalty_12': 1.2},
            'late': {'free_cells': 1.0, 'max_corner': 3.0, 'monotonicity': 2.0, 'merges': 2.5, 'penalty_12': 1.5}
        }

        os.makedirs(os.path.dirname(memory_file), exist_ok=True)

    def load_memory(self):
        try:
            if os.path.exists(self._memory_file):
                with open(self._memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            if self._debug:
                print(f'Memory load error: {e}')
        return {}

    def save_memory(self):
        try:
            with open(self._memory_file, 'w') as f:
                json.dump(self._memory, f, indent=2)
        except Exception as e:
            if self._debug:
                print(f"Memory save error: {e}")

    def get_game_phase(self, max_tile):
        if max_tile <= 24:
            return 'early'
        elif max_tile <= 192:
            return 'mid'
        else:
            return 'late'

    def calculate_monotonicity(self, board):
        monotonicity = 0

        for i in range(4):
            for j in range(3):
                if board[i, j] >= board[i, j+1] and board[i, j] > 0:
                    monotonicity += 1
                elif board[i, j] > 0 and board[i, j+1] > 0:
                    monotonicity -= 1

        for j in range(4):
            for i in range(3):
                if board[i, j] >= board[i+1, j] and board[i, j] > 0:
                    monotonicity += 1
                elif board[i, j] > 0 and board[i+1, j] > 0:
                    monotonicity -= 1

        return monotonicity

    def calculate_merge_potential(self, board):
        merge_potential = 0

        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    continue

                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 4 and 0 <= nj < 4:
                        if self.can_merge(board[i, j], board[ni, nj]):
                            merge_potential += 1

        return merge_potential

    def calculate_isolated_12_penalty(self, board):
        penalty = 0

        for i in range(4):
            for j in range(4):
                if board[i, j] in [1, 2]:
                    has_partner = False

                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        ni, nj = i + dx, j + dy
                        if 0 <= ni < 4 and 0 <= nj < 4:
                            neighbor = board[ni, nj]
                            if (board[i, j] == 1 and neighbor == 2) or (board[i, j] == 2 and neighbor == 1):
                                has_partner = True
                                break

                    if not has_partner:
                        penalty += 5

        return penalty

    def calculate_large_tiles_bonus(self, board):
        bonus = 0
        large_tile_threshold = 12

        for i in range(4):
            for j in range(4):
                if board[i, j] >= large_tile_threshold:
                    for dx, dy in [(0, 1), (1, 0)]:
                        ni, nj = i + dx, j + dy
                        if 0 <= ni < 4 and 0 <= nj < 4:
                            if board[ni, nj] >= large_tile_threshold:
                                bonus += min(board[i, j], board[ni, nj]) // 3

        return bonus

    def evaluate_position(self, board):
        max_tile = np.max(board)
        phase = self.get_game_phase(max_tile)
        weights = self._game_phase_weights[phase]

        score = 0

        free_cells = np.sum(board == 0)
        score += free_cells * weights['free_cells'] * 10

        max_tile_positions = np.argwhere(board == max_tile)
        corner_bonus = 0
        for pos in max_tile_positions:
            distance_to_corner = min(pos[0] + pos[1], pos[0] + (3-pos[1]), (3-pos[0]) + pos[1], (3-pos[0]) + (3-pos[1]))
            corner_bonus += (6 - distance_to_corner) * 5
        score += corner_bonus * weights['max_corner']

        monotonicity = self.calculate_monotonicity(board)
        score += monotonicity * weights['monotonicity'] * 2

        merge_potential = self.calculate_merge_potential(board)
        score += merge_potential * weights['merges'] * 3

        penalty_12 = self.calculate_isolated_12_penalty(board)
        score -= penalty_12 * weights['penalty_12']

        large_tiles_bonus = self.calculate_large_tiles_bonus(board)
        score += large_tiles_bonus

        return score

    def board_to_hash(self, board, next_tile):
        board_tuple = tuple(board.flatten())
        return f'{board_tuple}_{next_tile}'

    def get_memory_advice(self, board, next_tile):
        state_hash = self.board_to_hash(board, next_tile)
        self._game_states_seen += 1

        if state_hash in self._memory:
            self._memory_hits += 1
            memory_data = self._memory[state_hash]
            memory_data['visit_count'] += 1

            best_direction = None
            best_score = -1

            for direction, move_data in memory_data['moves'].items():
                if move_data['total_count'] > 0:
                    success_rate = move_data['success_count'] / move_data['total_count']
                    avg_score_change = np.mean(move_data['score_changes']) if move_data['score_changes'] else 0

                    memory_score = success_rate * 100 + avg_score_change + move_data['max_score_achieved'] * 0.1

                    if memory_score > best_score:
                        best_score = memory_score
                        best_direction = direction

            if best_direction and best_score > 50:
                if self._debug:
                    print(f'Memory advice: {best_direction} (score: {best_score:.1f})')
                return best_direction, best_score

        return None, 0

    def evaluate_position_with_next_tile(self, board, next_tile, depth):
        if depth <= 0:
            return self.evaluate_position(board)

        free_positions = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]

        if not free_positions:
            return self.evaluate_position(board)

        worst_score = float('inf')
        evaluated_positions = min(2, len(free_positions))

        for i in range(evaluated_positions):
            pos = free_positions[i]
            test_board = board.copy()
            test_board[pos] = next_tile

            score, _ = self.find_best_move(test_board, 0, depth-1)

            if score < worst_score:
                worst_score = score

        return worst_score

    def find_best_move(self, board, next_tile, depth=2):
        if isinstance(next_tile, str):
            try:
                next_tile = int(next_tile)
            except (ValueError, TypeError):
                next_tile = 1

        memory_direction, memory_score = self.get_memory_advice(board, next_tile)

        best_score = float('-inf')
        best_direction = 'left'
        valid_moves = []
        move_scores = {}

        for direction in ['left', 'right', 'up', 'down']:
            new_board, changed = self.simulate_move(board, direction)

            if not changed:
                continue

            valid_moves.append(direction)

            score = self.evaluate_position_with_next_tile(new_board, next_tile, depth-1)

            if direction == memory_direction:
                score += max(50, memory_score * 0.5)

            move_scores[direction] = score

            if score > best_score:
                best_score = score
                best_direction = direction

        if not valid_moves:
            return float('-inf'), random.choice(['left', 'right', 'up', 'down'])

        max_tile = np.max(board)
        if max_tile < 48 and random.random() < 0.1:
            exploration_direction = random.choice(valid_moves)
            if self._debug:
                print(f'Exploring: {exploration_direction}')
            return move_scores[exploration_direction], exploration_direction

        return best_score, best_direction

    def record_move(self, board, next_tile, direction, new_board, score_before, score_after, move_count):
        if isinstance(next_tile, str):
            try:
                next_tile = int(next_tile)
            except (ValueError, TypeError):
                next_tile = 0

        score_change = score_after - score_before

        move_info = {
            'move_count': move_count,
            'direction': direction,
            'next_tile': next_tile,
            'max_tile': np.max(board),
            'free_cells_before': np.sum(board == 0),
            'free_cells_after': np.sum(new_board == 0),
            'score_change': score_change
        }
        self._move_history.append(move_info)

        self.remember_successful_move(board, next_tile, direction, score_change, np.max(new_board))

    def remember_successful_move(self, board, next_tile, direction, score_change, result_score):
        state_hash = self.board_to_hash(board, next_tile)

        if state_hash not in self._memory:
            self._memory[state_hash] = {
                'moves': {},
                'best_score': result_score,
                'visit_count': 0
            }

        if direction not in self._memory[state_hash]['moves']:
            self._memory[state_hash]['moves'][direction] = {
                'score_changes': [],
                'success_count': 0,
                'total_count': 0,
                'max_score_achieved': result_score
            }

        move_data = self._memory[state_hash]['moves'][direction]
        move_data['score_changes'].append(score_change)
        move_data['total_count'] += 1

        if result_score > self._memory[state_hash]['best_score']:
            self._memory[state_hash]['best_score'] = result_score

        if result_score > move_data['max_score_achieved']:
            move_data['max_score_achieved'] = result_score
            move_data['success_count'] += 1

        if len(move_data['score_changes']) > 10:
            move_data['score_changes'] = move_data['score_changes'][-5:]

    def remember_failed_move(self, board, next_tile, direction):
        state_hash = self.board_to_hash(board, next_tile)

        if state_hash not in self._memory:
            self._memory[state_hash] = {
                'moves': {},
                'best_score': 0,
                'visit_count': 0
            }

        if direction not in self._memory[state_hash]['moves']:
            self._memory[state_hash]['moves'][direction] = {
                'score_changes': [],
                'success_count': 0,
                'total_count': 0,
                'max_score_achieved': 0
            }

        move_data = self._memory[state_hash]['moves'][direction]
        move_data['total_count'] += 1
        move_data['score_changes'].append(-10)

    def start_new_game(self, board):
        self._move_history = []
        if self._debug:
            print('MemoryStrategy: New game started')

    def end_game(self, final_score, max_tile, total_moves):
        success_rate = self._memory_hits / self._game_states_seen if self._game_states_seen > 0 else 0

        if self._debug:
            print(f'Memory stats: {self._memory_hits}/{self._game_states_seen} hits ({success_rate:.1%})')
            print(f'Memory size: {len(self._memory)} states')

        if max_tile >= 96:
            self.save_memory()
            if self._debug:
                print('Game memory saved')

    def get_memory_stats(self):
        return {
            'states_remembered': len(self._memory),
            'memory_hits': self._memory_hits,
            'game_states_seen': self._game_states_seen,
            'hit_rate': self._memory_hits / max(1, self._game_states_seen)
        }
