import time
import random
import threading
import logging
from typing import Optional, List, Dict, Any
from models import db, Song, Room, GameScore, User
from game.scoring import ScoringEngine
from utils.guess_matcher import check_guess
from services.trending_service import TrendingService

logger = logging.getLogger(__name__)

class GameManager:
    """
    Authoritative Server-Side Game Manager for a specific room.
    Handles round transitions, song selection, timer loops, and scoring.
    """
    def __init__(self, room_session, socketio, app=None):
        self.room = room_session
        self.socketio = socketio
        if app is None:
            try:
                from flask import current_app
                self.app = current_app._get_current_object()
            except Exception:
                self.app = None
        else:
            self.app = app

        self.current_round = 0
        self.total_rounds = room_session.rounds
        self.drawer_rotation: List[str] = [] # List of player sids in order
        self.drawer_index = -1
        self.current_drawer_sid: Optional[str] = None
        self.current_song: Optional[Dict[str, Any]] = None
        self.used_song_ids: set = set()

        # Round state
        self.time_remaining = 0
        self.timer_thread: Optional[threading.Thread] = None
        self.timer_stop_event = threading.Event()
        self.correct_guessers_count = 0
        self.round_start_time = 0.0

        # Link GameManager back to RoomSession
        self.room.game_manager = self

    def _run_with_app_context(self, func):
        if self.app:
            with self.app.app_context():
                func()
        else:
            func()

    def start_game(self) -> bool:
        """Initialize and start the multiplayer game."""
        if self.room.get_player_count() < 2:
            return False

        self.room.status = "STARTING"
        self.current_round = 0
        self.used_song_ids.clear()

        # Reset all player scores
        for p in self.room.players.values():
            p.score = 0
            p.round_score = 0
            p.guessed_correctly = False

        # Build drawer rotation order
        self.drawer_rotation = list(self.room.players.keys())
        random.shuffle(self.drawer_rotation)
        self.drawer_index = -1

        # Emit game starting event to room
        self.socketio.emit("game_starting", {
            "room_code": self.room.room_code,
            "rounds": self.total_rounds,
            "category": self.room.category,
            "countdown": 3
        }, room=self.room.room_code)

        # Launch next round after brief countdown
        def delayed_start():
            time.sleep(3)
            self._run_with_app_context(self.start_next_round)

        threading.Thread(target=delayed_start, daemon=True).start()
        return True

    def select_song(self) -> Optional[Dict[str, Any]]:
        """Select a song matching category that hasn't been played yet in this room."""
        category = self.room.category
        
        # Check Trending service first if category is Trending
        if category == "Trending":
            trending_songs = TrendingService.get_trending_songs()
            available = [s for s in trending_songs if s.get("id") not in self.used_song_ids and s.get("title") not in self.used_song_ids]
            if available:
                selected = random.choice(available)
                self.used_song_ids.add(selected.get("id") or selected.get("title"))
                return selected

        # Query database for matching category
        query = Song.query.filter_by(category=category, active=True)
        all_category_songs = query.all()

        available_db = [s for s in all_category_songs if s.id not in self.used_song_ids]
        if not available_db:
            # Reset used songs if list exhausted
            self.used_song_ids.clear()
            available_db = all_category_songs

        if not available_db:
            # Ultimate fallback if no songs found in DB
            return {
                "id": 9999,
                "title": "Blinding Lights",
                "artist": "The Weeknd",
                "category": category,
                "difficulty": "EASY",
                "movie": None,
                "keywords": "sunglasses, night, city lights"
            }

        selected_song = random.choice(available_db)
        self.used_song_ids.add(selected_song.id)
        return selected_song.to_dict(include_secret=True)

    def get_masked_title(self, title: str) -> str:
        """Create masked title e.g. '_ _ _ _ _   _ _ _ _ _ _'."""
        words = title.split()
        masked_words = []
        for word in words:
            chars = []
            for c in word:
                if c.isalnum():
                    chars.append("_")
                else:
                    chars.append(c)
            masked_words.append(" ".join(chars))
        return "   ".join(masked_words)

    def start_next_round(self):
        """Advance to next round and drawer."""
        self.stop_timer()
        self.room.current_strokes.clear()
        self.correct_guessers_count = 0

        # Check if game completed
        if self.current_round >= self.total_rounds:
            self.finish_game()
            return

        self.current_round += 1

        # Advance drawer rotation (skipping disconnected players)
        active_sids = [sid for sid in self.room.players.keys()]
        if not active_sids:
            return

        self.drawer_rotation = [sid for sid in self.drawer_rotation if sid in active_sids]
        if not self.drawer_rotation:
            self.drawer_rotation = active_sids
            random.shuffle(self.drawer_rotation)

        self.drawer_index = (self.drawer_index + 1) % len(self.drawer_rotation)
        self.current_drawer_sid = self.drawer_rotation[self.drawer_index]

        # Reset round status for players
        for p in self.room.players.values():
            p.round_score = 0
            p.guessed_correctly = False

        # Select secret song
        self.current_song = self.select_song()
        self.room.status = "DRAWING"

        drawer_player = self.room.get_player(self.current_drawer_sid)
        drawer_name = drawer_player.name if drawer_player else "Unknown"
        masked_title = self.get_masked_title(self.current_song["title"])

        # 1. Send public round info to all players (WITHOUT secret title)
        public_info = {
            "round": self.current_round,
            "total_rounds": self.total_rounds,
            "category": self.room.category,
            "duration": self.room.round_duration,
            "drawer_sid": self.current_drawer_sid,
            "drawer_name": drawer_name,
            "masked_title": masked_title,
            "word_count": len(self.current_song["title"].split()),
            "players": [p.to_dict(is_drawer=(p.sid == self.current_drawer_sid)) for p in self.room.players.values()]
        }
        self.socketio.emit("round_started", public_info, room=self.room.room_code)

        # 2. Send SECRET song data ONLY to drawer's private socket ID
        self.socketio.emit("your_secret_song", {
            "title": self.current_song["title"],
            "artist": self.current_song["artist"],
            "movie": self.current_song.get("movie"),
            "difficulty": self.current_song.get("difficulty", "MEDIUM"),
            "keywords": self.current_song.get("keywords")
        }, to=self.current_drawer_sid)

        logger.info(f"Round {self.current_round} started in {self.room.room_code}. Drawer: {drawer_name}. Secret: {self.current_song['title']}")

        # Start timer countdown
        self.start_timer(self.room.round_duration)

    def start_timer(self, duration: int):
        """Authoritative server countdown timer thread."""
        self.time_remaining = duration
        self.round_start_time = time.time()
        self.timer_stop_event.clear()

        def timer_worker():
            while self.time_remaining > 0 and not self.timer_stop_event.is_set():
                time.sleep(1)
                if self.timer_stop_event.is_set():
                    break
                self.time_remaining -= 1
                self.socketio.emit("timer_tick", {
                    "time_remaining": self.time_remaining,
                    "total_time": duration
                }, room=self.room.room_code)

            if not self.timer_stop_event.is_set() and self.time_remaining <= 0:
                self._run_with_app_context(lambda: self.end_round(reason="timeout"))

        self.timer_thread = threading.Thread(target=timer_worker, daemon=True)
        self.timer_thread.start()

    def stop_timer(self):
        """Stop running timer thread."""
        self.timer_stop_event.set()

    def process_guess(self, sid: str, guess_text: str) -> dict:
        """
        Authoritatively validate and score a submitted guess.
        """
        player = self.room.get_player(sid)
        if not player or not self.current_song or self.room.status != "DRAWING":
            return {"status": "ignored"}

        # Drawer cannot guess their own drawing
        if sid == self.current_drawer_sid:
            return {"status": "drawer_cannot_guess"}

        # Player already guessed correctly this round
        if player.guessed_correctly:
            return {"status": "already_guessed"}

        # Evaluate guess against secret song
        result = check_guess(
            guess=guess_text,
            title=self.current_song["title"],
            artist=self.current_song.get("artist"),
            movie=self.current_song.get("movie")
        )

        if result["is_correct"]:
            player.guessed_correctly = True
            player.guess_time = time.time()
            self.correct_guessers_count += 1

            # Compute authoritative score
            score_awarded = ScoringEngine.calculate_guess_score(
                time_remaining=self.time_remaining,
                total_time=self.room.round_duration,
                difficulty=self.current_song.get("difficulty", "MEDIUM"),
                guess_rank=self.correct_guessers_count
            )
            player.score += score_awarded
            player.round_score = score_awarded

            # Notify guesser privately of points
            self.socketio.emit("guess_result", {
                "is_correct": True,
                "points": score_awarded,
                "message": f"🎉 Correct! +{score_awarded} pts"
            }, to=sid)

            # Announce publicly to room that player guessed correctly (WITHOUT revealing answer)
            self.socketio.emit("player_guessed_correctly", {
                "player_name": player.name,
                "sid": player.sid,
                "score": player.score,
                "players": [p.to_dict(is_drawer=(p.sid == self.current_drawer_sid)) for p in self.room.players.values()]
            }, room=self.room.room_code)

            # Check if all active guessers have guessed correctly
            total_active_guessers = len(self.room.players) - 1
            if self.correct_guessers_count >= total_active_guessers and total_active_guessers > 0:
                self.end_round(reason="all_guessed")

            return {"status": "correct", "points": score_awarded}

        elif result["is_close"] or result["is_artist"] or result["is_movie"]:
            # Send private hint to this player only
            self.socketio.emit("guess_result", {
                "is_correct": False,
                "is_close": result["is_close"],
                "message": result["feedback"]
            }, to=sid)
            return {"status": "close", "feedback": result["feedback"]}

        else:
            # Normal incorrect guess - broadcast to game chat
            self.socketio.emit("chat_message", {
                "sender": player.name,
                "text": guess_text,
                "is_system": False
            }, room=self.room.room_code)
            return {"status": "incorrect"}

    def end_round(self, reason: str = "timeout"):
        """Authoritatively conclude the current round and reveal secret."""
        self.stop_timer()
        self.room.status = "ROUND_END"

        # Calculate drawer score based on how many players guessed
        total_guessers = max(1, len(self.room.players) - 1)
        drawer = self.room.get_player(self.current_drawer_sid)
        drawer_bonus = 0
        if drawer and self.correct_guessers_count > 0:
            drawer_bonus = ScoringEngine.calculate_drawer_score(
                correct_guess_count=self.correct_guessers_count,
                total_guessers=total_guessers
            )
            drawer.score += drawer_bonus
            drawer.round_score = drawer_bonus

        # Prepare round summary payload
        summary = {
            "reason": reason,
            "round": self.current_round,
            "total_rounds": self.total_rounds,
            "song": {
                "title": self.current_song["title"] if self.current_song else "",
                "artist": self.current_song.get("artist") if self.current_song else "",
                "movie": self.current_song.get("movie") if self.current_song else None
            },
            "drawer_name": drawer.name if drawer else "Unknown",
            "drawer_bonus": drawer_bonus,
            "correct_count": self.correct_guessers_count,
            "players": sorted(
                [p.to_dict(is_drawer=(p.sid == self.current_drawer_sid)) for p in self.room.players.values()],
                key=lambda x: x["score"],
                reverse=True
            ),
            "next_round_in": 5
        }

        self.socketio.emit("round_ended", summary, room=self.room.room_code)
        logger.info(f"Round {self.current_round} ended in {self.room.room_code}. Answer revealed: {summary['song']['title']}")

        # Intermission before next round (5s)
        def delayed_next():
            time.sleep(5)
            self._run_with_app_context(self.start_next_round)

        threading.Thread(target=delayed_next, daemon=True).start()

    def handle_drawer_disconnect(self):
        """Safely handle when active drawer disconnects mid-round."""
        logger.warning(f"Drawer disconnected mid-round in {self.room.room_code}")
        self.stop_timer()
        self.socketio.emit("system_announcement", {
            "message": "The drawer disconnected! Advancing to the next round..."
        }, room=self.room.room_code)

        def delayed_advance():
            time.sleep(3)
            self._run_with_app_context(self.start_next_round)

        threading.Thread(target=delayed_advance, daemon=True).start()

    def finish_game(self):
        """Conclude full game and show podium rankings."""
        self.stop_timer()
        self.room.status = "GAME_END"

        sorted_players = sorted(
            [p for p in self.room.players.values()],
            key=lambda p: p.score,
            reverse=True
        )

        results = {
            "room_code": self.room.room_code,
            "category": self.room.category,
            "total_rounds": self.total_rounds,
            "podium": [
                {"rank": i + 1, "name": p.name, "score": p.score, "sid": p.sid}
                for i, p in enumerate(sorted_players[:3])
            ],
            "leaderboard": [p.to_dict() for p in sorted_players]
        }

        # Save game scores to database
        def save_results():
            try:
                room_record = Room.query.filter_by(room_code=self.room.room_code).first()
                if room_record:
                    room_record.status = "FINISHED"
                    for idx, p in enumerate(sorted_players):
                        score_rec = GameScore(
                            room_id=room_record.id,
                            user_id=p.user_id,
                            player_name=p.name,
                            score=p.score
                        )
                        db.session.add(score_rec)

                        # Update User stats if authenticated
                        if p.user_id:
                            user = User.query.get(p.user_id)
                            if user:
                                user.games_played += 1
                                user.total_points += p.score
                                if idx == 0:
                                    user.games_won += 1
                                if p.score > user.best_score:
                                    user.best_score = p.score
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error saving game results to DB: {e}")

        self._run_with_app_context(save_results)

        self.socketio.emit("game_ended", results, room=self.room.room_code)

    def reset_for_play_again(self):
        """Reset game state for Play Again in same room."""
        self.stop_timer()
        self.room.status = "WAITING"
        self.current_round = 0
        self.used_song_ids.clear()
        self.room.current_strokes.clear()
        
        for p in self.room.players.values():
            p.score = 0
            p.round_score = 0
            p.guessed_correctly = False

        self.socketio.emit("lobby_reset", {
            "room_code": self.room.room_code,
            "players": [p.to_dict() for p in self.room.players.values()]
        }, room=self.room.room_code)
