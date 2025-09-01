import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import requests
from snake_ladder_game import SnakeLadderGame
import threading
import websocket
from websocket import WebSocketApp
import pyperclip

SERVER_URL = "http://localhost:8000"

class GameClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login/Register")
        self.show_register_window()

    def show_register_window(self):
        self.clear_window()
        tk.Label(self.root, text="Register", font=("Arial", 16)).pack(pady=10)

        username_entry = tk.Entry(self.root)
        password_entry = tk.Entry(self.root, show="*")
        username_entry.pack(pady=5)
        password_entry.pack(pady=5)

        def attempt_register():
            username = username_entry.get()
            password = password_entry.get()
            r = requests.post(f"{SERVER_URL}/register", params={"username": username, "password": password})
            if r.status_code == 200 and r.json().get("status") == "success":
                messagebox.showinfo("Success", "Registration successful!")
                self.show_login_window()
            else:
                messagebox.showerror("Error", r.json().get("message", "Unknown error"))

        tk.Button(self.root, text="Register", command=attempt_register).pack(pady=10)
        tk.Button(self.root, text="Already registered? Login", command=self.show_login_window).pack()

    def show_login_window(self):
        self.clear_window()
        tk.Label(self.root, text="Login", font=("Arial", 16)).pack(pady=10)

        username_entry = tk.Entry(self.root)
        password_entry = tk.Entry(self.root, show="*")
        username_entry.pack(pady=5)
        password_entry.pack(pady=5)

        def attempt_login():
            username = username_entry.get()
            password = password_entry.get()
            r = requests.post(f"{SERVER_URL}/login", params={"username": username, "password": password})
            if r.status_code == 200 and r.json().get("status") == "success":
                self.username = username  # зачува име
                self.avatar = r.json().get("avatar", "🙂")  # зачува аватар, default 🙂
                messagebox.showinfo("Success", "Login successful!")
                self.show_main_menu()
            else:
                messagebox.showerror("Error", r.json().get("message", "Unknown error"))

        tk.Button(self.root, text="Login", command=attempt_login).pack(pady=10)
        tk.Button(self.root, text="Back to Register", command=self.show_register_window).pack()

    def show_main_menu(self):
        self.clear_window()
        tk.Label(self.root, text=f"{self.avatar} {self.username}", font=("Arial", 14)).pack(pady=5)

        tk.Label(self.root, text="Snake & Ladder - Main Menu", font=("Arial", 18)).pack(pady=20)
        tk.Label(self.root, text="Invite players and start the game!", font=("Arial", 12)).pack(pady=5)

        tk.Button(self.root, text="🎮 Create Game Session", font=("Arial", 14), command=self.create_game_session).pack(
            pady=10)
        tk.Button(self.root, text="🔗 Join via Invite Link", font=("Arial", 14), command=self.join_game_session).pack(
            pady=10)
        tk.Button(self.root, text="👤 Edit Profile", command=self.show_profile_window).pack(pady=10)
        tk.Button(self.root, text="Logout", command=self.show_login_window).pack(pady=10)
    def create_game_session(self):
        try:
            r = requests.post(f"{SERVER_URL}/create_session")
            if r.status_code == 200:
                session_info = r.json()
                invite_link = session_info["invite_link"]
                session_id = session_info["session_id"]

                # Автоматски го копира линкот во clipboard
                pyperclip.copy(invite_link)

                # Покажува прозорец со линкот и копче за повторно копирање
                def copy_link():
                    pyperclip.copy(invite_link)
                    messagebox.showinfo("Copied", "Invite link copied to clipboard!")

                invite_window = tk.Toplevel(self.root)
                invite_window.title("Invite Link")
                invite_window.geometry("400x150")

                tk.Label(invite_window, text="Share this link with your friend:", font=("Arial", 12)).pack(pady=10)
                link_entry = tk.Entry(invite_window, width=50)
                link_entry.insert(0, invite_link)
                link_entry.pack(pady=5)
                tk.Button(invite_window, text="Copy to Clipboard", command=copy_link).pack(pady=10)

                self.start_game(session_id)
            else:
                messagebox.showerror("Error", "Failed to create game session.")
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def join_game_session(self):
        invite_link = simpledialog.askstring("Join Game", "Paste Invite Link:")
        if invite_link:
            session_id = invite_link.split("/")[-1]
            self.start_game(session_id)

    def start_game(self, session_id):
        self.session_id = session_id
        self.root.withdraw()

        # Create the game window
        game_window = tk.Toplevel(self.root)
        game_window.title("Snake & Ladder")

        # WebSocket URL
        ws_url = f"ws://localhost:8000/ws/{session_id}"

        # Create game instance
        self.game_instance = SnakeLadderGame(game_window)

        # Attach ws reference to game instance
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_ws_message,
            on_close=lambda ws: print("Disconnected from session."),
            on_open=lambda ws: print("Connected to session.")
        )
        self.game_instance.ws = self.ws

        # Покажи играчот (avatar + username) на прозорецот на играта
        player_label = tk.Label(game_window, text=f"{self.avatar} {self.username}", font=("Arial", 14))
        player_label.pack(pady=5)

        # Run WebSocket in background
        threading.Thread(target=self.ws.run_forever, daemon=True).start()
    def show_profile_window(self):
        profile_window = tk.Toplevel(self.root)
        profile_window.title("Player Profile")
        profile_window.geometry("300x400")

        tk.Label(profile_window, text="Choose Avatar (emoji):", font=("Arial", 12)).pack(pady=5)

        # фиксен сет на emojis
        avatars = ["🙂", "😎", "🤖", "🐍", "🐱", "🐯", "🐸", "🐧"]
        selected_avatar = tk.StringVar(value=avatars[0])  # default

        # правиме копчиња за избор
        avatar_frame = tk.Frame(profile_window)
        avatar_frame.pack(pady=5)
        for emoji in avatars:
            b = tk.Radiobutton(
                avatar_frame,
                text=emoji,
                variable=selected_avatar,
                value=emoji,
                indicatoron=False,
                font=("Arial", 20),
                width=3,
                relief="raised",
                selectcolor="lightblue"
            )
            b.pack(side="left", padx=2)

        tk.Label(profile_window, text="Custom Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(profile_window)
        name_entry.insert(0, self.username if hasattr(self, "username") else "")  # тековно корисничко име
        name_entry.pack(pady=5)

        def save_profile():
            avatar = selected_avatar.get()
            name = name_entry.get()

            r = requests.post(f"{SERVER_URL}/update_profile",
                              params={"username": self.username, "avatar": avatar, "new_name": name})
            if r.status_code == 200 and r.json().get("status") == "success":
                # Ажурирај локално
                self.avatar = avatar
                self.username = name
                messagebox.showinfo("Saved", f"Profile updated!\nName: {name}\nAvatar: {avatar}")
            else:
                messagebox.showerror("Error", r.json().get("message", "Failed to update profile"))

            profile_window.destroy()
            # Рендерирај повторно главното мени со новите податоци
            self.show_main_menu()

        tk.Button(profile_window, text="Save", command=save_profile).pack(pady=10)

        # пример статистика (од сервер)
        r = requests.get(f"{SERVER_URL}/stats", params={"username": self.username})
        if r.status_code == 200:
            stats = r.json()
            tk.Label(profile_window, text="Your Stats:", font=("Arial", 12, "bold")).pack(pady=10)
            tk.Label(profile_window, text=f"Wins: {stats['wins']}").pack()
            tk.Label(profile_window, text=f"Losses: {stats['losses']}").pack()
            if stats["fastest_win_seconds"] < 9999:
                tk.Label(profile_window, text=f"Fastest Win: {stats['fastest_win_seconds']}s").pack()
    def on_ws_message(self, ws, message):

        if hasattr(self, "game_instance"):
            self.game_instance.move_player(int(message))

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = GameClient()
    client.run()