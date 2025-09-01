from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid
import uvicorn
from database import SessionLocal, create_db, User

app = FastAPI()

clients = {}  # session_id -> list of WebSocket connections

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

create_db()

@app.post("/register")
async def register(username: str, password: str):
    db = SessionLocal()
    if db.query(User).filter(User.username == username).first():
        db.close()
        return {"status": "error", "message": "Username taken."}
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    db.close()
    return {"status": "success"}

@app.post("/login")
async def login(username: str, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username, User.password == password).first()
    db.close()
    if user:
        return {"status": "success", "user_id": user.id}
    return {"status": "error", "message": "Invalid credentials."}

@app.post("/create_session")
async def create_session():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id, "invite_link": f"ws://localhost:8000/ws/{session_id}"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in clients:
        clients[session_id] = []
    clients[session_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for client in clients[session_id]:
                if client != websocket:
                    await client.send_text(data)
    except WebSocketDisconnect:
        clients[session_id].remove(websocket)

@app.post("/update_stats")
async def update_stats(username: str, result: str, duration: int = None):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        return {"status": "error", "message": "User not found"}

    if result == "win":
        user.wins += 1
        if duration and duration < user.fastest_win_seconds:
            user.fastest_win_seconds = duration
    elif result == "loss":
        user.losses += 1

    db.commit()
    db.close()
    return {"status": "success"}

@app.post("/update_profile")
async def update_profile(username: str, avatar: str = "🙂", new_name: str = None):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user:
        db.close()
        return {"status": "error", "message": "User not found"}

    if new_name:
        if db.query(User).filter(User.username==new_name).first():
            db.close()
            return {"status": "error", "message": "Username already taken"}
        user.username  = new_name

    if avatar:
        user.avatar = avatar

    db.commit()
    db.close()
    return {"status": "success"}

@app.get("/stats")
async def get_stats(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if not user:
        return {"status": "error", "message": "User not found"}
    return {
        "username": user.username,
        "avatar": user.avatar,
        "wins": user.wins,
        "losses": user.losses,
        "fastest_win_seconds": user.fastest_win_seconds
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

