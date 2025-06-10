from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the socket_app from endpoints.py
from app.api.endpoints import socket_app as ws_app # Renamed to avoid conflict

app = FastAPI()

# Configure CORS for HTTP requests
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000", # Added for completeness
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "AI Chat App Backend"}

# Mount the Socket.IO app
# The socketio_path in ASGIApp constructor ("ws") determines the path
# So, it will be available at /ws
app.mount("/ws", ws_app)

# To run this app:
# uvicorn app.main:app --reload --port 8000
# The WebSocket will be accessible at ws://localhost:8000/ws
