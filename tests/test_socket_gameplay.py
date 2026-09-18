import unittest
import time
from app import create_app, socketio
from game.room_manager import RoomManager
from seed_songs import seed_database

class TestSocketGameplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure database has songs
        seed_database("testing")

    def setUp(self):
        self.app = create_app("testing")
        self.client1 = socketio.test_client(self.app)
        self.client2 = socketio.test_client(self.app)
        RoomManager._rooms.clear()
        RoomManager._sid_to_room.clear()

    def tearDown(self):
        if self.client1.is_connected():
            self.client1.disconnect()
        if self.client2.is_connected():
            self.client2.disconnect()

    def test_full_multiplayer_game_loop(self):
        # 1. Host creates room
        room = RoomManager.create_room(
            host_sid="host-init-Aryan",
            host_name="Aryan",
            category="English",
            rounds=3,
            round_duration=30,
            max_players=8
        )
        room_code = room.room_code

        # 2. Host joins
        self.client1.emit("join_room_socket", {
            "room_code": room_code,
            "player_name": "Aryan"
        })
        received1 = self.client1.get_received()
        joined_event = next(e for e in received1 if e["name"] == "room_joined")
        self.assertTrue(joined_event["args"][0]["is_host"])

        # 3. Second player joins
        self.client2.emit("join_room_socket", {
            "room_code": room_code,
            "player_name": "Alex"
        })
        received2 = self.client2.get_received()
        joined_event2 = next(e for e in received2 if e["name"] == "room_joined")
        self.assertFalse(joined_event2["args"][0]["is_host"])
        self.assertEqual(room.get_player_count(), 2)

        # 4. Host starts the game
        self.client1.emit("start_game", {})
        time.sleep(0.2)
        self.assertEqual(room.status, "STARTING")

        # 5. Wait for countdown (3 seconds) to trigger round 1
        time.sleep(3.5)
        self.assertEqual(room.status, "DRAWING")
        self.assertIsNotNone(room.game_manager.current_song)

        secret_title = room.game_manager.current_song["title"]
        drawer_sid = room.game_manager.current_drawer_sid
        drawer_player = room.get_player(drawer_sid)
        guesser_name = "Alex" if drawer_player.name == "Aryan" else "Aryan"
        guesser_client = self.client2 if guesser_name == "Alex" else self.client1
        drawer_client = self.client1 if guesser_client == self.client2 else self.client2

        # 6. Verify drawer received the secret song
        drawer_events = drawer_client.get_received()
        secret_event = next((e for e in drawer_events if e["name"] == "your_secret_song"), None)
        self.assertIsNotNone(secret_event)
        self.assertEqual(secret_event["args"][0]["title"], secret_title)

        # 7. Verify guesser received round_started with masked title and NO secret title
        guesser_events = guesser_client.get_received()
        round_event = next((e for e in guesser_events if e["name"] == "round_started"), None)
        self.assertIsNotNone(round_event)
        self.assertNotIn(secret_title, round_event["args"][0]["masked_title"])
        self.assertIn("_", round_event["args"][0]["masked_title"])

        # 8. Guesser submits incorrect guess
        guesser_client.emit("submit_guess", {"guess": "completely wrong song"})
        time.sleep(0.2)
        guesser_received = guesser_client.get_received()
        chat_msg = next((e for e in guesser_received if e["name"] == "chat_message"), None)
        self.assertIsNotNone(chat_msg)
        self.assertEqual(chat_msg["args"][0]["text"], "completely wrong song")

        # 9. Guesser submits correct guess
        guesser_client.emit("submit_guess", {"guess": secret_title})
        time.sleep(0.2)
        guesser_received_correct = guesser_client.get_received()
        guess_result = next((e for e in guesser_received_correct if e["name"] == "guess_result"), None)
        self.assertIsNotNone(guess_result)
        self.assertTrue(guess_result["args"][0]["is_correct"])
        self.assertGreater(guess_result["args"][0]["points"], 0)

        # 10. Verify game state recorded correct guess
        guesser_player = room.get_player_by_name(guesser_name)
        self.assertIsNotNone(guesser_player)
        self.assertTrue(guesser_player.guessed_correctly)
        self.assertGreater(guesser_player.score, 0)

if __name__ == "__main__":
    unittest.main()
