import unicodedata
from google_auth_helper import get_drive_service
from images_helper import check_image_exists
from logger import log_message
from config import PARENT_FOLDER

def fetch_pdf_config_settings(sheet):
    settings = sheet.worksheet("Settings").get_all_values()
    data = {row[0]: row[1] for row in settings[1:] if row[0]}

    pdf_size = data.get("PDFSize", "A4")
    top_margin = data.get("TopMargin", "0.5in")
    bottom_margin = data.get("BottomMargin", "0.5in")
    title_font_size = data.get("TitleFontSize", "24pt")
    logo_name = data.get("LogoName", "logo.png")
    logo_width = data.get("LogoWidth", "150px")
    logo_height = data.get("LogoHeight", "80px")

    return data, pdf_size, top_margin, bottom_margin, logo_name

def generate_grouped_people(sheet):
    """Reads people data from the 'People' sheet and groups them by category."""
    rows = sheet.worksheet("People").get_all_values()[1:]
    people = []
    for r in rows:
        if not any(cell.strip() for cell in r):
            continue
        name = r[1]
        
        # Using check_image_exists to get the image URL directly from Google Drive
        img = check_image_exists(name.replace(" ", "_"))  # No need for fallback here
        
        people.append({
            "Category": r[0],
            "Name": name,
            "Title": r[2],
            "Show": r[3] if len(r) > 3 else "",
            "Image File": img
        })

    # Group people by category
    grouped = {}
    for p in people:
        grouped.setdefault(p["Category"], []).append(p)
    
    return grouped

def list_google_sheets():
    try:
        drive_service = get_drive_service()
        response = drive_service.files().list(
            q=f"'{PARENT_FOLDER}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute()
        return response.get("files", [])
    except Exception as e:
        log_message(f"❌ Failed to list sheets: {e}")
        return []
