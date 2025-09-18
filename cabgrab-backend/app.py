from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
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
import firebase_admin
from firebase_admin import credentials, firestore

# -----------------------------
# Flask Setup
# -----------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config.update(
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=False,  # True if using HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    # PERMANENT_SESSION_LIFETIME=timedelta(hours=1)
)

# Enable CORS for frontend
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# -----------------------------
# Firebase Setup
# -----------------------------
cred = credentials.Certificate("cabgrab-12478-firebase-adminsdk-fbsvc-d92b5a1a0c.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# -----------------------------
# Flask-Login Setup
# -----------------------------
login_manager = LoginManager()
login_manager.login_view = "api_login"
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id_, email):
        self.id = id_
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    return User(user_id, session.get("email"))

# -----------------------------
# OAuth Setup
# -----------------------------
oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# -----------------------------
# Auth Routes
# -----------------------------
@app.route("/api/login")
def api_login():
    redirect_uri = url_for("authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = token["userinfo"]
    email = user_info["email"]

    user = User(id_=email, email=email)
    login_user(user)
    session["email"] = email

    # Redirect to frontend dashboard
    return redirect("http://localhost:3000/")

@app.route("/api/logout")
@login_required
def api_logout():
    logout_user()
    session.clear()
    return jsonify({"success": True})

# -----------------------------
# API Routes for Next.js
# -----------------------------
@app.route("/api/subscriptions", methods=["GET", "POST"])
@login_required
def api_subscriptions():
    if request.method == "POST":
        data = request.get_json()
        crns = data.get("crn", "").split(",")
        added = []

        for crn in crns:
            crn = crn.strip()
            if not crn:
                continue
            try:
                info = get_course_info(crn)
                if not info:
                    print(f"CRN {crn} returned no course info.")
                    continue
                doc_ref = db.collection("subscriptions").add({
                    "email": current_user.email,
                    "crn": crn,
                    "notified": 0
                })
                added.append({
                    "id": doc_ref.id,
                    "crn": crn,
                    "date_added": None
                })
            except Exception as e:
                print(f"Failed to add CRN {crn}: {e}")
        return jsonify(added)

    # GET request
    subs_ref = db.collection("subscriptions").where("email", "==", current_user.email)
    subscriptions = [
        {"id": doc.id, "crn": doc.to_dict()["crn"], "date_added": None} 
        for doc in subs_ref.stream()
    ]
    return jsonify(subscriptions)

@app.route("/api/subscriptions/<sub_id>", methods=["DELETE"])
@login_required
def api_delete_subscription(sub_id):
    doc_ref = db.collection("subscriptions").document(sub_id)
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get("email") == current_user.email:
        doc_ref.delete()
        return jsonify({"success": True})
    return jsonify({"success": False}), 403

# -----------------------------
# Polling Loop for Seat Notifications
# -----------------------------
def poll_loop():
    while True:
        subs = db.collection("subscriptions").stream()
        for doc in subs:
            data = doc.to_dict()
            sub_id = doc.id
            email = data["email"]
            crn = data["crn"]
            notified = data.get("notified", 0)

            try:
                info = get_course_info(crn)
                time.sleep(2)
                seats = info["seats_available"]

                if seats > 0 and notified == 0:
                    send_email(crn, email)
                    db.collection("subscriptions").document(sub_id).update({"notified": 1})
                    print(f"Sent alert to {email} for CRN {crn} ({seats} seats open)")

                elif seats <= 0 and notified == 1:
                    db.collection("subscriptions").document(sub_id).update({"notified": 0})

            except Exception as e:
                print(f"Error checking {crn}: {e}")

        time.sleep(300)

threading.Thread(target=poll_loop, daemon=True).start()

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)