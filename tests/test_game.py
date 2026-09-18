import unittest
from game.room_manager import RoomManager
from utils.validators import validate_player_name, validate_room_settings

class TestRoomLifecycle(unittest.TestCase):
    def setUp(self):
        RoomManager._rooms.clear()
        RoomManager._sid_to_room.clear()

    def test_room_creation(self):
        room = RoomManager.create_room(
            host_sid="sid-1",
            host_name="HostPlayer",
            category="English",
            rounds=5,
            round_duration=60,
            max_players=8
        )
        self.assertIsNotNone(room.room_code)
        self.assertEqual(len(room.room_code), 5)
        self.assertEqual(room.get_player_count(), 1)
        self.assertTrue(room.players["sid-1"].is_host)

    def test_join_room_and_capacity(self):
        room = RoomManager.create_room("sid-1", "HostPlayer", max_players=2)
        code = room.room_code

        # Join player 2
        r, p2, err = RoomManager.join_room(code, "sid-2", "Player2")
        self.assertIsNone(err)
        self.assertEqual(room.get_player_count(), 2)

        # Attempt to join player 3 in full room
        r3, p3, err3 = RoomManager.join_room(code, "sid-3", "Player3")
        self.assertIsNotNone(err3)
        self.assertIn("full", err3.lower())

    def test_host_reassignment_on_disconnect(self):
        room = RoomManager.create_room("sid-1", "HostPlayer")
        code = room.room_code
        RoomManager.join_room(code, "sid-2", "SecondPlayer")

        # Host leaves
        r, removed = RoomManager.leave_room("sid-1")
        self.assertEqual(room.get_player_count(), 1)
        # Second player must become the new host
        self.assertTrue(room.players["sid-2"].is_host)
        self.assertEqual(room.host_sid, "sid-2")

    def test_validators(self):
        # Invalid player names
        self.assertFalse(validate_player_name("")[0])
        self.assertFalse(validate_player_name("a")[0])
        self.assertFalse(validate_player_name("name<script>")[0])
        self.assertTrue(validate_player_name("Rockstar99")[0])

        # Invalid room settings
        self.assertFalse(validate_room_settings("Bollywood", 5, 60, 8)[0]) # Bollywood not supported
        self.assertFalse(validate_room_settings("English", 1, 60, 8)[0])    # rounds < 3
        self.assertFalse(validate_room_settings("English", 5, 120, 8)[0])   # duration > 90
        self.assertTrue(validate_room_settings("Hollywood", 5, 60, 8)[0])

if __name__ == "__main__":
    unittest.main()
