from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from config import Config
from game.room_manager import RoomManager
from models import db, Room
from utils.validators import validate_player_name, validate_room_settings
from utils.helpers import sanitize_string

game_bp = Blueprint("game", __name__)

@game_bp.route("/create-room", methods=["GET", "POST"])
def create_room():
    mode = request.values.get("mode", "song").lower()
    if mode not in Config.GAME_MODES:
        mode = "song"
    mode_info = Config.GAME_MODES[mode]
    categories = mode_info["categories"]

    if request.method == "POST":
        player_name = sanitize_string(request.form.get("player_name", ""))
        category = sanitize_string(request.form.get("category", categories[0]))
        rounds = request.form.get("rounds", Config.DEFAULT_ROUNDS)
        round_duration = request.form.get("round_duration", Config.DEFAULT_ROUND_DURATION)
        max_players = request.form.get("max_players", Config.MAX_PLAYERS)

        # Validate
        valid_name, name_err = validate_player_name(player_name)
        if not valid_name:
            flash(name_err, "error")
            return render_template("create_room.html", categories=categories, mode=mode, mode_info=mode_info, form=request.form)

        valid_settings, set_err = validate_room_settings(category, rounds, round_duration, max_players, mode=mode)
        if not valid_settings:
            flash(set_err, "error")
            return render_template("create_room.html", categories=categories, mode=mode, mode_info=mode_info, form=request.form)

        # Store player name in session
        session["player_name"] = player_name
        user_id = session.get("user_id")

        # Create in-memory Room session
        room = RoomManager.create_room(
            host_sid=f"host-init-{player_name}",
            host_name=player_name,
            category=category,
            rounds=int(rounds),
            round_duration=int(round_duration),
            max_players=int(max_players),
            host_user_id=user_id
        )

        # Persist room to DB
        try:
            db_room = Room(
                room_code=room.room_code,
                host_id=user_id,
                host_name=player_name,
                category=category,
                rounds=int(rounds),
                round_duration=int(round_duration),
                max_players=int(max_players),
                status="WAITING"
            )
            db.session.add(db_room)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

        return redirect(url_for("game.room_view", room_code=room.room_code, name=player_name))

    default_name = session.get("player_name", "")
    return render_template("create_room.html", categories=categories, mode=mode, mode_info=mode_info, default_name=default_name)

@game_bp.route("/join-room", methods=["GET", "POST"])
def join_room():
    if request.method == "POST":
        room_code = sanitize_string(request.form.get("room_code", "")).upper()
        player_name = sanitize_string(request.form.get("player_name", ""))

        valid_name, name_err = validate_player_name(player_name)
        if not valid_name:
            flash(name_err, "error")
            return render_template("join_room.html", form=request.form)

        if not room_code:
            flash("Please enter a room code.", "error")
            return render_template("join_room.html", form=request.form)

        room = RoomManager.get_room(room_code)
        if not room:
            # Check if exists in DB or not active
            db_room = Room.query.filter_by(room_code=room_code).first()
            if not db_room:
                flash(f"Room '{room_code}' was not found. Please check the code.", "error")
                return render_template("join_room.html", form=request.form)
            flash(f"Room '{room_code}' is no longer active.", "error")
            return render_template("join_room.html", form=request.form)

        if room.is_full():
            flash("This room is full (maximum players reached).", "error")
            return render_template("join_room.html", form=request.form)

        if room.status not in ["WAITING", "GAME_END"]:
            flash("Game has already started in this room.", "error")
            return render_template("join_room.html", form=request.form)

        session["player_name"] = player_name
        return redirect(url_for("game.room_view", room_code=room_code, name=player_name))

    code_prefill = request.args.get("code", "").upper()
    default_name = session.get("player_name", "")
    return render_template("join_room.html", code_prefill=code_prefill, default_name=default_name)

@game_bp.route("/room/<room_code>")
def room_view(room_code):
    room_code = room_code.upper().strip()
    room = RoomManager.get_room(room_code)
    
    if not room:
        flash(f"Room '{room_code}' does not exist or has expired.", "error")
        return redirect(url_for("game.join_room", code=room_code))

    player_name = request.args.get("name") or session.get("player_name") or "Player"
    user_id = session.get("user_id")

    return render_template(
        "game.html",
        room_code=room_code,
        player_name=player_name,
        user_id=user_id,
        category=room.category,
        rounds=room.rounds,
        duration=room.round_duration,
        max_players=room.max_players,
        categories=Config.CATEGORIES
    )
