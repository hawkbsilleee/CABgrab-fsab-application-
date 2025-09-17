from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
import threading
import time
from api_interface import get_course_info
from notifier import send_email
from authlib.integrations.flask_client import OAuth
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, UserMixin, current_user
)
import os

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY")
DB = "subscriptions.db"

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        crn TEXT NOT NULL,
        notified INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    # User is stored in session, just reload
    return User(user_id, session.get("email"))

# --- OAuth Setup ---
oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# --- Auth Routes ---
@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = token["userinfo"]
    email = user_info["email"]

    # enforce @brown.edu restriction
    # if not email.endswith("@brown.edu"):
    #     return "❌ Must use a @brown.edu email", 403

    user = User(id_=email, email=email)
    login_user(user)

    session["email"] = email
    return redirect(url_for("landing"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("landing"))

# --- Routes ---
@app.route("/")
@app.route("/landing")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        crns = request.form["crn"].split(",")
        
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        added = []
        failed = []

        for crn in crns:
            crn = crn.strip()
            if not crn:
                continue
            try:
                # Try fetching course info to validate CRN
                info = get_course_info(crn)
                if info and "seats_available" in info:
                    c.execute("INSERT INTO subscriptions (email, crn) VALUES (?, ?)", (current_user.email, crn))
                    added.append(crn)
                else:
                    failed.append(crn)
            except Exception as e:
                failed.append(crn)

        conn.commit()
        conn.close()

        # Optional: flash messages (requires enabling Flask's flash/secret key)
        if added:
            # print(f"✅ Added valid CRNs: {', '.join(added)}")
            flash(f"Added valid CRNs: {', '.join(added)}", "success")
        if failed:
            # print(f"❌ Invalid CRNs skipped: {', '.join(failed)}")
            flash(f"Invalid CRNs skipped: {', '.join(failed)}", "error")

        return redirect(url_for("dashboard"))

    # GET request
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, crn, datetime('now') FROM subscriptions WHERE email = ?", (current_user.email,))
    subscriptions = c.fetchall()
    conn.close()

    return render_template("index.html", subscriptions=subscriptions)

@app.route("/delete/<int:sub_id>", methods=["POST"])
@login_required
def delete_subscription(sub_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM subscriptions WHERE id = ? AND email = ?", (sub_id, current_user.email))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

# --- Background Poller ---
def poll_loop():
    while True:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT id, email, crn, notified FROM subscriptions")
        subs = c.fetchall()

        for sub_id, email, crn, notified in subs:
            try:
                info = get_course_info(crn)
                time.sleep(2)
                seats = info["seats_available"]

                # If seats are open and we haven’t emailed this user yet
                if seats > 0 and notified == 0:
                    send_email(crn, email)
                    c.execute("UPDATE subscriptions SET notified = 1 WHERE id = ?", (sub_id,))
                    conn.commit()   # 🔥 commit right away
                    print(f"📧 Sent alert to {email} for CRN {crn} ({seats} seats open)")

                # Reset notification if seats drop back down
                elif seats <= 0 and notified == 1:
                    c.execute("UPDATE subscriptions SET notified = 0 WHERE id = ?", (sub_id,))
                    conn.commit()   # 🔥 commit right away

            except Exception as e:
                print(f"❌ Error checking {crn}: {e}")

        conn.close()
        time.sleep(300)

threading.Thread(target=poll_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)