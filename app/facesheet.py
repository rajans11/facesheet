import os
import sys
import json

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from pdf import convert_html_to_pdf
from logger import log_message
from config import IS_PRODUCTION, PARENT_FOLDER, TEMPLATE_DIR
from google_auth_helper import get_sheet
from images_helper import initialize_image_index, check_image_exists
from sheet import fetch_pdf_config_settings, generate_grouped_people
from core import app
from upload_delete import upload_or_replace_file

# === Environment Setup ===
if not IS_PRODUCTION:
    load_dotenv()

# === Helpers ===
def return_response(payload):
    if not IS_PRODUCTION:
        print("\n🛠️  [DEV MODE OUTPUT]")
        print(json.dumps(payload, indent=2))
        print("🛠️  [END OUTPUT]\n")
    return payload

# === Main Workflow ===
def generate(email, sheet_id):
    log_message(f"👤 Starting generation for {email} using sheet ID: {sheet_id}")
    try:
        sheet = get_sheet(sheet_id)
        log_message(f"📄 Using Google Sheet: '{sheet.title}'")

        OUTPUT_HTML = f"{sheet.title}.html"
        OUTPUT_PDF = f"{sheet.title}.pdf"

        settings_data, size, top, bottom, logo_name = fetch_pdf_config_settings(sheet)
        log_message("⚙️ PDF Config settings fetched.")
        
        initialize_image_index(PARENT_FOLDER)

        grouped_people = generate_grouped_people(sheet)
        log_message(f"🧑‍🤝‍🧑 Grouped data for {len(grouped_people)} groups.")

        logo_path = check_image_exists(logo_name)
        log_message(f"🖼️ Logo path: {logo_path}")

        env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        tpl = env.get_template("facesheet.html")
        html = tpl.render(
            settings_data=settings_data,
            grouped_people=grouped_people,
            email=email,
            logo_path=logo_path
        )

        with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
            f.write(html)
        log_message(f"✍️ HTML written to: {OUTPUT_HTML}")

        log_message("🚧 Starting PDF generation...")
        convert_html_to_pdf(OUTPUT_HTML, OUTPUT_PDF, size, top, bottom)

        file_id, file_link = upload_or_replace_file(OUTPUT_PDF, OUTPUT_PDF, PARENT_FOLDER)

        payload = {"result": "Success", "pdf_link": file_link}
        if not IS_PRODUCTION:
            return_response(payload)
        return payload

    except Exception as e:
        error_payload = {"result": "Error", "error": str(e)}
        log_message(f"🔥 Error during generation: {e}")
        if not IS_PRODUCTION:
            return_response(error_payload)
        return error_payload

# === CLI Entrypoint ===
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python facesheet.py <email> <sheet_id>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])