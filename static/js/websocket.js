/* =========================================================
   DRAW THE SONG - WEBSOCKET CLIENT WRAPPER
   Manages Socket.IO connection and event dispatching
   ========================================================= */

class GameSocket {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.sid = null;
    this.listeners = new Map();
  }

  connect() {
    if (this.socket) return;

    // Connect to current origin
    this.socket = io({
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000
    });

    this.socket.on("connect", () => {
      this.connected = true;
      this.sid = this.socket.id;
      console.log("⚡ Connected to Draw the Song WebSocket server. SID:", this.sid);
    });

    this.socket.on("disconnect", (reason) => {
      this.connected = false;
      console.warn("🔌 Disconnected from server:", reason);
    });

    this.socket.on("connect_error", (error) => {
      console.error("Socket connection error:", error);
    });
  }

  emit(event, data) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  joinRoom(roomCode, playerName, userId = null) {
    this.emit("join_room_socket", {
      room_code: roomCode,
      player_name: playerName,
      user_id: userId
    });
  }

  submitGuess(guess) {
    this.emit("submit_guess", { guess: guess });
  }

  sendStroke(strokeData) {
    this.emit("drawing_stroke", strokeData);
  }

  sendClear() {
    this.emit("drawing_clear", {});
  }

  sendUndo() {
    this.emit("drawing_undo", {});
  }

  startGame() {
    this.emit("start_game", {});
  }

  updateSettings(settings) {
    this.emit("update_settings", settings);
  }

  playAgain() {
    this.emit("play_again", {});
  }
}

window.gameSocket = new GameSocket();
