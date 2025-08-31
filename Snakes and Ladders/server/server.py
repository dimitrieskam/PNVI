# server/server.py
import json
import time
import uuid
import random
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import SessionLocal, create_db, User

app = FastAPI()
create_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory session state managed by the server (authoritative) ---
# sessions[session_id] = {
#   "clients": [WebSocket, ...],
#   "players": [ {"user_id": int, "username": str}, ...],
#   "turn_index": 0,
#   "positions": { user_id: int },
#   "dice": None,
#   "start_time": float
# }
sessions: Dict[str, Dict] = {}

SNAKES = {98: 78, 95: 56, 87: 24, 64: 60, 62: 19}
LADDERS = {4: 14, 9: 31, 28: 84, 51: 67, 71: 91, 80: 100}


def apply_snakes_ladders(pos: int) -> int:
    if pos in LADDERS:
        return LADDERS[pos]
    if pos in SNAKES:
        return SNAKES[pos]
    return pos


def broadcast(session_id: str, payload: dict):
    """Send a JSON message to all clients in the session."""
    if session_id not in sessions:
        return
    msg = json.dumps(payload)
    for ws in list(sessions[session_id]["clients"]):
        try:
            # WebSocket.send_text is awaitable; here we fire-and-forget via loop.create_task
            # but FastAPI requires awaits. We'll schedule sequentially.
            import asyncio
            asyncio.create_task(ws.send_text(msg))
        except Exception:
            pass


@app.post("/register")
async def register(username: str, password: str):
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            return {"status": "error", "message": "Username taken."}
        user = User(username=username, password=password)
        db.add(user)
        db.commit()
        return {"status": "success"}
    finally:
        db.close()


@app.post("/login")
async def login(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username, User.password == password).first()
        if user:
            return {"status": "success", "user_id": user.id, "username": user.username,
                    "wins": user.wins, "losses": user.losses, "fastest_win_seconds": user.fastest_win_seconds}
        return {"status": "error", "message": "Invalid credentials."}
    finally:
        db.close()


@app.post("/create_session")
async def create_session():
    session_id = str(uuid.uuid4())
    # Initialize empty session
    sessions[session_id] = {
        "clients": [],
        "players": [],
        "turn_index": 0,
        "positions": {},
        "dice": None,
        "start_time": None,
    }
    return {"session_id": session_id, "invite_link": f"ws://localhost:8000/ws/{session_id}"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # Ensure session exists
    if session_id not in sessions:
        sessions[session_id] = {
            "clients": [],
            "players": [],
            "turn_index": 0,
            "positions": {},
            "dice": None,
            "start_time": None,
        }
    sessions[session_id]["clients"].append(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            msg_type = data.get("type")

            # 1) JOIN: a client identifies themselves (user_id, username)
            if msg_type == "join":
                user_id = int(data["user_id"])
                username = data.get("username", f"Player{user_id}")

                # Register player if new
                player_ids = [p["user_id"] for p in sessions[session_id]["players"]]
                if user_id not in player_ids:
                    sessions[session_id]["players"].append({"user_id": user_id, "username": username})
                    sessions[session_id]["positions"][user_id] = 0

                # Start time when the first player joins
                if sessions[session_id]["start_time"] is None:
                    sessions[session_id]["start_time"] = time.time()

                # Send full state to everyone
                broadcast(session_id, {
                    "type": "state",
                    "players": sessions[session_id]["players"],
                    "positions": sessions[session_id]["positions"],
                    "turn_user_id": sessions[session_id]["players"][sessions[session_id]["turn_index"]]["user_id"],
                    "dice": sessions[session_id]["dice"],
                })

            # 2) ROLL: only the player whose turn it is may request a roll
            elif msg_type == "roll":
                if not sessions[session_id]["players"]:
                    continue
                current_turn_user_id = sessions[session_id]["players"][sessions[session_id]["turn_index"]]["user_id"]
                requester = int(data["user_id"])
                if requester != current_turn_user_id:
                    # Ignore invalid roll
                    await websocket.send_text(json.dumps({"type": "error", "message": "Not your turn"}))
                    continue

                dice = random.randint(1, 6)
                sessions[session_id]["dice"] = dice

                # Move player
                cur_pos = sessions[session_id]["positions"][requester]
                next_pos = cur_pos + dice
                if next_pos > 100:
                    next_pos = cur_pos  # overshoot: don't move
                else:
                    next_pos = apply_snakes_ladders(next_pos)

                sessions[session_id]["positions"][requester] = next_pos

                # Broadcast dice result and move
                broadcast(session_id, {
                    "type": "dice",
                    "user_id": requester,
                    "dice": dice,
                    "positions": sessions[session_id]["positions"],
                })

                # Win check
                if next_pos == 100:
                    elapsed = int(time.time() - sessions[session_id]["start_time"]) if sessions[session_id]["start_time"] else 0
                    # Update DB: winner gets win, others get loss; fastest
                    db = SessionLocal()
                    try:
                        # Winner
                        winner = db.query(User).get(requester)
                        if winner:
                            winner.wins += 1
                            if winner.fastest_win_seconds is None or elapsed < (winner.fastest_win_seconds or 1_000_000):
                                winner.fastest_win_seconds = elapsed
                        # Losers
                        for p in sessions[session_id]["players"]:
                            if p["user_id"] != requester:
                                loser = db.query(User).get(p["user_id"])
                                if loser:
                                    loser.losses += 1
                        db.commit()
                    finally:
                        db.close()

                    broadcast(session_id, {
                        "type": "end",
                        "winner_user_id": requester,
                        "elapsed_seconds": elapsed,
                        "positions": sessions[session_id]["positions"],
                    })
                    # Optionally reset or leave session as-is
                    continue

                # Advance turn
                sessions[session_id]["turn_index"] = (sessions[session_id]["turn_index"] + 1) % max(1, len(sessions[session_id]["players"]))
                broadcast(session_id, {
                    "type": "turn",
                    "turn_user_id": sessions[session_id]["players"][sessions[session_id]["turn_index"]]["user_id"],
                })

            # 3) (Optional) explicit sync request
            elif msg_type == "sync":
                broadcast(session_id, {
                    "type": "state",
                    "players": sessions[session_id]["players"],
                    "positions": sessions[session_id]["positions"],
                    "turn_user_id": sessions[session_id]["players"][sessions[session_id]["turn_index"]]["user_id"] if sessions[session_id]["players"] else None,
                    "dice": sessions[session_id]["dice"],
                })

    except WebSocketDisconnect:
        # remove this websocket
        if session_id in sessions and websocket in sessions[session_id]["clients"]:
            sessions[session_id]["clients"].remove(websocket)
        # (Optional) if everyone left, you can cleanup session
        # if not sessions[session_id]["clients"]:
        #     del sessions[session_id]

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
