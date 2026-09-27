import os
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, make_response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "badminton.sqlite3"))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))

app = Flask(__name__)
app.config.update(SECRET_KEY=SECRET_KEY)


def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_code TEXT NOT NULL UNIQUE,
            group_name TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            venue_name TEXT NOT NULL,
            venue_address TEXT NOT NULL,
            max_players INTEGER NOT NULL DEFAULT 16,
            court_numbers TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            waitlisted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
        );
        """
    )

    # Upgrade databases created by the earlier pair-based version.
    columns = {row["name"] for row in db.execute("PRAGMA table_info(events)").fetchall()}
    if "max_players" not in columns:
        db.execute("ALTER TABLE events ADD COLUMN max_players INTEGER NOT NULL DEFAULT 16")
        if "max_pairs" in columns:
            db.execute("UPDATE events SET max_players = max_pairs * 2")

    # Migrate old pairs into individual players when possible.
    old_tables = {row["name"] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if "pairs" in old_tables:
        old_pairs = db.execute("SELECT event_id, partner_one, partner_two FROM pairs").fetchall()
        for pair in old_pairs:
            for name in (pair["partner_one"], pair["partner_two"]):
                exists = db.execute(
                    "SELECT 1 FROM players WHERE event_id = ? AND name = ?",
                    (pair["event_id"], name),
                ).fetchone()
                if not exists:
                    db.execute(
                        "INSERT INTO players (event_id, name, waitlisted) VALUES (?, ?, 0)",
                        (pair["event_id"], name),
                    )
    db.commit()
    db.close()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def get_event(public_code):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE public_code = ?", (public_code,)).fetchone()
    db.close()
    if event is None:
        abort(404)
    return event


def event_data(public_code):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE public_code = ?", (public_code,)).fetchone()
    if event is None:
        db.close()
        abort(404)
    players = db.execute(
        "SELECT * FROM players WHERE event_id = ? AND waitlisted = 0 ORDER BY id", (event["id"],)
    ).fetchall()
    waitlist = db.execute(
        "SELECT * FROM players WHERE event_id = ? AND waitlisted = 1 ORDER BY id", (event["id"],)
    ).fetchall()
    db.close()
    return event, players, waitlist


@app.template_filter("pretty_date")
def pretty_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%A, %B %-d, %Y")
    except ValueError:
        return value


@app.context_processor
def inject_helpers():
    return {"quote": quote}


@app.route("/")
def home():
    db = get_db()
    events = db.execute("SELECT * FROM events ORDER BY event_date DESC, start_time DESC").fetchall()
    db.close()
    return render_template("home.html", events=events)


@app.route("/j/<public_code>")
def event_page(public_code):
    event, players, waitlist = event_data(public_code)
    return render_template("event.html", event=event, players=players, waitlist=waitlist)


@app.post("/j/<public_code>/signup")
def signup(public_code):
    event, players, _ = event_data(public_code)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Please enter your name.", "error")
    else:
        db = get_db()
        already_signed_up = db.execute(
            "SELECT 1 FROM players WHERE event_id = ? AND lower(name) = lower(?)",
            (event["id"], name),
        ).fetchone()
        if already_signed_up:
            flash("That name is already signed up.", "error")
        else:
            is_waitlisted = len(players) >= event["max_players"]
            db.execute(
                "INSERT INTO players (event_id, name, waitlisted) VALUES (?, ?, ?)",
                (event["id"], name, int(is_waitlisted)),
            )
            db.commit()
            flash(
                "The session is full, so you were added to the waitlist."
                if is_waitlisted else "You were added to the lineup.",
                "success",
            )
        db.close()
    return redirect(url_for("event_page", public_code=public_code) + "#signup")


@app.route("/calendar/<public_code>.ics")
def calendar_event(public_code):
    event = get_event(public_code)
    start = datetime.strptime(f"{event['event_date']} {event['start_time']}", "%Y-%m-%d %H:%M")
    end = datetime.strptime(f"{event['event_date']} {event['end_time']}", "%Y-%m-%d %H:%M")
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    body = "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Badminton Signup//EN",
        "BEGIN:VEVENT", f"UID:{event['public_code']}@badminton-signup", f"DTSTAMP:{stamp}",
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}", f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{event['title']}", f"LOCATION:{event['venue_name']}\\, {event['venue_address']}",
        f"DESCRIPTION:{event['notes']}", "END:VEVENT", "END:VCALENDAR", "",
    ])
    response = make_response(body)
    response.headers["Content-Type"] = "text/calendar; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=badminton-session.ics"
    return response


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
            session["admin_authenticated"] = True
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Incorrect password.", "error")
    return render_template("admin_login.html")


@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin_dashboard():
    if request.method == "POST":
        required = ["group_name", "title", "event_date", "start_time", "end_time", "venue_name", "venue_address"]
        if any(not request.form.get(field, "").strip() for field in required):
            flash("Please complete all required event fields.", "error")
        else:
            code = secrets.token_urlsafe(12)
            db = get_db()
            db.execute(
                """INSERT INTO events
                (public_code, group_name, title, event_date, start_time, end_time,
                 venue_name, venue_address, max_players, court_numbers, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    code, request.form["group_name"].strip(), request.form["title"].strip(),
                    request.form["event_date"], request.form["start_time"], request.form["end_time"],
                    request.form["venue_name"].strip(), request.form["venue_address"].strip(),
                    max(1, int(request.form.get("max_players", 16))),
                    request.form.get("court_numbers", "").strip(), request.form.get("notes", "").strip(),
                ),
            )
            db.commit()
            db.close()
            flash("Event created.", "success")
            return redirect(url_for("admin_dashboard"))
    db = get_db()
    events = db.execute("SELECT * FROM events ORDER BY event_date DESC, start_time DESC").fetchall()
    db.close()
    return render_template("admin.html", events=events)


@app.get("/admin/events/<int:event_id>")
@admin_required
def admin_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    players = db.execute("SELECT * FROM players WHERE event_id = ? ORDER BY waitlisted, id", (event_id,)).fetchall()
    db.close()
    if event is None:
        abort(404)
    return render_template("admin_event.html", event=event, players=players)


@app.post("/admin/players/<int:player_id>/delete")
@admin_required
def delete_player(player_id):
    db = get_db()
    player = db.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    if player:
        was_active = player["waitlisted"] == 0
        db.execute("DELETE FROM players WHERE id = ?", (player_id,))
        if was_active:
            next_player = db.execute(
                "SELECT id FROM players WHERE event_id = ? AND waitlisted = 1 ORDER BY id LIMIT 1",
                (player["event_id"],),
            ).fetchone()
            if next_player:
                db.execute("UPDATE players SET waitlisted = 0 WHERE id = ?", (next_player["id"],))
        db.commit()
    db.close()
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.post("/admin/events/<int:event_id>/delete")
@admin_required
def delete_event(event_id):
    db = get_db()
    db.execute("DELETE FROM players WHERE event_id = ?", (event_id,))
    db.execute("DELETE FROM events WHERE id = ?", (event_id,))
    db.commit()
    db.close()
    flash("Event deleted.", "success")
    return redirect(url_for("admin_dashboard"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
