import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import random
import os
import math

# import winsound # winsound is Windows-specific, so it's commented out for broader compatibility.

# Constants
BOARD_SIZE = 600
TILE_SIZE = BOARD_SIZE // 10
# UPDATED ASSET_PATH to the user-provided absolute directory
ASSET_PATH = "snake_ladder_assets/"

# Define snakes and ladders with their start and end positions
snakes = {98: 78, 95: 56, 87: 24, 64: 60, 62: 19}
ladders = {4: 14, 9: 31, 28: 84, 51: 67, 71: 91, 80: 100}

class SnakeLadderGame:
    def __init__(self, root, websocket_connection=None):
        self.ws = websocket_connection
        self.root = root
        self.root.title("🐍 Snake & Ladder with Image-Based Spanning Design")
        self.root.geometry(f"{BOARD_SIZE + 200}x{BOARD_SIZE + 150}")

        self.game_frame = tk.Frame(root, bg="#f0f0f0", padx=10, pady=10, relief=tk.RAISED, borderwidth=2)
        self.game_frame.pack(expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(self.game_frame, width=BOARD_SIZE, height=BOARD_SIZE, bg="white",
                                highlightbackground="black", highlightthickness=1)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)

        self.controls_frame = tk.Frame(self.game_frame, bg="#e0e0e0", padx=10, pady=10)
        self.controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.draw_board()
        self.load_images()
        self.draw_snakes_and_ladders()

        self.positions = [0, 0]
        self.tokens = [
            self.canvas.create_oval(10, 10, 30, 30, fill='red', outline='darkred', width=2, tags="player0"),
            self.canvas.create_oval(30, 10, 50, 30, fill='blue', outline='darkblue', width=2, tags="player1")
        ]

        self.dice_value = 0
        self.current_player = 0
        self.movable = False

        self.dice_label = tk.Label(self.controls_frame, bg="#e0e0e0")
        self.dice_label.pack(pady=20)

        self.roll_button = tk.Button(self.controls_frame, text="🎲 Roll Dice", command=self.roll_dice,
                                     font=("Arial", 14, "bold"), bg="#4CAF50", fg="white",
                                     activebackground="#45a049", activeforeground="white",
                                     relief=tk.RAISED, bd=3, padx=10, pady=5)
        self.roll_button.pack(pady=10)

        self.reset_button = tk.Button(self.controls_frame, text="🔁 Reset Game", command=self.reset_game,
                                      font=("Arial", 12), bg="#f44336", fg="white",
                                      activebackground="#da190b", activeforeground="white",
                                      relief=tk.RAISED, bd=3, padx=10, pady=5)
        self.reset_button.pack(pady=10)

        self.status_label = tk.Label(self.controls_frame, text="Player 1's turn", font=("Arial", 14, "bold"),
                                     bg="#e0e0e0", fg="navy")
        self.status_label.pack(pady=20)

        self.canvas.tag_bind("player0", "<Button-1>", lambda e: self.try_move(0))
        self.canvas.tag_bind("player1", "<Button-1>", lambda e: self.try_move(1))

        self.move_token(0)
        self.move_token(1)

    def create_dice_image(self, value, size=60):
        """Creates a PIL Image of a dice face with dots."""
        img = Image.new('RGB', (size, size), 'white')
        draw = ImageDraw.Draw(img)
        dot_radius = size // 10
        center = size // 2
        offset = size // 4

        draw.rectangle([0, 0, size - 1, size - 1], outline='black', width=2)

        dots = {
            1: [(center, center)],
            2: [(center - offset, center - offset), (center + offset, center + offset)],
            3: [(center - offset, center - offset), (center, center), (center + offset, center + offset)],
            4: [(center - offset, center - offset), (center + offset, center - offset),
                (center - offset, center + offset), (center + offset, center + offset)],
            5: [(center - offset, center - offset), (center + offset, center - offset),
                (center - offset, center + offset), (center + offset, center + offset),
                (center, center)],
            6: [(center - offset, center - offset), (center + offset, center - offset),
                (center - offset, center), (center + offset, center),
                (center - offset, center + offset), (center + offset, center + offset)]
        }

        for x, y in dots[value]:
            draw.ellipse((x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius), fill='black')
        return ImageTk.PhotoImage(img)

    def make_image_background_transparent(self, image, color_to_remove=(0, 0, 0), tolerance=10):
        """
        Makes a specific color in an image transparent.
        Args:
            image (PIL.Image.Image): The input image.
            color_to_remove (tuple): The RGB color to make transparent (e.g., (0, 0, 0) for black).
            tolerance (int): How much deviation from color_to_remove is allowed.
        Returns:
            PIL.Image.Image: The image with the specified color made transparent.
        """
        image = image.convert("RGBA")
        datas = image.getdata()

        new_data = []
        for item in datas:
            # Check if the pixel color is close to the color_to_remove within tolerance
            r_diff = abs(item[0] - color_to_remove[0])
            g_diff = abs(item[1] - color_to_remove[1])
            b_diff = abs(item[2] - color_to_remove[2])

            if r_diff <= tolerance and g_diff <= tolerance and b_diff <= tolerance:
                new_data.append((255, 255, 255, 0))  # Make transparent (R, G, B, Alpha=0)
            else:
                new_data.append(item)

        image.putdata(new_data)
        return image

    def load_images(self):
        """Loads and prepares dice images and snake/ladder images for dynamic drawing."""
        self.dice_images = [self.create_dice_image(i, size=80) for i in range(1, 7)]

        try:
            # Load the base snake image
            self.base_snake_img = Image.open(os.path.join(ASSET_PATH, "snake_big.png")).convert("RGBA")

            # Load the base ladder image (now correctly .png)
            ladder_img_path = os.path.join(ASSET_PATH, "ladder_big.png")  # Changed to .png
            self.base_ladder_img = Image.open(ladder_img_path).convert("RGBA")
            # Apply transparency function to the ladder image, targeting dark grey/black
            self.base_ladder_img = self.make_image_background_transparent(self.base_ladder_img,
                                                                          color_to_remove=(0, 0, 0), tolerance=50)


        except FileNotFoundError as e:
            print(
                f"Error loading image: {e}. Make sure 'snake_big.png' and 'ladder_big.png' are in the '{ASSET_PATH}' directory.")  # Updated error message
            # Fallback to placeholder images if files are not found
            self.base_snake_img = Image.new('RGBA', (100, 100), (255, 0, 0, 128))  # Semi-transparent red
            self.base_ladder_img = Image.new('RGBA', (100, 100), (0, 255, 0, 128))  # Semi-transparent green

    def draw_board(self):
        """Draws the 10x10 game board with alternating colors and numbers."""
        colors = ['#e0f7fa', '#b2ebf2', '#80deea', '#4dd0e1', '#26c6da']  # Shades of blue/cyan
        for row in range(10):
            for col in range(10):
                x1 = col * TILE_SIZE
                y1 = (9 - row) * TILE_SIZE

                x2 = x1 + TILE_SIZE
                y2 = y1 + TILE_SIZE

                if row % 2 == 0:
                    index = row * 10 + col + 1
                else:
                    index = row * 10 + (9 - col) + 1

                color = colors[(row + col) % len(colors)]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='black', width=1)
                self.canvas.create_text(x1 + TILE_SIZE // 2, y1 + TILE_SIZE // 2,
                                        text=str(index), font=("Arial", 10, "bold"), fill="black")

    def get_tile_center_coords(self, pos):
        """Calculates the center (x, y) coordinates for a given board position."""
        if pos < 1:  # For position 0 (start)
            return self.get_tile_center_coords(1)

        pos -= 1  # Adjust to 0-indexed for calculation (0-99)
        row = pos // 10

        if row % 2 == 0:  # Even rows (0, 2, 4...) go left-to-right
            col = pos % 10
        else:  # Odd rows (1, 3, 5...) go right-to-left
            col = 9 - (pos % 10)

        x = col * TILE_SIZE + TILE_SIZE // 2
        y = BOARD_SIZE - (row * TILE_SIZE + TILE_SIZE // 2)
        return x, y

    def draw_snakes_and_ladders(self):
        """Draws snakes and ladders using transformed images."""
        self.snake_photo_images = []  # Store references to prevent garbage collection
        self.ladder_photo_images = []  # Store references to prevent garbage collection

        # Draw snakes
        for start_pos, end_pos in snakes.items():
            start_x, start_y = self.get_tile_center_coords(start_pos)
            end_x, end_y = self.get_tile_center_coords(end_pos)

            # Calculate distance and angle
            dx = end_x - start_x
            dy = end_y - start_y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)

            # Determine scaling factors
            original_width, original_height = self.base_snake_img.size

            scale_factor_height = distance / original_height
            new_width = int(original_width * scale_factor_height * 0.5)  # Adjust width to make it thinner
            new_height = int(distance)

            transformed_snake_img = self.base_snake_img.resize((new_width, new_height), Image.LANCZOS)

            rotation_angle = angle_deg - 90  # Adjust based on the image's inherent orientation

            transformed_snake_img = transformed_snake_img.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)

            photo_image = ImageTk.PhotoImage(transformed_snake_img)
            self.snake_photo_images.append(photo_image)  # Keep a reference!

            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            self.canvas.create_image(mid_x, mid_y, image=photo_image, tags="snake_image")

        # Draw ladders
        for start_pos, end_pos in ladders.items():
            start_x, start_y = self.get_tile_center_coords(start_pos)
            end_x, end_y = self.get_tile_center_coords(end_pos)

            dx = end_x - start_x
            dy = end_y - start_y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)

            original_width, original_height = self.base_ladder_img.size

            scale_factor_height = distance / original_height
            new_width = int(original_width * scale_factor_height * 0.5)  # Adjust width
            new_height = int(distance)

            transformed_ladder_img = self.base_ladder_img.resize((new_width, new_height), Image.LANCZOS)

            rotation_angle = angle_deg - 90  # Adjust based on image orientation

            transformed_ladder_img = transformed_ladder_img.rotate(rotation_angle, expand=True, resample=Image.BICUBIC)

            photo_image = ImageTk.PhotoImage(transformed_ladder_img)
            self.ladder_photo_images.append(photo_image)  # Keep a reference!

            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            self.canvas.create_image(mid_x, mid_y, image=photo_image, tags="ladder_image")

        # Ensure tokens are drawn on top
        self.canvas.tag_raise("player0")
        self.canvas.tag_raise("player1")

    def roll_dice(self):
        """Simulates rolling the dice with an animation."""
        if self.ws:
            self.ws.send("ROLL_DICE")
        if self.movable:
            self.status_label.config(text="Please move your player first!")
            return

        self.roll_button.config(state=tk.DISABLED)
        self.animate_dice()

    def animate_dice(self, frame=0):
        """Animates the dice rolling."""
        if frame < 15:
            value = random.randint(1, 6)
            self.dice_label.config(image=self.dice_images[value - 1])
            self.root.after(70, lambda: self.animate_dice(frame + 1))
        else:
            self.dice_value = random.randint(1, 6)
            self.dice_label.config(image=self.dice_images[self.dice_value - 1])
            self.status_label.config(
                text=f"Player {self.current_player + 1} rolled {self.dice_value}. Click your token to move.")
            self.movable = True
            self.roll_button.config(state=tk.NORMAL)

    def try_move(self, player):
        """Attempts to move the selected player's token."""
        if player != self.current_player or not self.movable:
            self.status_label.config(text=f"It's Player {self.current_player + 1}'s turn to move!")
            return

        current_pos = self.positions[player]
        next_pos = current_pos + self.dice_value

        if next_pos > 100:
            self.status_label.config(text=f"Player {player + 1} cannot move (overshot 100).")
            self.movable = False
            self.switch_turn()
            return

        self.animate_token_move(player, current_pos, next_pos)

    def animate_token_move(self, player, start_pos, end_pos, step=0):
        """Animates the token moving tile by tile."""
        if step < self.dice_value:
            intermediate_pos = start_pos + step + 1
            self.positions[player] = intermediate_pos
            self.move_token(player)
            self.root.after(150, lambda: self.animate_token_move(player, start_pos, end_pos, step + 1))
        else:
            final_pos = end_pos

            if final_pos in ladders:
                final_pos = ladders[final_pos]
                self.status_label.config(text=f"Player {player + 1} climbed to {final_pos}! 🚀")
            elif final_pos in snakes:
                final_pos = snakes[final_pos]
                self.status_label.config(text=f"Player {player + 1} bitten! 🐍 Falls to {final_pos}!")
            else:
                self.status_label.config(text=f"Player {player + 1} moved to {final_pos}.")

            # Update position and redraw token
            self.positions[player] = final_pos
            self.move_token(player)

            self.movable = False

            if final_pos == 100:
                self.status_label.config(text=f"🎉 Player {player + 1} wins! 🎉")
                self.roll_button.config(state=tk.DISABLED)
            else:
                self.switch_turn()

    def move_token(self, player):
        """Updates the visual position of a player's token on the canvas."""
        x, y = self.get_tile_center_coords(self.positions[player])
        # Adjust offset for each player to prevent overlap
        offset_x = -10 if player == 0 else 10
        offset_y = -10 if player == 0 else 10
        self.canvas.coords(self.tokens[player], x + offset_x - 10, y + offset_y - 10,
                           x + offset_x + 10, y + offset_y + 10)

    def switch_turn(self):
        """Switches the active player and updates the status label."""
        self.current_player = 1 - self.current_player
        self.status_label.config(text=f"Player {self.current_player + 1}'s turn")

    def reset_game(self):
        """Resets the game to its initial state."""
        self.positions = [0, 0]
        self.move_token(0)
        self.move_token(1)
        self.current_player = 0
        # Corrected indentation for these lines
        self.movable = False
        self.status_label.config(text="Game reset. Player 1's turn.")
        self.dice_label.config(image='')
        self.roll_button.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeLadderGame(root)
    root.mainloop()