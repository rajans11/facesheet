# Facesheet Generator

Facesheet is a simple app that generates a **PDF facesheet** from a **Google Spreadsheet** and associated **Drive images**.

It runs as a **Flask** app, deployed to **Google Cloud Run**, with secure OAuth login and Google Drive access.  
Designed to be lightweight, fast, and production-ready.

## ✨ Features

- **Google OAuth2** login for access control.
- **Service Account impersonation** for Drive/Sheets access (secure, no service account keys needed).
- **PDF generation** from HTML templates.
- **Upload images and spreadsheet-driven automation.**
- **Easy local development** + **one-command deploy**.

## ⚙️ Environment Variables

Make sure the following are set (typically in your `.env` file):

| Name                    | Description |
|:-------------------------|:------------|
| `PROJECT_ID`             | Your GCP project ID (e.g., `facesheet-457613`) |
| `REGION`                 | GCP region for deployment (e.g., `europe-west2`) |
| `IMAGE_NAME`             | Name of the Docker image (e.g., `facesheet-generator`) |
| `BASE_URL`               | Public URL of the deployed service |
| `GOOGLE_CLIENT_ID`       | OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET`   | OAuth 2.0 client secret |
| `SECRET_KEY`             | Flask session secret key |
| `IMAGE_DRIVE_FOLDER_ID`  | Google Drive folder ID for images |
| `PARENT_FOLDER`          | Google Drive folder ID for access control |
| `SERVICE_ACCOUNT_EMAIL`  | Service account email used for impersonation (e.g., `secure-sa@facesheet-457613.iam.gserviceaccount.com`) |
| `PORT`                   | (Optional) Port for local server (`8080` by default) |
| `USER_EMAIL`             | (Local-only) Your personal Google account email, used for impersonation when developing locally |

> **Notes:**
> - `PORT` is only needed for running the app locally.
> - `USER_EMAIL` is only needed for **local development impersonation** (ignored in production).
> - Keep your `SERVICE_ACCOUNT_EMAIL` private and secured.

## 🚀 Running Locally (venv)

```bash
# Create and activate your virtualenv
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run the Flask app (development mode)
python app/app.py
```

You can also generate a facesheet manually by running:

```bash
python app/facesheet.py your-email@example.com
```

## 🐳 Running Locally (Docker)

If you prefer to test locally with Docker (same as production):

```bash
# Build the Docker image
docker build -t facesheet-generator .

# Run it, binding to port 8080
docker run --env-file .env -p 8080:8080 facesheet-generator
```

Then visit:  
[http://localhost:8080](http://localhost:8080)

> Make sure your `.env` file is ready before running the container.

## ☁️ Deploying to Cloud Run

Ensure you are logged in with a user which allows you to deploy and then run:

```bash
gcloud auth login
```

Once logged in check the output is correct otherwise set it up against the correct google project ID

```bash
gcloud config set project PROJECT_ID
```

The below will run the correct roles against the deploy, containerise image and push to gcr and then deploy to google cloud run:

```bash
python deploy/deploy.py
```

This will:
- Build the Docker image
- Push it to Artifact Registry
- Deploy to Cloud Run (in your configured project and region)

Your production app will then be available at:

🔗 **Production URL:**
### [https://facesheet-generator-204707763164.europe-west2.run.app](https://facesheet-generator-204707763164.europe-west2.run.app)

## 🔒 Service Account Roles & Permissions

For security, a **Service Account** is used for Google API access, and **impersonated** (no private keys exposed).  
Correct roles must be assigned to this service account:

- `roles/run.admin`
- `roles/storage.admin`
- `roles/artifactregistry.writer`
- `roles/iam.serviceAccountUser`
- `roles/iam.serviceAccountTokenCreator`

You can **automatically fix** the roles using our helper script:

👉 See [`deploy/roles_manager.py`](deploy/roles_manager.py)

Run it like this:

```bash
python deploy/roles_manager.py
```

## 🔥 Highlights

- Fully serverless (only pays while running)
- Least privilege security design
- OAuth2 + Google Drive access combined
- Simple, readable codebase (Flask + pure Google libraries)
- Ready for production immediately

## 📂 Project Structure

```bash
app/
├── app.py              # Main Flask app
├── facesheet.py        # Facesheet generation logic
├── google_auth_helper.py # Handles Drive/Sheets/OAuth
templates/              # HTML templates
deploy/
├── deploy.py           # Build and deploy script
├── roles_manager.py    # Manage service account roles
.env                    # Environment variables (not checked into git)
requirements.txt        # Python dependencies
README.md               # This file
```

## 🛡️ Security Notes

- All Google API access uses short-lived OAuth2 tokens.
- No long-lived service account keys are exposed.
- Roles are automatically enforced for minimum privileges.
- User login is via secure OAuth2 with Google.

