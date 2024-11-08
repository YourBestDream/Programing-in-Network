from flask import Blueprint
from flask_socketio import emit, join_room, leave_room
from app.socketio_instance import socketio

chat_blueprint = Blueprint('chat', __name__)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('message', {'msg': f'{username} has joined the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('message', {'msg': f'{username} has left the room.'}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    emit('message', {'msg': data['msg']}, room=room)
