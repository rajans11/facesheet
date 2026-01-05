from googleapiclient.http import MediaFileUpload
from logger import log_message
from google_auth_helper import get_drive_service

drive_service = get_drive_service()

def upload_or_replace_file(file_path, filename, parent_id, mime_type="application/pdf"):
    """Uploads a file to Drive, replacing the old one if it exists."""
    try:
        existing = drive_service.files().list(
            q=f"'{parent_id}' in parents and name='{filename}' and trashed=false",
            fields="files(id)"
        ).execute().get('files', [])

        for f in existing:
            try:
                drive_service.files().delete(fileId=f['id']).execute()
                log_message(f"🗑️ Deleted old {filename}")
            except Exception as e:
                log_message(f"⚠️ Failed to delete {filename}: {e}")

        metadata = {
            'name': filename,
            'parents': [parent_id],
            'mimeType': mime_type
        }
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True, chunksize=25 * 1024 * 1024)
        upload = drive_service.files().create(body=metadata, media_body=media, fields='id').execute()

        file_link = f"https://drive.google.com/file/d/{upload['id']}/view"
        log_message(f"✅ Uploaded file")
        return upload['id'], file_link

    except Exception as e:
        log_message(f"❌ Upload error: {e}")
        return None, None