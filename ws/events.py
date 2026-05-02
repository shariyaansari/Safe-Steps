import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from core.config import settings
from core.database import get_db
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ─────────────────────────────────────────────
# Redis connection
#
# Redis is an in-memory data store we use here
# as a "message broker" — a middleman that
# passes messages between different parts of
# the app.
#
# Think of it like a radio tower:
#   - someone PUBLISHES a message (broadcasts)
#   - everyone SUBSCRIBED receives it instantly
#
# aioredis is the async version of the Redis
# client, so it doesn't block FastAPI while
# waiting for messages.
# ─────────────────────────────────────────────

redis_client = aioredis.from_url(
    settings.redis_url,
    decode_responses=True   # return strings instead of raw bytes
)

# the name of the Redis channel we publish/subscribe on
# think of it like a WhatsApp group name — everyone in
# the group gets messages sent to it
INCIDENT_CHANNEL = "safesteps:incidents"


# ─────────────────────────────────────────────
# Connection Manager
#
# This class keeps track of every browser tab
# that currently has the map open (i.e. has an
# active WebSocket connection).
#
# When a user opens the map → we add them.
# When they close the tab  → we remove them.
# When a new incident comes → we loop through
# everyone and send them the update.
#
# It's essentially a list of "people currently
# watching the live map".
# ─────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        # list of all currently connected WebSocket clients
        # each entry is one open browser tab on the map page
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # accept() completes the WebSocket handshake with the browser
        # without this the connection stays pending and nothing works
        await websocket.accept()
        self.active.append(websocket)
        logger.debug(f"[WS] New client connected. Total open connections: {len(self.active)}")

    def disconnect(self, websocket: WebSocket):
        # remove this connection from our list when the browser tab closes
        self.active.remove(websocket)
        logger.debug(f"[WS] Client disconnected. Total open connections: {len(self.active)}")

    async def broadcast(self, message: dict):
        """
        Send a message to every connected browser tab simultaneously.

        We loop through all active connections and send the JSON payload.
        If a connection is broken (browser crashed, network dropped), sending
        will raise an exception — we catch it and add that connection to a
        'dead' list, then clean them up after the loop so we don't modify
        the list while iterating over it (that would cause bugs).
        """
        data = json.dumps(message)
        dead = []

        for ws in self.active:
            try:
                await ws.send_text(data)
            except Exception:
                # this connection is broken — mark for removal
                dead.append(ws)

        # clean up broken connections after the loop finishes
        for ws in dead:
            self.active.remove(ws)


# single shared instance — the whole app uses this one manager
# so all routes and the subscriber talk to the same connection list
manager = ConnectionManager()


# ─────────────────────────────────────────────
# WebSocket Authentication
#
# Normal HTTP requests carry cookies automatically,
# but WebSocket upgrade requests don't attach
# cookies in all browsers reliably.
#
# So instead of reading the cookie, we ask the
# client to pass the JWT token as a URL query
# parameter when connecting:
#
#   ws://localhost:8000/ws/incidents?token=eyJ...
#
# This function decodes that token, looks up the
# user in the database, and returns them if valid.
# Returns None if the token is invalid or expired.
# ─────────────────────────────────────────────

async def get_ws_user(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
) -> User | None:

    try:
        # decode the JWT — this will raise JWTError if
        # the token is expired, tampered with, or invalid
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None

    # look up the user in the database to make sure they still exist
    # and haven't been banned since the token was issued
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    # return None if user doesn't exist or has been deactivated
    return user if user and user.is_active else None


# ─────────────────────────────────────────────
# WebSocket Endpoint
#
# This is the route the browser connects to when
# the map page loads. It's a persistent two-way
# connection (unlike HTTP which is one request
# then done).
#
# Flow:
#   1. Browser connects with their JWT token
#   2. We verify the token — reject if invalid
#   3. We accept the connection and add to manager
#   4. We send a welcome message so client knows it's live
#   5. We sit in a loop waiting for "ping" messages
#      from the client (keepalive heartbeat)
#   6. When the tab closes, WebSocketDisconnect
#      is raised and we remove them from manager
#
# Note: actual incident data doesn't come through
# this loop — it comes from the Redis subscriber
# below which calls manager.broadcast() directly.
# ─────────────────────────────────────────────

