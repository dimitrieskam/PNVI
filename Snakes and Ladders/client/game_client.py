# client/game_client.py
import json
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import requests
import websocket
from snake_ladder_game import SnakeLadderGame  # your existing UI/game class
import pyperclip

SERVER_URL = "http://localhost:8000"

class GameClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Login/Register")
        self.user_id = None
        self.username = None
        self.ws = None
        self.game = None
        self.show_register_window()

    def show_register_window(self):
        self.clear_window()
        tk.Label(self.root, text="Register", font=("Arial", 16)).pack(pady=10)

        username_entry = tk.Entry(self.root)
        password_entry = tk.Entry(self.root, show="*")
        username_entry.pack(pady=5)
        password_entry.pack(pady=5)

        def attempt_register():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
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
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            r = requests.post(f"{SERVER_URL}/login", params={"username": username, "password": password})
            data = r.json()
            if r.status_code == 200 and data.get("status") == "success":
                self.user_id = data["user_id"]
                self.username = data.get("username", username)
                messagebox.showinfo("Success", f"Welcome, {self.username}!")
                self.show_main_menu()
            else:
                messagebox.showerror("Error", data.get("message", "Unknown error"))

        tk.Button(self.root, text="Login", command=attempt_login).pack(pady=10)
        tk.Button(self.root, text="Back to Register", command=self.show_register_window).pack()

    def show_main_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Snake & Ladder - Main Menu", font=("Arial", 18)).pack(pady=20)
        tk.Label(self.root, text="Invite players and start the game!", font=("Arial", 12)).pack(pady=5)

        tk.Button(self.root, text="🎮 Create Game Session", font=("Arial", 14), command=self.create_game_session).pack(pady=10)
        tk.Button(self.root, text="🔗 Join via Invite Link", font=("Arial", 14), command=self.join_game_session).pack(pady=10)
        tk.Button(self.root, text="Logout", command=self.show_login_window).pack(pady=10)

    def create_game_session(self):
        try:
            r = requests.post(f"{SERVER_URL}/create_session")
            if r.status_code == 200:
                session_info = r.json()
                invite_link = session_info["invite_link"]
                session_id = session_info["session_id"]

                pyperclip.copy(invite_link)

                def copy_link():
                    pyperclip.copy(invite_link)
                    messagebox.showinfo("Copied", "Invite link copied to clipboard!")

                invite_window = tk.Toplevel(self.root)
                invite_window.title("Invite Link")
                invite_window.geometry("460x160")

                tk.Label(invite_window, text="Share this link with your friend:", font=("Arial", 12)).pack(pady=10)
                link_entry = tk.Entry(invite_window, width=60)
                link_entry.insert(0, invite_link)
                link_entry.pack(pady=5)
                tk.Button(invite_window, text="Copy to Clipboard", command=copy_link).pack(pady=10)

                self.start_game(session_id)
            else:
                messagebox.showerror("Error", "Failed to create game session.")
        except Exception as e:
            messagebox.showerror("Error", f"Server error: {e}")

    def join_game_session(self):
        link_or_id = simpledialog.askstring("Join Game", "Paste the invite link OR the session ID:")
        if not link_or_id:
            return
        # Accept either full ws://.../ws/<id> or the id itself
        if "/ws/" in link_or_id:
            session_id = link_or_id.rsplit("/ws/", 1)[-1]
        else:
            session_id = link_or_id.strip()
        self.start_game(session_id)

    def start_game(self, session_id: str):
        self.session_id = session_id
        self.root.withdraw()
        game_window = tk.Toplevel()
        game_window.protocol("WM_DELETE_WINDOW", self.on_close_game)

        ws_url = f"ws://localhost:8000/ws/{session_id}"

        def on_open(ws):
            print("Connected to session.")
            # Introduce ourselves to the server
            join_msg = {"type": "join", "user_id": self.user_id, "username": self.username}
            ws.send(json.dumps(join_msg))

        def on_message(ws, message):
            data = json.loads(message)
            # Forward to the game object (thread-safe via Tk event)
            if self.game:
                self.game.after_from_ws(lambda: self.game.handle_server_event(data))

        def on_close(ws, *args):
            print("Disconnected from session.")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_close=on_close
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

        # Pass ws and identity to the game UI
        self.game = SnakeLadderGame(game_window, websocket_connection=self.ws, user_id=self.user_id, username=self.username)

    def on_close_game(self):
        try:
            self.ws.close()
        except Exception:
            pass
        self.game = None
        self.root.deiconify()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    GameClient().run()
