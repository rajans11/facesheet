import os
from datetime import timedelta
import time
from dotenv import load_dotenv

# === Load environment variables BEFORE app imports ===
if os.getenv("ENVIRONMENT", "development") != "production":
    load_dotenv()

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
from image_search import search_images, save_image_to_drive, check_filename_exists, get_images_folder_url
from images_helper import clear_image_cache

app.config['BASE_URL'] = BASE_URL
app.secret_key = os.getenv("SECRET_KEY", "fallback-dev-key")

# === Session Setup ===
# Cloud Run only guarantees /tmp is writable; use it unconditionally in production
SESSION_FOLDER = '/tmp/flask_session' if IS_PRODUCTION else os.path.join(os.getcwd(), 'flask_session')
os.makedirs(SESSION_FOLDER, exist_ok=True)

app.config.update({
    'SESSION_TYPE': 'filesystem',
    'SESSION_FILE_DIR': SESSION_FOLDER,
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': timedelta(days=7),
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_SECURE': IS_PRODUCTION,
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


@app.route("/images-folder")
def images_folder_route():
    if "email" not in session:
        return jsonify({"error": "Not logged in"}), 403
    try:
        url = get_images_folder_url(PARENT_FOLDER)
        return jsonify({"url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/image-check")
def image_check_route():
    if "email" not in session:
        return jsonify({"error": "Not logged in"}), 403
    filename = (request.args.get("filename") or "").strip()
    if not filename:
        return jsonify({"error": "Missing filename"}), 400
    try:
        exists, existing_name = check_filename_exists(filename, PARENT_FOLDER)
        return jsonify({"exists": exists, "existing_name": existing_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/image-search")
def image_search_route():
    if "email" not in session:
        return jsonify({"error": "Not logged in"}), 403
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query"}), 400
    try:
        results = search_images(q)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/image-save", methods=["POST"])
def image_save_route():
    if "email" not in session:
        return jsonify({"error": "Not logged in"}), 403
    data = request.json or {}
    url = (data.get("url") or "").strip()
    filename = (data.get("filename") or "").strip()
    if not url or not filename:
        return jsonify({"error": "Missing url or filename"}), 400
    try:
        file_id, saved_name = save_image_to_drive(url, filename, PARENT_FOLDER)
        clear_image_cache()
        return jsonify({"success": True, "filename": saved_name, "file_id": file_id})
    except Exception as e:
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

