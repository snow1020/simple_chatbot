# Contents for backend/app/api/endpoints.py
import socketio
import datetime
import logging # Import logging
from app.services.connection_manager import manager
from app.services.ai_assistant import ai_assistant_service

# Configure basic logging (can be expanded in main.py or core.logging later)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, socketio_path="ws")

@sio.event
async def connect(sid, environ):
    try:
        await manager.connect(sid)
        logger.info(f"Client connected: {sid}, Environment: {environ}")
        await sio.emit('server_registered_sid', {'sid': sid}, room=sid)
        logger.info(f"Emitted 'server_registered_sid' with SID {sid} to client {sid}")
        await sio.emit("message", {"type": "status", "data": f"Welcome {sid}!"}, room=sid)

        ai_welcome = {
            "sender_sid": ai_assistant_service.ai_sid,
            "text": "Hello! I am your friendly AI assistant. Ask me anything!",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "is_ai": True
        }
        await sio.emit("new_message", ai_welcome, room=sid)
    except Exception as e:
        logger.error(f"Error during connect for SID {sid}: {e}", exc_info=True)
        # Optionally, try to emit an error to the client if possible,
        # though connection might already be problematic.
        try:
            await sio.emit("error", {"message": "Connection error occurred."}, room=sid)
        except Exception as emit_exception:
            logger.error(f"Failed to emit connection error to SID {sid}: {emit_exception}", exc_info=True)


@sio.event
async def disconnect(sid):
    try:
        await manager.disconnect(sid)
        logger.info(f"Client disconnected: {sid}")
        await sio.emit("message", {"type": "status", "data": f"User {sid} has left."}, skip_sid=sid)
    except Exception as e:
        logger.error(f"Error during disconnect for SID {sid}: {e}", exc_info=True)


@sio.event
async def chat_message(sid, data):
    try:
        logger.info(f"Message from {sid}: {data}")

        if not isinstance(data, dict) or "text" not in data:
            logger.warning(f"Invalid message format from {sid}. Data: {data}")
            await sio.emit("error", {"type": "validation_error", "message": "Invalid message format. Expected {'text': 'your message'}"}, room=sid)
            return

        user_message_text = data.get("text")
        user_message_payload = {
            "sender_sid": sid,
            "text": user_message_text,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "is_ai": False
        }

        logger.info(f"Broadcasting user message from {sid}: {user_message_payload}")
        await sio.emit("new_message", user_message_payload)

        logger.info(f"Generating AI response for {sid} based on: {user_message_text}")
        ai_response = await ai_assistant_service.generate_dummy_response(user_message_text, sid)

        logger.info(f"Sending AI response to all clients: {ai_response}")
        await sio.emit("new_message", ai_response)
    except socketio.exceptions.SocketIOError as e: # More specific Socket.IO errors
        logger.error(f"Socket.IO error processing chat_message for SID {sid}: {e}", exc_info=True)
        try:
            await sio.emit("error", {"type": "server_error", "message": "A server error occurred while processing your message."}, room=sid)
        except Exception as emit_exception:
            logger.error(f"Failed to emit server_error to SID {sid}: {emit_exception}", exc_info=True)
    except Exception as e: # Generic catch-all
        logger.error(f"Unexpected error processing chat_message for SID {sid}: {e}", exc_info=True)
        try:
            await sio.emit("error", {"type": "unexpected_error", "message": "An unexpected server error occurred."}, room=sid)
        except Exception as emit_exception:
            logger.error(f"Failed to emit unexpected_error to SID {sid}: {emit_exception}", exc_info=True)

# Adding a generic error handler for unhandled Socket.IO events or errors
@sio.on("*")
async def any_event(event, sid, data):
    logger.debug(f"Unhandled event '{event}' from SID {sid}' with data: {data}")
    # This is a catch-all for events not explicitly handled.
    # You might not want to do anything here, or just log.

# This handles errors that occur within the Socket.IO server itself,
# not necessarily tied to a specific event handler you've defined.
@sio.event
async def error(sid, data):
    # This 'error' event is a bit special. It's often triggered by the server
    # when it wants to inform a client of an issue, or if an unhandled
    # exception occurs in an event handler that python-socketio catches.
    logger.error(f"Server-side error event triggered for SID {sid}: {data}")
    # No need to emit back 'error' from here usually, as this IS the error event.
