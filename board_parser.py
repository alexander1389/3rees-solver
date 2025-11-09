import cv2
import json
import numpy as np
import os
import time

from datetime import datetime
from PIL import ImageGrab


class BoardParser:
    def __init__(self, calibration_dir='calibration', debug=True):
        self._calibration_dir = calibration_dir
        self._debug = debug
        self._board_region = None
        self._next_tile_region = None
        self._tile_colors = {}
        self._scale_factor = 0.5

        self._tile_width = None
        self._tile_height = None
        self._gap_x = None
        self._gap_y = None
        self._tile_positions = None

        self._debug_dir = os.path.join(calibration_dir, 'debug')
        if debug and not os.path.exists(self._debug_dir):
            os.makedirs(self._debug_dir)

        self.load_calibration_data()

    def _adjust_region_for_retina(self, region):
        if region is None:
            return None

        left, top, right, bottom = region
        scaled_region = (
            int(left * self._scale_factor),
            int(top * self._scale_factor),
            int(right * self._scale_factor),
            int(bottom * self._scale_factor)
        )

        if self._debug:
            print(f'Original region: {region}')
            print(f'Scaled region: {scaled_region}')
            print(f'Scale factor: {self._scale_factor}')

        return scaled_region

    def load_calibration_data(self):
        filepath = os.path.join(self._calibration_dir, 'calibration_data.json')

        if not os.path.exists(filepath):
            raise FileNotFoundError(f'Calibration file not found: {filepath}. Run the calibration first.')

        try:
            with open(filepath, 'r') as f:
                calibration_data = json.load(f)

            self._board_region = tuple(calibration_data['board_region'])
            self._next_tile_region = tuple(calibration_data['next_tile_region'])
            self._tile_colors = calibration_data['tile_colors']

            if 'grid_params' in calibration_data:
                grid_params = calibration_data['grid_params']
                self._tile_width = grid_params['tile_width']
                self._tile_height = grid_params['tile_height']
                self._gap_x = grid_params['gap_x']
                self._gap_y = grid_params['gap_y']
                self._tile_positions = grid_params['tile_positions']

            if self._debug:
                print('Calibration data loaded successfully')
                if self._tile_positions:
                    print(
                        f'Grid parameters: tile_size={self._tile_width}x{self._tile_height}, '
                        f'gaps=({self._gap_x}, {self._gap_y})'
                    )

            return True
        except Exception as e:
            raise Exception(f'Error loading calibration data: {e}')

    def countdown_timer(self, seconds):
        print(f'Starting in {seconds} seconds... Switch to the game window!')
        for i in range(seconds, 0, -1):
            print(f'{i}...')
            time.sleep(1)
        print('Go!')

    def get_screenshot(self, region=None, filename=None):
        try:
            adjusted_region = self._adjust_region_for_retina(region)

            if adjusted_region:
                left, top, right, bottom = adjusted_region
                if left >= right or top >= bottom:
                    raise ValueError(f'Invalid region: {adjusted_region}')
                screenshot = ImageGrab.grab(bbox=adjusted_region)
            else:
                screenshot = ImageGrab.grab()

            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            if filename and self._debug:
                filepath = os.path.join(self._debug_dir, filename)
                cv2.imwrite(filepath, img)
                print(f'Screenshot saved: {filepath}')
            return img
        except Exception as e:
            raise Exception(f'Error capturing screenshot of region {adjusted_region}: {e}')

    def draw_region(self, image, region, color=(0, 255, 0), thickness=2, label=None):
        x1, y1, x2, y2 = region
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)

        if label and self._debug:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_thickness = 2

            text_x = x1
            text_y = y1 - 10 if y1 - 10 > 10 else y1 + 20

            text_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
            cv2.rectangle(
                image,
                (text_x, text_y - text_size[1] - 5),
                (text_x + text_size[0], text_y + 5),
                color, -1
            )

            cv2.putText(image, label, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)

        return image

    def create_debug_screenshot(self):
        if not self._debug:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        full_screen = self.get_screenshot(filename=f'debug_full_{timestamp}.png')

        debug_image = full_screen.copy()

        if self._board_region:
            debug_image = self.draw_region(
                debug_image, self._board_region,
                color=(0, 255, 0), thickness=3,
                label='Board'
            )

        if self._next_tile_region:
            debug_image = self.draw_region(
                debug_image, self._next_tile_region,
                color=(255, 0, 0), thickness=3,
                label='Next Tile'
            )

        if self._tile_positions and self._debug:
            for i in range(4):
                for j in range(4):
                    tile_left, tile_top, tile_right, tile_bottom = self._tile_positions[i][j]
                    abs_left = self._board_region[0] + tile_left
                    abs_top = self._board_region[1] + tile_top
                    abs_right = self._board_region[0] + tile_right
                    abs_bottom = self._board_region[1] + tile_bottom
                    abs_tile_region = (abs_left, abs_top, abs_right, abs_bottom)

                    self.draw_region(
                        debug_image, abs_tile_region,
                        color=(255, 255, 0), thickness=1,
                        label=f'{i},{j}'
                    )

        debug_filepath = os.path.join(self._debug_dir, f'debug_regions_{timestamp}.png')
        cv2.imwrite(debug_filepath, debug_image)
        print(f'Debug screenshot saved: {debug_filepath}')

        if self._board_region:
            try:
                self.get_screenshot(
                    self._board_region, filename=f'debug_board_{timestamp}.png')
            except Exception as e:
                print(f'Failed to save game board screenshot: {e}')

        if self._next_tile_region:
            try:
                self.get_screenshot(
                    self._next_tile_region, filename=f'debug_next_tile_{timestamp}.png')
            except Exception as e:
                print(f'Failed to save next tile screenshot: {e}')

    def recognize_tile_value(self, cell_image, position=None):
        h, w = cell_image.shape[:2]
        margin_h = int(h * 0.1)
        margin_w = int(w * 0.1)
        center_region = cell_image[margin_h:h-margin_h, margin_w:w-margin_w]

        avg_color = np.mean(center_region, axis=(0, 1))

        if np.mean(avg_color) > 240:
            return 0

        best_match = 0
        min_distance = float('inf')

        for value, color_data in self._tile_colors.items():
            if value == 0:
                continue

            target_color = np.array(color_data['average'])
            distance = np.linalg.norm(avg_color - target_color)

            if distance < min_distance:
                min_distance = distance
                best_match = value

        threshold = 40

        if min_distance > threshold:
            if self._debug and position:
                print(f'Cell {position}: no good match (min distance {min_distance}), returning 0')
            return 0

        if self._debug and position:
            print(f'Cell {position}: recognized as {best_match} (distance {min_distance})')

        return best_match

    def parse_board(self):
        if not self._board_region:
            raise ValueError('Game board region is not set!')

        if not self._tile_positions:
            raise ValueError('Tile grid parameters are not set! Run calibration first.')

        start_time = time.time()

        board_img = self.get_screenshot(self._board_region)
        board = np.zeros((4, 4), dtype=int)

        for i in range(4):
            for j in range(4):
                tile_left, tile_top, tile_right, tile_bottom = self._tile_positions[i][j]

                scaled_left = int(tile_left * self._scale_factor)
                scaled_top = int(tile_top * self._scale_factor)
                scaled_right = int(tile_right * self._scale_factor)
                scaled_bottom = int(tile_bottom * self._scale_factor)

                cell_img = board_img[scaled_top:scaled_bottom, scaled_left:scaled_right]
                board[i, j] = self.recognize_tile_value(cell_img, (i, j))

        parse_time = time.time() - start_time

        return board, parse_time

    def parse_next_tile(self):
        if not self._next_tile_region:
            raise ValueError('Next tile region is not set!')

        start_time = time.time()

        next_tile_img = self.get_screenshot(self._next_tile_region)
        next_tile_value = self.recognize_tile_value(next_tile_img, 'next_tile')

        parse_time = time.time() - start_time

        return next_tile_value, parse_time

    def print_board_text(self, board):
        print('+' + '------+' * 4)
        for i in range(4):
            row_str = '|'
            for j in range(4):
                if board[i, j] == 0:
                    row_str += '      |'
                else:
                    row_str += f' {board[i, j]:4} |'
            print(row_str)
            print('+' + '------+' * 4)

    def parse_board_state(self):
        if self._debug:
            print('=== PARSING BOARD STATE ===')

        self.countdown_timer(5)

        self.create_debug_screenshot()

        start_time = time.time()
        board, board_time = self.parse_board()
        next_tile, next_tile_time = self.parse_next_tile()
        total_time = time.time() - start_time

        if self._debug:
            print('\nRecognized board:')
            self.print_board_text(board)
            print(f'\nNext tile: {next_tile}')

            print('\n=== EXECUTION TIME ===')
            print(f'Board parsing: {board_time:.3f} sec')
            print(f'Next tile parsing: {next_tile_time:.3f} sec')
            print(f'Total time: {total_time:.3f} sec')

        return {
            'board': board,
            'next_tile': next_tile,
            'timing': {
                'board': board_time,
                'next_tile': next_tile_time,
                'total': total_time
            }
        }
