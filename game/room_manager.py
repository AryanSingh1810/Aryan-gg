import time
import logging
from typing import Dict, Optional, List, Any
from utils.helpers import generate_room_code

logger = logging.getLogger(__name__)

class Player:
    def __init__(self, sid: str, name: str, user_id: Optional[int] = None, is_host: bool = False):
        self.sid = sid
        self.name = name
        self.user_id = user_id
        self.is_host = is_host
        self.score = 0
        self.round_score = 0
        self.guessed_correctly = False
        self.guess_time = 0.0
        self.is_connected = True
        self.joined_at = time.time()

    def to_dict(self, is_drawer: bool = False):
        return {
            "sid": self.sid,
            "name": self.name,
            "user_id": self.user_id,
            "is_host": self.is_host,
            "score": self.score,
            "round_score": self.round_score,
            "guessed_correctly": self.guessed_correctly,
            "is_drawer": is_drawer,
            "is_connected": self.is_connected
        }

class RoomSession:
    def __init__(
        self,
        room_code: str,
        host_sid: str,
        host_name: str,
        category: str = "English",
        rounds: int = 5,
        round_duration: int = 60,
        max_players: int = 8,
        host_user_id: Optional[int] = None
    ):
        self.room_code = room_code
        self.host_sid = host_sid
        self.category = category
        self.rounds = rounds
        self.round_duration = round_duration
        self.max_players = max_players
        self.status = "WAITING" # WAITING, STARTING, DRAWING, ROUND_END, GAME_END
        self.created_at = time.time()

        # Players dictionary: sid -> Player
        self.players: Dict[str, Player] = {}
        # Add host as first player
        self.add_player(host_sid, host_name, user_id=host_user_id, is_host=True)

        # Drawing strokes buffer to sync new/reconnecting players
        self.current_strokes: List[Dict[str, Any]] = []

        # Reference to active GameManager instance
        self.game_manager = None

    def claim_or_reconnect_player(self, sid: str, name: str, user_id: Optional[int] = None) -> Optional[Player]:
        """Claim placeholder host slot or reconnect an existing player with matching name."""
        clean_name = name.strip().lower()
        for old_sid, p in list(self.players.items()):
            is_matching_host = (p.is_host and old_sid.startswith("host-init-") and p.name.lower() == clean_name)
            is_same_player = (p.name.lower() == clean_name)
            if is_matching_host or is_same_player:
                self.players.pop(old_sid, None)
                p.sid = sid
                p.name = name
                p.user_id = user_id or p.user_id
                p.is_connected = True
                self.players[sid] = p
                if p.is_host:
                    self.host_sid = sid
                if self.game_manager and self.game_manager.current_drawer_sid == old_sid:
                    self.game_manager.current_drawer_sid = sid
                if self.game_manager:
                    self.game_manager.drawer_rotation = [
                        sid if s == old_sid else s for s in self.game_manager.drawer_rotation
                    ]
                return p
        return None

    def add_player(self, sid: str, name: str, user_id: Optional[int] = None, is_host: bool = False) -> Player:
        # Avoid duplicate names by appending suffix if needed
        existing_names = {p.name.lower() for p in self.players.values()}
        final_name = name
        counter = 2
        while final_name.lower() in existing_names:
            final_name = f"{name} ({counter})"
            counter += 1

        player = Player(sid=sid, name=final_name, user_id=user_id, is_host=is_host)
        self.players[sid] = player
        return player

    def remove_player(self, sid: str) -> Optional[Player]:
        player = self.players.pop(sid, None)
        if player and player.is_host and self.players:
            # Reassign host to earliest connected player
            next_host = next(iter(self.players.values()))
            next_host.is_host = True
            self.host_sid = next_host.sid
            logger.info(f"Host transferred to {next_host.name} ({next_host.sid}) in room {self.room_code}")
        return player

    def get_player(self, sid: str) -> Optional[Player]:
        return self.players.get(sid)

    def get_player_by_name(self, name: str) -> Optional[Player]:
        for p in self.players.values():
            if p.name.lower() == name.lower():
                return p
        return None

    def get_player_count(self) -> int:
        return len(self.players)

    def is_full(self) -> bool:
        return len(self.players) >= self.max_players

    def to_dict(self):
        drawer_sid = self.game_manager.current_drawer_sid if self.game_manager else None
        return {
            "room_code": self.room_code,
            "host_sid": self.host_sid,
            "category": self.category,
            "rounds": self.rounds,
            "round_duration": self.round_duration,
            "max_players": self.max_players,
            "player_count": len(self.players),
            "status": self.status,
            "players": [p.to_dict(is_drawer=(p.sid == drawer_sid)) for p in self.players.values()]
        }

