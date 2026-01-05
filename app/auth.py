import os
import requests
from flask import redirect, session, url_for, jsonify, render_template, request
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

from config import IS_PRODUCTION, BASE_URL
from google_auth_helper import has_drive_access
from logger import log_message

if not IS_PRODUCTION:
    load_dotenv()

# OAuth setup
oauth = OAuth()
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile', 'prompt': 'select_account'}
)

# Redirect URI
oauth_redirect_uri = f"{BASE_URL}/login/authorized"

def setup_oauth(app):
    """Configure OAuth with the app."""
    oauth.init_app(app)

def login():
    """Redirect to Google's OAuth login."""
    session.clear()
    submitted_email = request.form.get('email')
    if not submitted_email:
        return render_template("login.html", error="Please enter an email.")
    
    log_message(f"[Login] Submitted email: {submitted_email}")
    session['submitted_email'] = submitted_email.strip().lower()
    return google.authorize_redirect(redirect_uri=oauth_redirect_uri)

def logout():
    """Clear session and log the user out of Google OAuth."""
    user = session.get('email', 'Unknown')
    log_message(f"[Logout] User: {user}")
    
    revoke_google_token()
    session.clear()
    return redirect(f"https://accounts.google.com/Logout?continue=https://appengine.google.com/_ah/logout?continue={BASE_URL}")

def authorized():
    """Handle the OAuth callback and verify email."""
    token = google.authorize_access_token()
    session['oauth_token'] = token  # Store token for revocation if needed

    user_info = token.get('userinfo') or google.get('userinfo').json()
    oauth_email = user_info.get('email', '').strip().lower()
    submitted_email = session.get('submitted_email', '').strip().lower()

    if oauth_email != submitted_email:
        log_message(f"[Mismatch] OAuth email ({oauth_email}) does not match submitted email ({submitted_email})")
        return render_template('login.html', error=f"⚠️ OAuth email ({oauth_email}) does not match submitted email ({submitted_email}).")

    if has_drive_access(oauth_email):
        log_message(f"[Access] Access granted to: {oauth_email}")
        session['email'] = oauth_email
        return redirect(url_for('home'))  # make sure `home` route exists
    else:
        log_message(f"[Access] Access denied for: {oauth_email}")
        return render_template('login.html', error=f"🚫 Access denied for {oauth_email}.")

def revoke_google_token():
    """Revoke the user's Google OAuth token."""
    token = session.get('oauth_token')
    if token:
        try:
            response = requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={'token': token['access_token']},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
            if response.status_code == 200:
                log_message("[Revoke] Google OAuth token revoked successfully.")
            else:
                log_message(f"[Revoke] Failed to revoke token: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            log_message(f"[Revoke] Error revoking token: {e}")

def check_login():
    """Check if the user is logged in."""
    return 'email' in session