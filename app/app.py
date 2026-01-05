import os
import shutil
from datetime import timedelta
import time
from dotenv import load_dotenv

from flask import Flask, render_template, session, request, redirect, url_for, jsonify, send_file
from flask_session import Session
from threading import Thread

from auth import login, check_login, setup_oauth, authorized
from facesheet import generate
from logger import log_message, LOG_FILE
from config import IS_PRODUCTION, BASE_URL, PORT, PARENT_FOLDER
from sheet import list_google_sheets
from datetime_helper import format_datetime
from core import app

# === Load environment variables ===
if not IS_PRODUCTION:
    load_dotenv()

app.config['BASE_URL'] = BASE_URL
app.secret_key = os.getenv("SECRET_KEY", "fallback-dev-key")

# === Session Setup ===
SESSION_FOLDER = os.path.join(os.getcwd(), 'flask_session')
if os.path.exists(SESSION_FOLDER):
    shutil.rmtree(SESSION_FOLDER)
os.makedirs(SESSION_FOLDER, exist_ok=True)

app.config.update({
    'SESSION_TYPE': 'filesystem',
    'SESSION_FILE_DIR': SESSION_FOLDER,
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': timedelta(days=7)
})
Session(app)

# === OAuth Setup ===
setup_oauth(app)

@app.route('/')
def home():
    if 'email' in session:
        sheets = list_google_sheets()
        for s in sheets:
            s["modifiedTime"] = format_datetime(s["modifiedTime"])
        return render_template('home.html', email=session.get('email'), sheets=sheets, parent=PARENT_FOLDER)
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        if not email or "@" not in email:
            error = "Please enter a valid email address."
        else:
            return login()
    return render_template('login.html', error=error)

@app.route('/login/authorized')
def authorized_route():
    return authorized()

@app.route('/logout')
def logout_route():
    session.clear()
    return redirect(url_for('login_page'))

@app.route("/me")
def me():
    return jsonify({"email": session.get("email")})

@app.route('/generate', methods=['POST'])
def generate_route():
    email = session.get("email")
    if not email:
        return jsonify({"error": "Not logged in"}), 403

    data = request.json
    sheet_id = data.get("sheet_id")
    if not sheet_id:
        return jsonify({"error": "Missing sheet_id"}), 400

    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    try:
        log_message("Generation started...")
        start_time = time.time()
        result = generate(email, sheet_id)
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        log_message(f"🎉 All done in {duration} seconds! PDF Link: {result.get('pdf_link')}")
        return jsonify({
            "pdf_link": result.get("pdf_link"),
            "duration": duration
        })
    except Exception as e:
        log_message(f"❌ Error during generation: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/logs')
def get_logs():
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, mimetype='text/plain')
    return "No logs available.", 404

@app.route("/sheets")
def get_sheets():
    return jsonify(list_google_sheets())

# === Main Entry Point ===
if __name__ == '__main__' and not IS_PRODUCTION:
    app.run(host='0.0.0.0', port=PORT, debug=True, threaded=True)

