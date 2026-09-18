/* =========================================================
   DRAW THE SONG - MAIN GAME CLIENT CONTROLLER
   Manages Lobby, Drawing Arena, Guessing, and Results
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  const roomCode = window.DTS_CONFIG.roomCode;
  const playerName = window.DTS_CONFIG.playerName;
  const userId = window.DTS_CONFIG.userId;

  // View Containers
  const lobbyView = document.getElementById("lobbyView");
  const gameView = document.getElementById("gameView");
  const roundOverlay = document.getElementById("roundOverlay");
  const gameOverOverlay = document.getElementById("gameOverOverlay");

  // Canvas Instance
  const drawingEngine = new DrawingCanvas("drawingCanvas");

  // DOM Elements - Topbar & Status
  const roundDisplay = document.getElementById("roundDisplay");
  const timerDisplay = document.getElementById("timerDisplay");
  const categoryDisplay = document.getElementById("categoryDisplay");
  const secretHintText = document.getElementById("secretHintText");
  const drawerSecretCard = document.getElementById("drawerSecretCard");
  const drawerSongTitle = document.getElementById("drawerSongTitle");
  const drawerSongMeta = document.getElementById("drawerSongMeta");

  // DOM Elements - Sidebar & Chat
  const playersScoreList = document.getElementById("playersScoreList");
  const chatMessagesList = document.getElementById("chatMessagesList");
  const guessForm = document.getElementById("guessForm");
  const guessInput = document.getElementById("guessInput");

  // DOM Elements - Lobby
  const lobbyPlayersGrid = document.getElementById("lobbyPlayersGrid");
  const lobbyPlayerCount = document.getElementById("lobbyPlayerCount");
  const startGameBtn = document.getElementById("startGameBtn");
  const copyRoomCodeBtn = document.getElementById("copyRoomCodeBtn");

  // State
  let isHost = false;
  let isDrawer = false;

  // Connect to WebSocket and join room
  window.gameSocket.connect();
  if (window.gameSocket.socket && window.gameSocket.socket.connected) {
    window.gameSocket.joinRoom(roomCode, playerName, userId);
  }
  window.gameSocket.socket.on("connect", () => {
    window.gameSocket.joinRoom(roomCode, playerName, userId);
  });

  // Copy Room Code Helper
  if (copyRoomCodeBtn) {
    copyRoomCodeBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(roomCode).then(() => {
        const originalText = copyRoomCodeBtn.innerHTML;
        copyRoomCodeBtn.innerHTML = "✓ Copied!";
        setTimeout(() => copyRoomCodeBtn.innerHTML = originalText, 2000);
      });
    });
  }

  // -------------------------------------------------------------
  // SOCKET EVENT LISTENERS
  // -------------------------------------------------------------

  // Initial Room State
  window.gameSocket.on("room_joined", (data) => {
    isHost = data.is_host;
    updateLobbyView(data);

    if (data.status === "DRAWING") {
      switchToGameView();
      if (data.round_info) {
        roundDisplay.textContent = `Round ${data.round_info.round} / ${data.round_info.total_rounds}`;
        categoryDisplay.textContent = data.round_info.category;
        timerDisplay.textContent = data.round_info.time_remaining;
        isDrawer = (data.round_info.drawer_sid === window.gameSocket.socket.id);
        drawingEngine.setCanDraw(isDrawer);
        if (!isDrawer) {
          secretHintText.style.display = "block";
          secretHintText.textContent = data.round_info.masked_title;
          drawerSecretCard.style.display = "none";
          guessInput.disabled = false;
          guessInput.placeholder = "Type your guess here...";
        }
      }
      if (data.strokes && data.strokes.length) {
        drawingEngine.syncStrokes(data.strokes);
      }
    } else {
      switchToLobbyView();
    }
  });

  // Player Joined
  window.gameSocket.on("player_joined", (data) => {
    updatePlayersList(data.players);
    appendChatMessage({
      sender: "SYSTEM",
      text: `${data.player_name} joined the room.`,
      is_system: true
    });
  });

  // Player Left
  window.gameSocket.on("player_left", (data) => {
    updatePlayersList(data.players);
    appendChatMessage({
      sender: "SYSTEM",
      text: `${data.player_name} left the room.`,
      is_system: true
    });
  });

  // Host Start Game
  if (startGameBtn) {
    startGameBtn.addEventListener("click", () => {
      startGameBtn.disabled = true;
      startGameBtn.textContent = "Starting...";
      window.gameSocket.startGame();
    });
  }

  // Game Starting (Countdown)
  window.gameSocket.on("game_starting", (data) => {
    appendChatMessage({
      sender: "SYSTEM",
      text: `Game starting in ${data.countdown} seconds! Get ready!`,
      is_system: true
    });
    switchToGameView();
  });

  // Round Started
  window.gameSocket.on("round_started", (data) => {
    // Hide any previous overlays
    roundOverlay.style.display = "none";
    gameOverOverlay.style.display = "none";

    // Update Topbar
    roundDisplay.textContent = `Round ${data.round} / ${data.total_rounds}`;
    categoryDisplay.textContent = data.category;
    timerDisplay.textContent = data.duration;
    timerDisplay.className = "timer-clock";

    // Drawer state check
    isDrawer = (data.drawer_sid === window.gameSocket.socket.id);
    drawingEngine.setCanDraw(isDrawer);
    drawingEngine.clearCanvas(false);

    if (isDrawer) {
      // Drawer view: drawer secret card will be populated by your_secret_song
      secretHintText.style.display = "none";
      drawerSecretCard.style.display = "inline-flex";
      guessInput.disabled = true;
      guessInput.placeholder = "You are drawing this round!";
    } else {
      // Guesser view: masked title
      secretHintText.style.display = "block";
      secretHintText.textContent = data.masked_title;
      drawerSecretCard.style.display = "none";
      guessInput.disabled = false;
      guessInput.placeholder = "Type your guess here and press Enter...";
      guessInput.focus();
    }

    updateScoreboard(data.players);

    appendChatMessage({
      sender: "SYSTEM",
      text: `Round ${data.round} started! ${data.drawer_name} is drawing clues!`,
      is_system: true
    });
  });

  // Secret Song Data (Only received by current drawer)
  window.gameSocket.on("your_secret_song", (song) => {
    drawerSongTitle.textContent = song.title;
    let metaText = `by ${song.artist}`;
    if (song.movie) metaText += ` (Movie: ${song.movie})`;
    drawerSongMeta.textContent = metaText;
  });

  // Timer Tick
  window.gameSocket.on("timer_tick", (data) => {
    timerDisplay.textContent = data.time_remaining;

    if (data.time_remaining <= 10 && data.time_remaining > 0) {
      timerDisplay.className = "timer-clock danger";
      window.soundEngine.playTick();
    } else if (data.time_remaining <= 20) {
      timerDisplay.className = "timer-clock warning";
    } else {
      timerDisplay.className = "timer-clock";
    }
  });

  // Drawing Events
  window.gameSocket.on("drawing_stroke", (stroke) => {
    if (!isDrawer) {
      drawingEngine.receiveStroke(stroke);
    }
  });

  window.gameSocket.on("drawing_clear", () => {
    if (!isDrawer) {
      drawingEngine.clearCanvas(false);
    }
  });

  window.gameSocket.on("drawing_undo", () => {
    if (!isDrawer) {
      drawingEngine.undo(false);
    }
  });

  // Player Guessed Correctly
  window.gameSocket.on("player_guessed_correctly", (data) => {
    window.soundEngine.playCorrect();
    updateScoreboard(data.players);

    const msgEl = document.createElement("div");
    msgEl.className = "chat-msg correct";
    msgEl.textContent = `🎉 ${data.player_name} guessed the song!`;
    chatMessagesList.appendChild(msgEl);
    chatMessagesList.scrollTop = chatMessagesList.scrollHeight;
  });

  // Private Guess Result Feedback
  window.gameSocket.on("guess_result", (data) => {
    if (data.is_correct) {
      window.soundEngine.playCorrect();
      guessInput.disabled = true;
      guessInput.placeholder = "You guessed correctly! Watch the rest of the round.";
    } else if (data.is_close) {
      window.soundEngine.playClose();
      const msgEl = document.createElement("div");
      msgEl.className = "chat-msg close";
      msgEl.textContent = `💡 Hint: ${data.message}`;
      chatMessagesList.appendChild(msgEl);
      chatMessagesList.scrollTop = chatMessagesList.scrollHeight;
    }
  });

  // Public Chat Message
  window.gameSocket.on("chat_message", (data) => {
    appendChatMessage(data);
  });

  // Round Ended
  window.gameSocket.on("round_ended", (data) => {
    window.soundEngine.playRoundEnd();
    showRoundEndOverlay(data);
    updateScoreboard(data.players);
  });

  // Game Ended (Podium)
  window.gameSocket.on("game_ended", (data) => {
    window.soundEngine.playGameOver();
    showGameOverOverlay(data);
  });

  // Lobby Reset on Play Again
  window.gameSocket.on("lobby_reset", (data) => {
    gameOverOverlay.style.display = "none";
    roundOverlay.style.display = "none";
    switchToLobbyView();
    updatePlayersList(data.players);
  });

  // Error Messages
  window.gameSocket.on("error_message", (data) => {
    alert(data.message || "An error occurred.");
  });

  // -------------------------------------------------------------
  // FORM & SUBMISSIONS
  // -------------------------------------------------------------

  if (guessForm) {
    guessForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = guessInput.value.trim();
      if (!text || isDrawer) return;

      window.gameSocket.submitGuess(text);
      guessInput.value = "";
    });
  }

  // -------------------------------------------------------------
  // UI RENDER HELPERS
  // -------------------------------------------------------------

  function switchToLobbyView() {
    if (lobbyView) lobbyView.style.display = "block";
    if (gameView) gameView.style.display = "none";
  }

  function switchToGameView() {
    if (lobbyView) lobbyView.style.display = "none";
    if (gameView) gameView.style.display = "flex";
  }

  function updateLobbyView(data) {
    updatePlayersList(data.players);
    if (startGameBtn) {
      if (isHost && data.players.length >= 2) {
        startGameBtn.disabled = false;
        startGameBtn.title = "Start the multiplayer game!";
      } else {
        startGameBtn.disabled = true;
        startGameBtn.title = isHost ? "Need at least 2 players to start." : "Waiting for host to start the game.";
      }
    }
  }

  function updatePlayersList(players) {
    if (!players) return;

    // Detect if this player is the host
    const mySid = window.gameSocket.sid || (window.gameSocket.socket ? window.gameSocket.socket.id : null);
    const me = players.find(p => (mySid && p.sid === mySid) || (p.name && p.name.toLowerCase() === playerName.toLowerCase()));
    if (me && me.is_host !== undefined) {
      isHost = me.is_host;
    }

    // Update Lobby Player Cards
    if (lobbyPlayersGrid) {
      lobbyPlayersGrid.innerHTML = "";
      players.forEach(p => {
        const card = document.createElement("div");
        card.className = `player-card ${p.is_host ? "is-host" : ""}`;
        card.innerHTML = `
          <div class="player-avatar">🎮</div>
          <div class="player-name" title="${p.name}">${p.name}</div>
          <span class="player-role-badge ${p.is_host ? "host" : "player"}">
            ${p.is_host ? "👑 Host" : "Player"}
          </span>
        `;
        lobbyPlayersGrid.appendChild(card);
      });
    }

    if (lobbyPlayerCount) {
      lobbyPlayerCount.textContent = `${players.length} / ${window.DTS_CONFIG.maxPlayers || 8}`;
    }

    // Update Start Button & Lobby Status
    if (startGameBtn) {
      if (isHost) {
        startGameBtn.style.display = "inline-flex";
        startGameBtn.disabled = (players.length < 2);
        startGameBtn.textContent = (players.length < 2) ? "Waiting for players (2 min)..." : "🚀 START GAME";
        startGameBtn.title = (players.length < 2) ? "Need at least 2 players to start." : "Start the multiplayer game!";
      } else {
        startGameBtn.style.display = "inline-flex";
        startGameBtn.disabled = true;
        startGameBtn.textContent = "⏳ Waiting for host to start...";
        startGameBtn.title = "Waiting for room host to start the game.";
      }
    }

    const lobbyStatusText = document.getElementById("lobbyStatusText");
    if (lobbyStatusText) {
      if (players.length < 2) {
        lobbyStatusText.textContent = "Waiting for players to join (2 minimum)...";
      } else if (isHost) {
        lobbyStatusText.textContent = "Ready to start! Click START GAME to begin.";
      } else {
        lobbyStatusText.textContent = "Room is ready! Waiting for the host to start...";
      }
    }

    // Also update Game Sidebar Scores
    updateScoreboard(players);
  }

  function updateScoreboard(players) {
    if (!playersScoreList || !players) return;
    playersScoreList.innerHTML = "";

    // Sort by score descending
    const sorted = [...players].sort((a, b) => b.score - a.score);

    sorted.forEach(p => {
      const item = document.createElement("div");
      let classes = "player-score-item";
      let badge = "🎮";

      if (p.is_drawer) {
        classes += " drawer";
        badge = "🎨";
      } else if (p.guessed_correctly) {
        classes += " guessed";
        badge = "✓";
      }

      item.className = classes;
      item.innerHTML = `
        <div class="player-score-left">
          <span class="player-badge-indicator">${badge}</span>
          <span class="player-score-name">${p.name}</span>
        </div>
        <span class="player-score-val">${p.score}</span>
      `;
      playersScoreList.appendChild(item);
    });
  }

  function appendChatMessage(data) {
    if (!chatMessagesList) return;
    const msgEl = document.createElement("div");
    msgEl.className = `chat-msg ${data.is_system ? "system" : ""}`;

    if (data.is_system) {
      msgEl.textContent = data.text;
    } else {
      msgEl.innerHTML = `<span class="sender">${data.sender}:</span> ${escapeHtml(data.text)}`;
    }

    chatMessagesList.appendChild(msgEl);
    chatMessagesList.scrollTop = chatMessagesList.scrollHeight;
  }

  function showRoundEndOverlay(data) {
    const revealSongTitle = document.getElementById("revealSongTitle");
    const revealSongArtist = document.getElementById("revealSongArtist");
    const revealSongMovie = document.getElementById("revealSongMovie");
    const revealRoundScores = document.getElementById("revealRoundScores");

    if (revealSongTitle) revealSongTitle.textContent = data.song.title;
    if (revealSongArtist) revealSongArtist.textContent = `by ${data.song.artist}`;

    if (revealSongMovie) {
      if (data.song.movie) {
        revealSongMovie.style.display = "inline-block";
        revealSongMovie.textContent = `🎬 Soundtrack: ${data.song.movie}`;
      } else {
        revealSongMovie.style.display = "none";
      }
    }

    if (revealRoundScores) {
      revealRoundScores.innerHTML = `
        <div style="margin: 1rem 0; font-size: 0.95rem; color: var(--text-secondary);">
          Drawer: <strong>${data.drawer_name}</strong> (+${data.drawer_bonus} pts) &bull; Guessed by <strong>${data.correct_count}</strong> player(s)
        </div>
      `;
    }

    roundOverlay.style.display = "flex";
  }

  function showGameOverOverlay(data) {
    roundOverlay.style.display = "none";

    const podiumContainer = document.getElementById("podiumContainer");
    if (podiumContainer) {
      podiumContainer.innerHTML = "";
      const p1 = data.podium[0];
      const p2 = data.podium[1];
      const p3 = data.podium[2];

      // Standard podium order: 2nd, 1st, 3rd
      const steps = [
        { rank: 2, player: p2, cls: "rank-2", badge: "🥈" },
        { rank: 1, player: p1, cls: "rank-1", badge: "👑" },
        { rank: 3, player: p3, cls: "rank-3", badge: "🥉" }
      ];

      steps.forEach(s => {
        if (s.player) {
          const stepEl = document.createElement("div");
          stepEl.className = `podium-step ${s.cls}`;
          stepEl.innerHTML = `
            <div style="font-size: 1.5rem; margin-bottom: 0.25rem;">${s.badge}</div>
            <div class="podium-player-name">${s.player.name}</div>
            <div class="podium-player-score">${s.player.score} pts</div>
            <div class="podium-bar">${s.rank}</div>
          `;
          podiumContainer.appendChild(stepEl);
        }
      });
    }

    const playAgainBtn = document.getElementById("playAgainBtn");
    if (playAgainBtn) {
      playAgainBtn.style.display = isHost ? "inline-flex" : "none";
      playAgainBtn.onclick = () => window.gameSocket.playAgain();
    }

    gameOverOverlay.style.display = "flex";
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
});
