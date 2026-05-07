import os
import time
import unicodedata
from dotenv import load_dotenv

from logger import log_message
from google_auth_helper import get_drive_service

# === Environment Setup ===
load_dotenv()

# Drive service
drive_service = get_drive_service()

# Global index with TTL-based cache (5 minutes)
_image_index = {}
_index_folder_id = None
_index_built_at = 0.0
_INDEX_TTL = 300

def initialize_image_index(PARENT_FOLDER_ID):
    """Fetch all image names from 'images' subfolder in Google Drive and normalize to lowercase."""
    global _image_index, _index_folder_id, _index_built_at

    if _image_index and PARENT_FOLDER_ID == _index_folder_id and (time.time() - _index_built_at) < _INDEX_TTL:
        log_message(f"✅ Using cached image index ({len(_image_index)} images).")
        return

    _image_index = {}
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
                _image_index[norm_key] = f"https://lh3.googleusercontent.com/d/{file_id}=s400?authuser=0"

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        _index_folder_id = PARENT_FOLDER_ID
        _index_built_at = time.time()
        log_message(f"✅ Indexed {len(_image_index)} images from 'images' subfolder.")
    except Exception as e:
        error_message = f"⚠️ Error indexing images from Drive: {e}"
        log_message(error_message)
        _image_index = {}


def clear_image_cache():
    global _image_index, _index_built_at
    _image_index = {}
    _index_built_at = 0.0


def check_image_exists(image_name):
    """Look up the image in the normalized index with common extensions."""
    norm_name = unicodedata.normalize('NFKD', image_name).lower()

    for ext in ['.png', '.jpg', '.jpeg']:
        key = f"{norm_name}{ext}"
        if key in _image_index:
            return _image_index[key]

    log_message(f"❌ '{norm_name}' not found in Drive image index.")
    return None