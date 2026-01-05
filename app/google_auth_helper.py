import os
import gspread
from googleapiclient.discovery import build
from google.auth import impersonated_credentials, default as google_auth_default
from config import IS_PRODUCTION

SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")
PARENT_FOLDER = os.getenv("PARENT_FOLDER")

# Scopes
SCOPES_FULL = ["https://www.googleapis.com/auth/drive"]
SCOPES_READONLY = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

def get_credentials(scopes):
    """Load credentials with proper scopes."""
    creds, _ = google_auth_default()

    if not IS_PRODUCTION:
        creds = impersonated_credentials.Credentials(
            source_credentials=creds,
            target_principal=SERVICE_ACCOUNT_EMAIL,
            target_scopes=scopes,
            lifetime=3600
        )
    else:
        if not hasattr(creds, 'scopes') or not set(scopes).issubset(set(creds.scopes or [])):
            creds = creds.with_scopes(scopes)

    return creds

def get_sheet(sheet_id):
    """Return a GSpread sheet client."""
    creds = get_credentials(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return gspread.authorize(creds).open_by_key(sheet_id)

def get_drive_service(readonly=False):
    """Return a Google Drive service."""
    scopes = SCOPES_READONLY if readonly else SCOPES_FULL
    creds = get_credentials(scopes)
    return build('drive', 'v3', credentials=creds)

def has_drive_access(email):
    """Check if an email has access to the parent folder."""
    try:
        service = get_drive_service(readonly=True)
        permissions = service.permissions().list(
            fileId=PARENT_FOLDER,
            fields="permissions(emailAddress, role)",
            supportsAllDrives=True
        ).execute()

        permitted_emails = [
            p['emailAddress'].lower()
            for p in permissions.get('permissions', [])
            if 'emailAddress' in p
        ]
        return email.lower() in permitted_emails
    except Exception as e:
        print(f"[Drive Access Check] Error: {e}")
        return False
