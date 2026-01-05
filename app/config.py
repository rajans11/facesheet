import os

# Environment info
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

PARENT_FOLDER = os.getenv("PARENT_FOLDER")
TEMPLATE_DIR = "templates"
IMAGE_DRIVE_FOLDER_ID = os.getenv("IMAGE_DRIVE_FOLDER_ID")

PORT = int(os.getenv("PORT", 8080))
BASE_URL = os.getenv("BASE_URL") if IS_PRODUCTION else f"http://localhost:{PORT}"
