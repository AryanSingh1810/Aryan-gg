from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, GameScore
from utils.helpers import sanitize_string

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = sanitize_string(request.form.get("username", ""))
        email = sanitize_string(request.form.get("email", "")).lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        favorite_category = request.form.get("favorite_category", "English")

        if not username or len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template("register.html", form=request.form)

        if not email or "@" not in email:
            flash("Please enter a valid email address.", "error")
            return render_template("register.html", form=request.form)

        if not password or len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html", form=request.form)

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html", form=request.form)

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash("Username already taken. Please choose another.", "error")
            return render_template("register.html", form=request.form)

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "error")
            return render_template("register.html", form=request.form)

        user = User(
            username=username,
            email=email,
            favorite_category=favorite_category
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["username"] = user.username
        session["player_name"] = user.username
        flash(f"Welcome to Draw the Song, {user.username}!", "success")
        return redirect(url_for("main.index"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = sanitize_string(request.form.get("login_id", "")).strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.username == login_id) | (User.email == login_id.lower())
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid username/email or password.", "error")
            return render_template("login.html", login_id=login_id)

        session["user_id"] = user.id
        session["username"] = user.username
        session["player_name"] = user.username
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for("main.index"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))

@auth_bp.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to view your profile.", "info")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    recent_games = GameScore.query.filter_by(user_id=user.id).order_by(GameScore.created_at.desc()).limit(10).all()

    return render_template("profile.html", user=user, recent_games=recent_games)
