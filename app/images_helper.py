import os
import unicodedata
from dotenv import load_dotenv

from logger import log_message
from google_auth_helper import get_drive_service

# === Environment Setup ===
load_dotenv()

# Drive service
drive_service = get_drive_service()

# Global index
_image_index = {}

def initialize_image_index(PARENT_FOLDER_ID):
    """Fetch all image names from 'images' subfolder in Google Drive and normalize to lowercase."""
    global _image_index
    _image_index = {}  # Reset index each run
    log_message("🔄 Initializing image index from Google Drive 'images' subfolder...")

    try:
        images_folder_response = drive_service.files().list(
            q=f"'{PARENT_FOLDER_ID}' in parents and name='images' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id)",
            pageSize=1
        ).execute()

        images_folder = images_folder_response.get('files')
        if not images_folder:
            error_message = f"⚠️ Error: 'images' subfolder not found within parent folder with ID: {PARENT_FOLDER_ID}"
            log_message(error_message)
            _image_index = {}
            return

        images_folder_id = images_folder[0]['id']

        page_token = None
        while True:
            response = drive_service.files().list(
                q=f"'{images_folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name)",
                pageSize=1000,
                pageToken=page_token
            ).execute()

            for item in response.get('files', []):
                name = item['name']
                file_id = item['id']
                norm_key = unicodedata.normalize('NFKD', name).lower()
                _image_index[norm_key] = f"https://lh3.googleusercontent.com/d/{file_id}=s750?authuser=0"

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        log_message(f"✅ Indexed {len(_image_index)} images from 'images' subfolder.")
    except Exception as e:
        error_message = f"⚠️ Error indexing images from Drive: {e}"
        log_message(error_message)
        _image_index = {}


def check_image_exists(image_name):
    """Look up the image in the normalized index with common extensions."""
    norm_name = unicodedata.normalize('NFKD', image_name).lower()

    for ext in ['.png', '.jpg', '.jpeg']:
        key = f"{norm_name}{ext}"
        if key in _image_index:
            return _image_index[key]

    log_message(f"❌ '{norm_name}' not found in Drive image index.")
    return None