# DRAW THE SONG 🎵🎨
> **"Draw it. Guess it. Win it."**

A modern, real-time multiplayer drawing and musical guessing web game inspired by drawing games like Skribbl, but with a unique focus on music. Players take turns sketching visual clues representing secret English, Hollywood soundtrack, and Trending hit songs while others compete in real time to guess the track and climb the leaderboard!

---

## 🌟 Key Features

* **Real-time Multiplayer Canvas**: High-performance HTML5 Canvas with pointer event support (Mouse, Touch, and Pen/Stylus) broadcasting smooth vector strokes across clients over WebSockets.
* **Curated Song Database**: Over 50+ hand-curated tracks spanning **English Pop & Rock**, **Hollywood Cinema Soundtracks**, and **Trending Charts** (strictly curated without regional songs in initial version).
* **Strict Server-Authoritative Gameplay**:
  * The secret song title is **never** sent to guessers via HTML, JavaScript, or public APIs.
  * Guessers only see masked clues (`_ _ _ _ _   _ _ _ _ _ _`).
  * Scoring and timers run exclusively on the server to eliminate tampering.
* **Smart Guess Engine**: Normalizes punctuation, capitalization, and whitespace. Provides private hints when players guess the artist or are "very close" (Levenshtein distance tolerance).
* **Time-Decay Scoring System**: Points decay gracefully over the round duration, rewarding the fastest guessers with bonus points, and rewarding the drawer for successful guesses.
* **Native Web Audio Effects**: Synthesized sound effects for clock countdowns, correct guesses, hints, round conclusions, and podium celebrations (zero external dependencies and zero copyrighted audio playback).
* **Cyber-Neon Gaming UI**: Sleek dark mode glassmorphism interface, custom typography, responsive layout for mobile/tablets, and podium animations.
* **User Accounts & Leaderboard**: Optional guest play with full account registration, tracking total points, match victories, and best scores.

---

## 🛠️ Technology Stack

