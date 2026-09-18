from flask import Blueprint, render_template, request
from config import Config
from models import User, GameScore, db

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Draw & Guess modern landing page."""
    return render_template("index.html", modes=Config.GAME_MODES)

@main_bp.route("/modes")
def modes():
    """Game mode selection page: Guess the Song & Guess the Movie."""
    return render_template("mode_selection.html", modes=Config.GAME_MODES)

@main_bp.route("/leaderboard")
def leaderboard():
    """Global player leaderboard."""
    period = request.args.get("period", "all")
    
    # Query top players by total score
    top_users = User.query.order_by(User.total_points.desc()).limit(50).all()
    
    # Also get recent top game scores
    recent_scores = GameScore.query.order_by(GameScore.score.desc()).limit(20).all()

    return render_template(
        "leaderboard.html", 
        top_users=top_users, 
        recent_scores=recent_scores, 
        current_period=period
    )
