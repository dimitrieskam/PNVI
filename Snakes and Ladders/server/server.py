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
    allow_headers=["*"])

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

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
