import logging
from flask import request
from flask_socketio import emit, join_room, leave_room
from game.room_manager import RoomManager
from game.game_manager import GameManager
from utils.validators import validate_room_settings

logger = logging.getLogger(__name__)

def register_socket_handlers(socketio):
    """Register all Socket.IO real-time event handlers."""

    @socketio.on("connect")
    def handle_connect():
        logger.debug(f"Client connected: {request.sid}")
        emit("connected", {"sid": request.sid})

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = request.sid
        logger.debug(f"Client disconnected: {sid}")
        room, player = RoomManager.leave_room(sid)
        if room and player:
            leave_room(room.room_code)
            # Announce player departure
            socketio.emit("player_left", {
                "player_name": player.name,
                "sid": sid,
                "host_sid": room.host_sid,
                "players": [p.to_dict() for p in room.players.values()]
            }, room=room.room_code)

            # Check if active drawer disconnected mid-game
            if room.game_manager and room.status == "DRAWING":
                if room.game_manager.current_drawer_sid == sid:
                    room.game_manager.handle_drawer_disconnect()

    @socketio.on("join_room_socket")
    def handle_join_room(data):
        room_code = data.get("room_code", "").upper().strip()
        player_name = data.get("player_name", "").strip()
        user_id = data.get("user_id")

        if not room_code or not player_name:
            emit("error_message", {"message": "Invalid room code or player name."})
            return

        room = RoomManager.get_room(room_code)
        if not room:
            emit("error_message", {"message": "Room not found."})
            return

        # Check if player already in room or add them
        player = room.get_player(request.sid)
        if not player:
            room, player, err = RoomManager.join_room(room_code, request.sid, player_name, user_id=user_id)
            if err:
                emit("error_message", {"message": err})
                return

        join_room(room_code)

        # Notify joining client of current room state
        room_joined_data = {
            "room_code": room.room_code,
            "category": room.category,
            "rounds": room.rounds,
            "round_duration": room.round_duration,
            "max_players": room.max_players,
            "is_host": player.is_host,
            "status": room.status,
            "players": [p.to_dict(is_drawer=(room.game_manager and p.sid == room.game_manager.current_drawer_sid)) for p in room.players.values()],
            "strokes": room.current_strokes if room.status == "DRAWING" else []
        }

        # If rejoining an in-progress round, attach active round metadata
        if room.status == "DRAWING" and room.game_manager:
            drawer_player = room.get_player(room.game_manager.current_drawer_sid)
            room_joined_data["round_info"] = {
                "round": room.game_manager.current_round,
                "total_rounds": room.game_manager.total_rounds,
                "category": room.category,
                "duration": room.round_duration,
                "time_remaining": room.game_manager.time_remaining,
                "drawer_sid": room.game_manager.current_drawer_sid,
                "drawer_name": drawer_player.name if drawer_player else "Drawer",
                "masked_title": room.game_manager.get_masked_title(room.game_manager.current_song["title"]) if room.game_manager.current_song else ""
            }

        emit("room_joined", room_joined_data)

        # If this joining player is the active drawer, send them their secret song
        if room.status == "DRAWING" and room.game_manager and room.game_manager.current_drawer_sid == player.sid:
            emit("your_secret_song", {
                "title": room.game_manager.current_song["title"],
                "artist": room.game_manager.current_song.get("artist"),
                "movie": room.game_manager.current_song.get("movie"),
                "difficulty": room.game_manager.current_song.get("difficulty", "MEDIUM"),
                "keywords": room.game_manager.current_song.get("keywords")
            })

        # Broadcast update to everyone in the room
        socketio.emit("player_joined", {
            "player_name": player.name,
            "sid": player.sid,
            "is_host": player.is_host,
            "players": [p.to_dict(is_drawer=(room.game_manager and p.sid == room.game_manager.current_drawer_sid)) for p in room.players.values()]
        }, room=room_code)

    @socketio.on("update_settings")
    def handle_update_settings(data):
        room = RoomManager.get_room_by_sid(request.sid)
        if not room:
            return

        player = room.get_player(request.sid)
        if not player or not player.is_host:
            emit("error_message", {"message": "Only the host can adjust room settings."})
            return

        category = data.get("category", room.category)
        rounds = data.get("rounds", room.rounds)
        duration = data.get("round_duration", room.round_duration)

        valid, msg = validate_room_settings(category, rounds, duration, room.max_players)
        if not valid:
            emit("error_message", {"message": msg})
            return

        RoomManager.update_settings(room.room_code, category, rounds, duration)
        socketio.emit("settings_updated", {
            "category": room.category,
            "rounds": room.rounds,
            "round_duration": room.round_duration
        }, room=room.room_code)

    @socketio.on("start_game")
    def handle_start_game(data=None):
        room = RoomManager.get_room_by_sid(request.sid)
        if not room:
            emit("error_message", {"message": "Room not found."})
            return

        player = room.get_player(request.sid)
        if not player or not player.is_host:
            emit("error_message", {"message": "Only the room host can start the game."})
            return

        if room.get_player_count() < 2:
            emit("error_message", {"message": "At least 2 players are required to start the game."})
            return

        from flask import current_app
        app = current_app._get_current_object()
        game_mgr = GameManager(room, socketio, app=app)
        success = game_mgr.start_game()
        if not success:
            emit("error_message", {"message": "Could not start game."})

    @socketio.on("drawing_stroke")
    def handle_drawing_stroke(data):
        room = RoomManager.get_room_by_sid(request.sid)
        if not room or room.status != "DRAWING" or not room.game_manager:
            return

        # Security: Authoritative drawer check
        if room.game_manager.current_drawer_sid != request.sid:
            return

        # Buffer stroke for syncing
        room.current_strokes.append(data)
        if len(room.current_strokes) > 5000:
            room.current_strokes = room.current_strokes[-5000:]

        # Broadcast stroke to all other players in the room
        emit("drawing_stroke", data, room=room.room_code, include_self=False)

    @socketio.on("drawing_clear")
    def handle_drawing_clear(data=None):
        room = RoomManager.get_room_by_sid(request.sid)
        if not room or room.status != "DRAWING" or not room.game_manager:
            return

        if room.game_manager.current_drawer_sid != request.sid:
            return

        room.current_strokes.clear()
        emit("drawing_clear", {}, room=room.room_code, include_self=False)

    @socketio.on("drawing_undo")
    def handle_drawing_undo(data=None):
        room = RoomManager.get_room_by_sid(request.sid)
        if not room or room.status != "DRAWING" or not room.game_manager:
            return

        if room.game_manager.current_drawer_sid != request.sid:
            return

        emit("drawing_undo", {}, room=room.room_code, include_self=False)

    @socketio.on("submit_guess")
    def handle_submit_guess(data=None):
        if not data:
            return
        guess = data.get("guess", "").strip()
        if not guess:
            return

        room = RoomManager.get_room_by_sid(request.sid)
        if not room or not room.game_manager:
            return

        room.game_manager.process_guess(request.sid, guess)

    @socketio.on("play_again")
    def handle_play_again(data=None):
        room = RoomManager.get_room_by_sid(request.sid)
        if not room or not room.game_manager:
            return

        player = room.get_player(request.sid)
        if not player or not player.is_host:
            emit("error_message", {"message": "Only the host can restart the game."})
            return

        room.game_manager.reset_for_play_again()
