import subprocess
import os
import json
from dotenv import load_dotenv

DEPLOY_DIR = "deploy"

def run_command(cmd, capture_output=False):
    print(f"➡️ Running: {cmd}")
    if capture_output:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"❌ Command failed: {cmd}\n{result.stderr}")
        return result.stdout
    else:
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"❌ Command failed: {cmd}")

def get_current_roles(project_id, service_account_email):
    output = run_command(
        f"gcloud projects get-iam-policy {project_id} --format=json",
        capture_output=True
    )
    policy = json.loads(output)

    current_roles = []
    for binding in policy.get("bindings", []):
        members = binding.get("members", [])
        if f"serviceAccount:{service_account_email}" in members:
            current_roles.append(binding["role"])

    return current_roles

def ensure_correct_roles(dry_run=False):
    load_dotenv()

    PROJECT_ID = os.getenv("PROJECT_ID")
    SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL")
    USER_EMAIL = os.getenv("USER_EMAIL")
    IMAGE_NAME = os.getenv("IMAGE_NAME")
    REGION = os.getenv("REGION")

    if not PROJECT_ID or not SERVICE_ACCOUNT_EMAIL or not USER_EMAIL or not IMAGE_NAME:
        raise ValueError("Missing PROJECT_ID, SERVICE_ACCOUNT_EMAIL, USER_EMAIL, or IMAGE_NAME in .env!") # Modified

    allowed_roles = [
        "roles/run.admin",
        "roles/storage.admin",
        "roles/artifactregistry.writer",
        "roles/iam.serviceAccountUser",
        "roles/iam.serviceAccountTokenCreator"
    ]

    # Step 1: Add impersonation permission for your user
    run_command(
        f"gcloud iam service-accounts add-iam-policy-binding {SERVICE_ACCOUNT_EMAIL} "
        f"--member='user:{USER_EMAIL}' "
        f"--role='roles/iam.serviceAccountTokenCreator' "
        f"--project={PROJECT_ID}"
    )

    # Step 2: Grant invoker permission to the service account on the Cloud Run service
    print(f"➕ Ensuring service account '{SERVICE_ACCOUNT_EMAIL}' can invoke Cloud Run service '{IMAGE_NAME}'")
    if not dry_run:
        try:
            run_command(
                f"gcloud run services add-iam-policy-binding {IMAGE_NAME} "
                f"--member='serviceAccount:{SERVICE_ACCOUNT_EMAIL}' "
                f"--role='roles/run.invoker' "
                f"--project={PROJECT_ID} "
                f"--region={REGION}"

            )
            print(f"✅ Service account '{SERVICE_ACCOUNT_EMAIL}' granted invoker permission on Cloud Run service '{IMAGE_NAME}'.")
        except RuntimeError as e:
            print(f"⚠️ Error granting invoker permission: {e}")

    # Step 3: Check existing roles
    current_roles = get_current_roles(PROJECT_ID, SERVICE_ACCOUNT_EMAIL)
    print(f"🔎 Current roles: {current_roles}")

    # Step 4: Remove any extra roles
    for role in current_roles:
        if role not in allowed_roles:
            print(f"🗑️ Removing extra role: {role}")
            if not dry_run:
                run_command(
                    f"gcloud projects remove-iam-policy-binding {PROJECT_ID} "
                    f"--member='serviceAccount:{SERVICE_ACCOUNT_EMAIL}' "
                    f"--role='{role}' "
                    f"--region={REGION}"
                )

    # Step 5: Add any missing roles
    for role in allowed_roles:
        if role not in current_roles:
            print(f"➕ Adding missing role: {role}")
            if not dry_run:
                run_command(
                    f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
                    f"--member='serviceAccount:{SERVICE_ACCOUNT_EMAIL}' "
                    f"--role='{role}' "
                    f"--region={REGION}"
                )

    print("✅ Service account roles are now correct!")

if __name__ == "__main__":
    ensure_correct_roles(dry_run=False)  # Set dry_run=True if you want a safe test first