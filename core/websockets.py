# To establish and manage WebSocket connections for real-time incident updates. The ConnectionManager class keeps track of active WebSocket connections and provides methods to connect, disconnect, and broadcast messages to all connected clients. The websocket_endpoint function handles incoming WebSocket connections at the /ws/incidents endpoint, allowing clients to receive real-time updates about incidents as they occur.
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging

# Same as normal routes, but for WebSockets. We create a ConnectionManager class to manage active WebSocket connections and provide methods to connect, disconnect, and broadcast messages to all connected clients. The websocket_endpoint function handles incoming WebSocket connections at the /ws/incidents endpoint, allowing clients to receive real-time updates about incidents as they occur.
router = APIRouter()
logger = logging.getLogger(__name__)

# Track and send updates about the user 
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []   #List of currently connected clients

    # Client connects to WebSocket, we accept the connection and add it to the list of active connections
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    # Remove from list of active connections when client disconnects to prevent memory leaks and ensure we don't try to send messages to disconnected clients
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    # It sends message to all connected users when an incident is updated, so they can see the changes in real-time without needing to refresh the page. It also includes error handling to log any issues that occur while sending messages to clients.
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)     # New crime reported, send to all connected clients
            # Some users may disconnect unexpectedly, so we catch exceptions to prevent the server from crashing and log the error for debugging purposes.
            except Exception as e:
                logger.error(f"Error sending message to websocket: {e}")

# This endpoint allows clients to establish a WebSocket connection to receive real-time updates about incidents. When a client connects, we add them to the ConnectionManager. We keep the connection open to allow for continuous updates, and if the client disconnects, we remove them from the ConnectionManager to clean up resources.
manager = ConnectionManager()

# WebSocket endpoint for incident updates
@router.websocket("/ws/incidents")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keeps connection alive 
        while True:
            # Keep connection open, client might send heartbeats
            # Why use receive_text? Allows future extension , and keeps connection alive. If client disconnects, it will raise WebSocketDisconnect exception, which we catch to remove the client from the ConnectionManager and clean up resources.
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