class RoomManager:
    """Manages all active in-memory room sessions."""
    _rooms: Dict[str, RoomSession] = {}
    _sid_to_room: Dict[str, str] = {}

    @classmethod
    def create_room(
        cls,
        host_sid: str,
        host_name: str,
        category: str = "English",
        rounds: int = 5,
        round_duration: int = 60,
        max_players: int = 8,
        host_user_id: Optional[int] = None
    ) -> RoomSession:
        room_code = generate_room_code(length=5, existing_codes=set(cls._rooms.keys()))
        session = RoomSession(
            room_code=room_code,
            host_sid=host_sid,
            host_name=host_name,
            category=category,
            rounds=rounds,
            round_duration=round_duration,
            max_players=max_players,
            host_user_id=host_user_id
        )
        cls._rooms[room_code] = session
        cls._sid_to_room[host_sid] = room_code
        logger.info(f"Room {room_code} created by {host_name}")
        return session

    @classmethod
    def get_room(cls, room_code: str) -> Optional[RoomSession]:
        if not room_code:
            return None
        return cls._rooms.get(room_code.upper().strip())

    @classmethod
    def get_room_by_sid(cls, sid: str) -> Optional[RoomSession]:
        room_code = cls._sid_to_room.get(sid)
        if room_code:
            return cls._rooms.get(room_code)
        return None

    @classmethod
    def join_room(cls, room_code: str, sid: str, name: str, user_id: Optional[int] = None) -> tuple[Optional[RoomSession], Optional[Player], Optional[str]]:
        room = cls.get_room(room_code)
        if not room:
            return None, None, "Room does not exist."

        # Clean any old room mapping for this sid
        cls.leave_room(sid)

        # Check if player is claiming host placeholder or reconnecting with same name
        reconnected_player = room.claim_or_reconnect_player(sid, name, user_id)
        if reconnected_player:
            # Clean old placeholder key from _sid_to_room
            for old_s, r_code in list(cls._sid_to_room.items()):
                if old_s.startswith("host-init-") and r_code == room.room_code:
                    cls._sid_to_room.pop(old_s, None)
            cls._sid_to_room[sid] = room.room_code
            return room, reconnected_player, None

        if room.is_full():
            return None, None, "Room is full (maximum players reached)."

        if room.status not in ["WAITING", "GAME_END"]:
            return None, None, "Game has already started in this room."

        player = room.add_player(sid=sid, name=name, user_id=user_id)
        cls._sid_to_room[sid] = room.room_code
        return room, player, None

    @classmethod
    def leave_room(cls, sid: str) -> tuple[Optional[RoomSession], Optional[Player]]:
        room_code = cls._sid_to_room.pop(sid, None)
        if not room_code:
            return None, None
            
        room = cls._rooms.get(room_code)
        if not room:
            return None, None
            
        player = room.remove_player(sid)
        if room.get_player_count() == 0:
            # Delete room if empty
            cls._rooms.pop(room_code, None)
            logger.info(f"Room {room_code} closed (no players left)")
            
        return room, player

    @classmethod
    def update_settings(cls, room_code: str, category: str, rounds: int, duration: int) -> bool:
        room = cls.get_room(room_code)
        if not room or room.status != "WAITING":
            return False
        room.category = category
        room.rounds = rounds
        room.round_duration = duration
        return True
