import cv2
import json
import numpy as np
import os
import time

from PIL import ImageGrab


class Calibrator:
    def __init__(self):
        self._board_region = None
        self._next_tile_region = None
        self._tile_colors = {}
        self._calibration_dir = 'calibration'

        self._tile_width = None
        self._tile_height = None
        self._gap_x = None
        self._gap_y = None
        self._tile_positions = None

        if not os.path.exists(self._calibration_dir):
            os.makedirs(self._calibration_dir)

    def wait_for_enter(self, message=''):
        if message:
            print(f'\n{message}')
        input('Press Enter to continue...')

    def countdown_timer(self, seconds):
        print(f'Starting in {seconds} seconds... Switch to the game window!')
        for i in range(seconds, 0, -1):
            print(f'{i}...')
            time.sleep(1)
        print('Go!')

    def get_screenshot(self, region=None, filename=None):
        if region:
            screenshot = ImageGrab.grab(bbox=region)
        else:
            screenshot = ImageGrab.grab()

        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        if filename:
            filepath = os.path.join(self._calibration_dir, filename)
            cv2.imwrite(filepath, img)
            print(f'Screenshot saved: {filepath}')

        return img

    def save_image(self, image, filename):
        filepath = os.path.join(self._calibration_dir, filename)
        cv2.imwrite(filepath, image)
        print(f'Image saved: {filepath}')

    def extract_region(self, image, region):
        x1, y1, x2, y2 = region
        return image[y1:y2, x1:x2]

    def draw_region(self, image, region, color=(0, 255, 0), thickness=2):
        x1, y1, x2, y2 = region
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
        return image

    def manual_calibration(self, full_screen):
        print('\n=== MANUAL REGION CALIBRATION ===')

        self.save_image(full_screen, '01_full_screen.png')

        self.wait_for_enter(
            'A screenshot of the entire screen has been saved. '
            'Examine the file and determine the coordinates of the game board.'
        )

        print('Enter the coordinates of the game board in the format: left top right bottom')
        coords = input('Coordinates: ').strip().split()

        if len(coords) == 4:
            self._board_region = tuple(map(int, coords))
            print(f'Game board set: {self._board_region}')
        else:
            self._board_region = (500, 300, 900, 700)
            print(f'Default coordinates are being used: {self._board_region}')

        print('\nEnter the coordinates for the NEXT TILE.')
        print('This is the tile that is shown separately from the game board and will be added after a move.')
        print('Enter the coordinates for the next tile area in the format: left top right bottom')
        coords = input('Coordinates: ').strip().split()

        if len(coords) == 4:
            self._next_tile_region = tuple(map(int, coords))
            print(f'Next tile area set: {self._next_tile_region}')

            left, top, right, bottom = self._next_tile_region
            self._tile_width = right - left
            self._tile_height = bottom - top
            print(f'Tile size from next tile: {self._tile_width}x{self._tile_height}')
        else:
            self._next_tile_region = (950, 400, 1050, 500)
            print(f'Default coordinates are being used: {self._next_tile_region}')

            left, top, right, bottom = self._next_tile_region
            self._tile_width = right - left
            self._tile_height = bottom - top
            print(f'Tile size from next tile: {self._tile_width}x{self._tile_height}')

        marked_screen = full_screen.copy()
        if self._board_region:
            marked_screen = self.draw_region(marked_screen, self._board_region, (0, 255, 0), 3)
        if self._next_tile_region:
            marked_screen = self.draw_region(marked_screen, self._next_tile_region, (255, 0, 0), 3)

        self.save_image(marked_screen, '02_marked_regions.png')

        return self._board_region is not None and self._next_tile_region is not None

    def calculate_grid_parameters(self, board_img):
        print('\n=== CALCULATING GRID PARAMETERS ===')

        if not self._tile_width or not self._tile_height:
            print('Error: Tile size is not defined!')
            return False

        h, w = board_img.shape[:2]

        self._gap_x = (w - 4 * self._tile_width) // 3
        self._gap_y = (h - 4 * self._tile_height) // 3

        print(f'Board size: {w}x{h}')
        print(f'Tile size: {self._tile_width}x{self._tile_height}')
        print(f'Calculated gaps: horizontal={self._gap_x}, vertical={self._gap_y}')

        if self._gap_x < 0 or self._gap_y < 0:
            print('Warning: Calculated gaps are negative! Check your region coordinates.')
            self._gap_x = max(self._gap_x, 1)
            self._gap_y = max(self._gap_y, 1)
            print(f'Adjusted gaps: horizontal={self._gap_x}, vertical={self._gap_y}')

        self._tile_positions = []
        for i in range(4):
            row = []
            for j in range(4):
                left = j * (self._tile_width + self._gap_x)
                top = i * (self._tile_height + self._gap_y)
                right = left + self._tile_width
                bottom = top + self._tile_height
                row.append((left, top, right, bottom))
            self._tile_positions.append(row)

        grid_image = board_img.copy()
        for i in range(4):
            for j in range(4):
                tile_region = self._tile_positions[i][j]
                self.draw_region(grid_image, tile_region, (0, 255, 255), 2)
                cv2.putText(
                    grid_image, f'{i},{j}', (tile_region[0], tile_region[1]-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1
                )

        self.save_image(grid_image, '03_board_grid.png')
        print('Grid visualization saved: 03_board_grid.png')

        if len(self._tile_positions) > 0 and len(self._tile_positions[0]) > 0:
            sample_tile = self.extract_region(board_img, self._tile_positions[0][0])
            self.save_image(sample_tile, '04_sample_tile.png')
            print('Sample tile saved: 04_sample_tile.png')

        return True

    def capture_board_cells(self, full_screen):
        if not self._board_region:
            print('Error: game board region is not set!')
            return False

        print('\n=== CAPTURING GAME BOARD CELLS ===')

        board_img = self.extract_region(full_screen, self._board_region)
        self.save_image(board_img, '03_board_region.png')

        if not self.calculate_grid_parameters(board_img):
            print('Error calculating grid parameters!')
            return False

        self.wait_for_enter('The game board grid has been calculated and visualized.')

        cells = []
        for i in range(4):
            row = []
            for j in range(4):
                tile_region = self._tile_positions[i][j]
                cell_img = self.extract_region(board_img, tile_region)
                filename = f'05_cell_{i}_{j}.png'
                self.save_image(cell_img, filename)
                row.append(cell_img)

                print(f'Cell saved ({i},{j}): {filename}')

            cells.append(row)

        self.wait_for_enter('All cells have been saved. Check the files in the calibration folder.')

        return cells

    def capture_next_tile(self, full_screen):
        if not self._next_tile_region:
            print('Error: next tile region is not set!')
            return None

        print('\n=== CAPTURING NEXT TILE ===')

        next_tile_img = self.extract_region(full_screen, self._next_tile_region)
        self.save_image(next_tile_img, '06_next_tile.png')

        self.wait_for_enter('The next tile has been saved.')

        return next_tile_img

    def analyze_tile_colors(self, cell_images, next_tile_image):
        print('\n=== TILE COLOR ANALYSIS ===')

        color_samples = {}

        for i in range(4):
            for j in range(4):
                cell_img = cell_images[i][j]

                h, w = cell_img.shape[:2]
                margin_h = int(h * 0.1)
                margin_w = int(w * 0.1)
                center_region = cell_img[margin_h:h-margin_h, margin_w:w-margin_w]

                avg_color = np.mean(center_region, axis=(0, 1))

                print(f'Cell ({i},{j}): average BGR color: {avg_color}')

                value = input(f'Enter the tile value in cell ({i},{j}) (0 if empty): ').strip()

                try:
                    tile_value = int(value)
                    if tile_value != 0:
                        if tile_value not in color_samples:
                            color_samples[tile_value] = []
                        color_samples[tile_value].append(avg_color)
                except ValueError:
                    print(f'Skipping cell ({i},{j}) - invalid value')

        if next_tile_image is not None:
            h, w = next_tile_image.shape[:2]
            margin_h = int(h * 0.1)
            margin_w = int(w * 0.1)
            center_region = next_tile_image[margin_h:h-margin_h, margin_w:w-margin_w]
            avg_color = np.mean(center_region, axis=(0, 1))

            print(f'Next tile: average BGR color: {avg_color}')

            value = input('Enter the value of the next tile: ').strip()

            try:
                tile_value = int(value)
                if tile_value != 0:
                    if tile_value not in color_samples:
                        color_samples[tile_value] = []
                    color_samples[tile_value].append(avg_color)
            except ValueError:
                print('Skipping next tile - invalid value')

        if color_samples:
            print('\nUpdating tile colors...')
            for value, colors in color_samples.items():
                avg_color = np.mean(colors, axis=0)

                lower_color = np.clip(avg_color - 10, 0, 255)
                upper_color = np.clip(avg_color + 10, 0, 255)
                self._tile_colors[value] = {
                    'lower': lower_color.tolist(),
                    'upper': upper_color.tolist(),
                    'average': avg_color.tolist()
                }
                print(f'Tile {value}: BGR color {avg_color} -> range {lower_color}-{upper_color}')

        self.wait_for_enter('Color analysis completed.')

        return color_samples

    def recognize_board_from_cells(self, cell_images):
        print('\n=== BOARD RECOGNITION ===')

        board = np.zeros((4, 4), dtype=int)

        for i in range(4):
            for j in range(4):
                cell_img = cell_images[i][j]
                value = self.recognize_tile_value(cell_img, (i, j))
                board[i, j] = value

        print('Recognized board:')
        self.print_board_text(board)

        self.wait_for_enter('Board recognition completed.')

        return board

    def recognize_next_tile(self, next_tile_image):
        if next_tile_image is None:
            print('Error: next tile image not provided!')
            return 0

        value = self.recognize_tile_value(next_tile_image, 'next_tile')
        print(f'Recognized next tile: {value}')

        return value

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
            return 0

        if position:
            print(f'Cell {position}: recognized as {best_match} (distance {min_distance})')

        return best_match

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

    def save_calibration_data(self):
        grid_params = {
            'tile_width': self._tile_width,
            'tile_height': self._tile_height,
            'gap_x': self._gap_x,
            'gap_y': self._gap_y,
            'tile_positions': self._tile_positions
        }

        calibration_data = {
            'board_region': self._board_region,
            'next_tile_region': self._next_tile_region,
            'tile_colors': self._tile_colors,
            'grid_params': grid_params
        }

        filepath = os.path.join(self._calibration_dir, 'calibration_data.json')
        with open(filepath, 'w') as f:
            json.dump(calibration_data, f, indent=4)

        print(f'Calibration data saved to: {filepath}')

    def load_calibration_data(self):
        filepath = os.path.join(self._calibration_dir, 'calibration_data.json')

        if not os.path.exists(filepath):
            print(f'Calibration file not found: {filepath}')
            return False

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

            print('Calibration data loaded successfully')
            return True
        except Exception as e:
            print(f'Error loading calibration data: {e}')
            return False

    def calibrate(self):
        print('=== CALIBRATION MODE ===')
        print('This mode will help configure game recognition.')
        print('Follow the instructions and press Enter to proceed to the next step.')

        self.countdown_timer(5)

        print('Taking a screenshot of the entire screen...')
        full_screen = self.get_screenshot(filename='01_full_screen.png')

        full_screen = cv2.imread('./game_over_20251016_122012.png')
        if not self.manual_calibration(full_screen):
            print('Region calibration error!')
            return False

        cell_images = self.capture_board_cells(full_screen)
        if not cell_images:
            print('Error capturing board cells!')
            return False

        next_tile_img = self.capture_next_tile(full_screen)

        self.analyze_tile_colors(cell_images, next_tile_img)

        self.recognize_board_from_cells(cell_images)

        if next_tile_img is not None:
            next_tile_value = self.recognize_next_tile(next_tile_img)
            print(f'\nRecognized next tile: {next_tile_value}')

        self.save_calibration_data()

        print('\n=== CALIBRATION COMPLETED ===')
        print(
            'Coordinates and colors have been saved. '
            'You can now run the program without the -c flag for automatic play.'
        )

        return True