@router.websocket("/ws/incidents")
async def incidents_ws(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # authenticate BEFORE accepting the connection
    # if we accept first and then reject, the browser
    # sees a connected-then-closed socket which is confusing
    user = await get_ws_user(token=token, db=db)
    if not user:
        # code 4001 is a custom close code meaning "unauthorized"
        # (4000-4999 are reserved for application-defined codes)
        await websocket.close(code=4001)
        logger.warning("[WS] Rejected connection — invalid or missing token")
        return

    # auth passed — add this connection to the manager
    await manager.connect(websocket)

    # tell the client the connection is live
    # the frontend JS listens for this to show a "live" indicator
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": f"Live feed active. Welcome {user.username}"
    }))

    try:
        # keep the connection alive indefinitely
        # we listen for "ping" messages from the client
        # and respond with "pong" — this is a heartbeat
        # pattern to prevent the connection timing out
        # on idle (many proxies and load balancers close
        # connections that are silent for too long)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        # browser tab was closed or network dropped
        # remove this connection so we stop trying to send to it
        manager.disconnect(websocket)


# ─────────────────────────────────────────────
# Redis Subscriber (Background Task)
#
# This is a long-running background coroutine
# that starts when the app boots and runs forever.
#
# It subscribes to our Redis channel and waits.
# Whenever something is published to that channel
# (e.g. admin verifies an incident), this function
# wakes up, reads the message, and calls
# manager.broadcast() to push it to all open maps.
#
# Think of it as:
#   Redis channel → this subscriber → all browsers
#
# It's started as an asyncio background task in
# app.py's lifespan function:
#   asyncio.create_task(redis_subscriber())
# ─────────────────────────────────────────────

async def redis_subscriber():
    logger.info("[WS] Redis subscriber started — listening for new incidents")

    # create a pub/sub object and subscribe to our channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(INCIDENT_CHANNEL)

    # listen() is an async generator that yields messages
    # as they arrive — it blocks until a message comes in,
    # then yields it, then blocks again. Very efficient.
    async for message in pubsub.listen():

        # Redis sends a "subscribe" confirmation message when you
        # first subscribe — we ignore that, only care about actual data
        if message["type"] != "message":
            continue

        try:
            # the message data is a JSON string — parse it back to a dict
            data = json.loads(message["data"])

            # push to every connected browser tab
            await manager.broadcast(data)
            logger.debug(f"[WS] Broadcast incident {data.get('id')} to {len(manager.active)} clients")

        except Exception as e:
            # log the error but don't crash — the subscriber must
            # keep running even if one message fails to process
            logger.error(f"[WS] Failed to broadcast message: {e}")


# ─────────────────────────────────────────────
# Publisher Helper
#
# This function is called from admin.py when
# an admin verifies an incident.
#
# It takes the incident object, packages the
# relevant fields as a JSON-serialisable dict,
# and publishes it to the Redis channel.
#
# From there, redis_subscriber() picks it up
# and broadcasts it to all open browser tabs.
#
# Usage in admin.py verify route:
#   from ws.events import publish_incident
#   await publish_incident(incident)
#
# The separation is intentional:
#   - admin.py handles DB logic
#   - this file handles real-time delivery
#   - Redis decouples the two so neither
#     needs to know about the other directly
# ─────────────────────────────────────────────

async def publish_incident(incident) -> None:
    payload = {
        "type":          "new_incident",   # client checks this to know what kind of event it is
        "id":            str(incident.id),
        "incident_type": incident.incident_type.value,
        "description":   incident.description,
        "area":          incident.area,
        "latitude":      incident.latitude,
        "longitude":     incident.longitude,
        "occurred_at":   incident.occurred_at.isoformat(),
        "upvotes":       incident.upvotes,
        "image_url":     incident.image_url,
    }

    # PUBLISH sends the message to the Redis channel
    # everyone subscribed to INCIDENT_CHANNEL receives it instantly
    await redis_client.publish(INCIDENT_CHANNEL, json.dumps(payload))
    logger.debug(f"[WS] Published incident {incident.id} to Redis channel")