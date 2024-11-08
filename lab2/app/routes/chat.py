import asyncio
from flask import Blueprint, render_template
import websockets
import json

chat_blueprint = Blueprint('chat', __name__)

# In-memory storage for connected clients and message history
clients = {}  # Dictionary to store {websocket: nickname}
message_history = []  # List of dictionaries with keys: 'nickname' and 'message'

async def broadcast_message(message):
    # Send message to all connected clients, creating tasks for each send operation
    if clients:
        await asyncio.wait([asyncio.create_task(client.send(message)) for client in clients])

async def websocket_handler(websocket, path):
    # Request nickname from the user
    await websocket.send(json.dumps({"action": "request_nickname"}))
    
    # Await for the nickname message with action 'nickname'
    nickname_message = await websocket.recv()
    nickname_data = json.loads(nickname_message)
    
    # Check if the received message is a nickname submission
    if nickname_data.get("action") == "nickname":
        nickname = nickname_data.get("nickname", "Anonymous")
    else:
        nickname = "Anonymous"
    
    # Register the client with nickname
    clients[websocket] = nickname

    # Send chat history to the new user
    for msg in message_history:
        await websocket.send(json.dumps({"nickname": msg["nickname"], "message": msg["message"]}))

    # Notify others of the new user joining
    join_message = f"{nickname} has joined the chat."
    await broadcast_message(json.dumps({"nickname": "System", "message": join_message}))
    message_history.append({"nickname": "System", "message": join_message})

    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get('action')

            if action == 'message':
                # Append message to history and broadcast
                user_message = data['message']
                message_history.append({"nickname": nickname, "message": user_message})
                await broadcast_message(json.dumps({"nickname": nickname, "message": user_message}))
            elif action == 'leave':
                leave_message = f"{nickname} has left the chat."
                await broadcast_message(json.dumps({"nickname": "System", "message": leave_message}))
                message_history.append({"nickname": "System", "message": leave_message})
                break
            elif action == 'ping':
                # Respond to ping with pong to keep connection alive
                await websocket.send(json.dumps({"action": "pong"}))
    except websockets.exceptions.ConnectionClosedError:
        print(f"{nickname} disconnected unexpectedly.")
    finally:
        # Notify others that the user has disconnected
        if websocket in clients:
            disconnect_message = f"{nickname} has disconnected."
            await broadcast_message(json.dumps({"nickname": "System", "message": disconnect_message}))
            message_history.append({"nickname": "System", "message": disconnect_message})
            del clients[websocket]
        await websocket.close()


@chat_blueprint.route('/chat', methods=["GET"])
def chat_room():
    return render_template('chat_interface.html')