* **Backend**:
  * Python 3.14+
  * [Flask](https://flask.palletsprojects.com/) (Application framework & routing)
  * [Flask-SocketIO](https://flask-socketio.readthedocs.io/) & [simple-websocket](https://github.com/miguelgrinberg/simple-websocket) (Real-time bidirectional event streaming)
  * [SQLAlchemy](https://www.sqlalchemy.org/) & Flask-SQLAlchemy (ORM for User, Room, Song, and GameScore persistence)
  * [SQLite](https://www.sqlite.org/) (Development database, easily swappable with PostgreSQL/MySQL)
  * [Flask-CORS](https://flask-cors.readthedocs.io/)
* **Frontend**:
  * HTML5 Semantic markup
  * Vanilla CSS3 (Custom Neon Design System, Glassmorphism, Responsive Grid/Flexbox)
  * Vanilla JavaScript (ES6+ Classes, HTML5 Canvas API, Web Audio API)
  * Socket.IO Client 4.7.5

---

## 📁 Architecture & Directory Structure

```
Guessthesongbydraw/
├── app.py                      # Flask & SocketIO application factory & entrypoint
├── config.py                   # Configuration classes (Dev, Testing, Prod)
├── requirements.txt            # Python package dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── seed_songs.py               # Database seeder script
├── README.md                   # Project documentation
│
├── database/                   # SQLite database directory
│   └── database.db
│
├── models/                     # SQLAlchemy data models
│   ├── __init__.py
│   ├── user.py                 # User authentication & stats
│   ├── song.py                 # Song metadata & masked title generator
│   └── room.py                 # Room and GameScore models
│
├── game/                       # Authoritative Game Logic Engine
│   ├── __init__.py
│   ├── room_manager.py         # In-memory room sessions & player rosters
│   ├── game_manager.py         # Round state machine, drawer rotation, timer thread
│   └── scoring.py              # Time-decay score formula & drawer bonus
│
├── routes/                     # HTTP Route Blueprints
│   ├── __init__.py
│   ├── main_routes.py          # Landing page & global leaderboard
│   ├── game_routes.py          # Room creation, joining, and game view
│   ├── auth_routes.py          # User authentication & profile management
│   └── song_routes.py          # Public song listing API (with masked secrets)
│
├── sockets/                    # Socket.IO Event Handlers
│   ├── __init__.py
│   └── game_socket.py          # Drawing, guessing, timer, and lobby events
│
├── utils/                      # Helper Utilities
│   ├── __init__.py
│   ├── helpers.py              # Unique collision-resistant room codes (e.g. X7K92)
│   ├── validators.py           # Form and room settings validation
│   └── guess_matcher.py        # Smart normalization & close-guess distance
│
├── services/                   # Service Layer
│   ├── __init__.py
│   └── trending_service.py     # Dynamic chart service hook & fallback
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Base layout, navbar, audio controls
│   ├── index.html              # Landing page (Hero, flow, features, categories)
│   ├── create_room.html        # Create game room form
│   ├── join_room.html          # Join room with 5-letter code
│   ├── game.html               # Main game arena (Lobby, Canvas, Chat, Modals)
│   ├── leaderboard.html        # Global high score rankings
│   ├── profile.html            # Player stats & profile
│   ├── login.html              # Login form
│   └── register.html           # User registration form
│
├── static/                     # Static Web Assets
│   ├── css/
│   │   ├── style.css           # Design tokens, buttons, glass cards, reset
│   │   ├── home.css            # Landing page layout & animations
│   │   ├── lobby.css           # Lobby player cards & room code display
│   │   ├── game.css            # Canvas container, drawing tools, chat
│   │   └── responsive.css      # Tablet & mobile responsive breakpoints
│   └── js/
│       ├── sound.js            # Web Audio API synthesizer
│       ├── websocket.js        # Socket.IO client interface
│       ├── canvas.js           # HTML5 Canvas vector drawing engine
│       └── game.js             # Main game state controller
│
├── data/                       # Datasets
│   └── songs.json              # 50+ curated English, Hollywood, and Trending tracks
│
└── tests/                      # Automated Test Suite
    ├── test_scoring.py         # Unit tests for scoring engine
    ├── test_guess_matcher.py   # Unit tests for normalization & hints
    ├── test_songs.py           # Unit tests for song filtering & masking
    └── test_game.py            # Unit tests for room lifecycle & validators
```

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ (tested on Python 3.14)
* Modern web browser (Chrome, Edge, Firefox, Safari)

### 2. Installation

1. Clone the repository and navigate into the root directory:
   ```bash
   cd Guessthesongbydraw
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize and seed the database:
   ```bash
   python seed_songs.py
   ```

5. Launch the application:
   ```bash
   python app.py
   ```

6. Open your browser and visit:
   ```
   http://localhost:5000
   ```

---

## 🧪 Running Automated Tests

Run the complete test suite with Python's built-in `unittest` runner:
```bash
python -m unittest discover tests
```

---

## 🎮 How Multiplayer Gameplay Works

1. **Create Room**:
   * A player sets the category (*English*, *Hollywood*, or *Trending*), number of rounds (3–10), and round duration (30–90 seconds).
   * A unique 5-letter room code (e.g., `X7K92`) is generated.
2. **Join Room**:
   * Friends enter their names and the room code to join the live lobby.
   * Player counts and host status update in real time.
3. **Round Start**:
   * The host starts the game (minimum 2 players required).
   * The server assigns the first drawer and randomly selects a secret song.
   * The secret song is transmitted **only** to the drawer's private socket ID.
   * Guessers receive only the masked dashes (e.g., `_ _ _ _ _   _ _ _ _ _ _`).
4. **Live Drawing & Guessing**:
   * As the drawer sketches on the HTML5 canvas, vector stroke deltas (`x, y, px, py, color, size, tool`) are streamed instantly to all connected players.
   * Guessers type in the chat box. Correct guesses trigger sound effects, award time-based points, and update the live scoreboard.
5. **Round End & Rotation**:
   * When the timer expires or all guessers succeed, the song is revealed, points are tallied, and the drawer rotates to the next player.
6. **Game Over**:
   * The top 3 players take the animated podium (1st, 2nd, and 3rd).
   * The host can click **Play Again** to restart without leaving the room.

---

## 🤖 Future AI / ML Roadmap

1. **AI Drawing Recognition**: Computer vision models (e.g. lightweight CNN or vision embeddings) to analyze canvas strokes in real time and detect visual song concepts.
2. **AI Smart Clues**: Automated progressive hints generated based on artist discography and lyrics without spoiling the title.
3. **Semantic Guess Matching**: Natural language embeddings to match clever colloquial phrasing and alternate titles with server verification.

---

## 📄 License
MIT License. Built for fun, music lovers, and gamers! 🎵🎨
