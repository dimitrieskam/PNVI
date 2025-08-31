import tkinter as tk
import random
from math import atan2, degrees, sqrt

CELL_SIZE = 60
ROWS, COLS = 10, 10
BOARD_SIZE = CELL_SIZE * ROWS


class SnakeLadderGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snakes and Ladders")

        self.canvas = tk.Canvas(root, width=BOARD_SIZE, height=BOARD_SIZE, bg="white")
        self.canvas.pack()

        self.create_board()
        self.create_snakes_and_ladders()

        self.players = [
            self.canvas.create_oval(5, 5, 25, 25, fill="red"),
            self.canvas.create_oval(30, 5, 50, 25, fill="blue")
        ]
        self.positions = [1, 1]

        self.current_player = 0

        self.roll_button = tk.Button(root, text="Roll Dice", command=self.roll_dice)
        self.roll_button.pack()

        self.dice_label = tk.Label(root, text="Dice: -", font=("Arial", 14))
        self.dice_label.pack()

    def create_board(self):
        """Draws 10x10 numbered board with alternating directions"""
        for row in range(ROWS):
            for col in range(COLS):
                x1 = col * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                color = "lightyellow" if (row + col) % 2 == 0 else "lightgreen"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

                # Calculate proper board number (snake numbering)
                num = ROWS * COLS - (row * COLS + col)
                if row % 2 == 1:
                    num = ROWS * COLS - (row * COLS + (COLS - col - 1))

                self.canvas.create_text(
                    x1 + CELL_SIZE / 2, y1 + CELL_SIZE / 2, text=str(num), font=("Arial", 10, "bold")
                )

    def create_snakes_and_ladders(self):
        """Define ladders and snakes"""
        self.ladders = {3: 22, 8: 26, 20: 41, 36: 55, 43: 77, 50: 70, 71: 92}
        self.snakes = {17: 4, 29: 9, 54: 34, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 99: 78}

        # Draw ladders
        for start, end in self.ladders.items():
            self.draw_line_symbol(start, end, "brown")  # Ladder = brown

        # Draw snakes
        for start, end in self.snakes.items():
            self.draw_line_symbol(start, end, "green")  # Snake = green

    def draw_line_symbol(self, start, end, color):
        """Draws a smaller snake/ladder aligned between start and end cells."""
        start_x, start_y = self.get_coords(start)
        end_x, end_y = self.get_coords(end)

        # Shrink factor (make line shorter so it fits nicely in the cells)
        shrink = 15
        dx, dy = end_x - start_x, end_y - start_y
        dist = sqrt(dx ** 2 + dy ** 2)

        if dist != 0:
            # Normalize vector
            dx /= dist
            dy /= dist

            # Move start/end points inward by shrink pixels
            start_x += dx * shrink
            start_y += dy * shrink
            end_x -= dx * shrink
            end_y -= dy * shrink

        # Draw ladder (parallel lines + rungs) or snake (curved/zigzag line)
        if color == "brown":  # Ladder
            offset = 8  # width between ladder rails
            # Parallel lines (ladder rails)
            self.canvas.create_line(start_x - offset, start_y - offset,
                                    end_x - offset, end_y - offset,
                                    width=3, fill=color)
            self.canvas.create_line(start_x + offset, start_y + offset,
                                    end_x + offset, end_y + offset,
                                    width=3, fill=color)

            # Rungs every ~20px
            steps = int(dist // 20)
            for i in range(1, steps):
                rung_x = start_x + dx * i * 20
                rung_y = start_y + dy * i * 20
                self.canvas.create_line(rung_x - offset, rung_y - offset,
                                        rung_x + offset, rung_y + offset,
                                        width=2, fill=color)

        else:  # Snake (green)
            # Draw a wavy snake line instead of a straight arrow
            points = []
            steps = int(dist // 15)
            for i in range(steps + 1):
                t = i / steps
                px = start_x + dx * dist * t
                py = start_y + dy * dist * t
                # Snake wiggle
                px += 10 * (1 - t) * (1 if i % 2 == 0 else -1)
                points.extend([px, py])

            self.canvas.create_line(points, smooth=True, width=4, fill=color)
            # Snake head
            self.canvas.create_oval(end_x - 10, end_y - 10, end_x + 10, end_y + 10, fill=color)

    def get_coords(self, pos):
        """Convert board position number to (x,y) canvas coordinates (center of cell)."""
        row = (pos - 1) // COLS
        col = (pos - 1) % COLS

        # Handle zig-zag numbering
        if row % 2 == 1:
            col = COLS - 1 - col

        x = col * CELL_SIZE + CELL_SIZE / 2
        y = BOARD_SIZE - (row * CELL_SIZE + CELL_SIZE / 2)
        return x, y

    def roll_dice(self):
        roll = random.randint(1, 6)
        self.dice_label.config(text=f"Dice: {roll}")
        self.move_player(roll)

    def move_player(self, steps):
        old_pos = self.positions[self.current_player]
        pos = old_pos + steps

        if pos > 100:
            pos = 100

        # Check for ladders and snakes
        if pos in self.ladders:
            pos = self.ladders[pos]
            self.dice_label.config(text=f"Climbed ladder to {pos}!")
        elif pos in self.snakes:
            pos = self.snakes[pos]
            self.dice_label.config(text=f"Hit snake down to {pos}!")

        self.positions[self.current_player] = pos
        x, y = self.get_coords(pos)

        # Move player token
        self.canvas.coords(self.players[self.current_player], x - 10, y - 10, x + 10, y + 10)

        # Check win
        if pos == 100:
            self.dice_label.config(text=f"Player {self.current_player + 1} Wins!")
            self.roll_button.config(state="disabled")
            return

        # Switch player
        self.current_player = 1 - self.current_player


if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeLadderGame(root)
    root.mainloop()
