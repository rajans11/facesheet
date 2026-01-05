import os
import subprocess
import datetime
from dotenv import load_dotenv
import yaml

from roles_manager import ensure_correct_roles

DEPLOY_DIR = "deploy"

def load_env_to_dict():
    env_file_path = ".env"
    if not os.path.exists(env_file_path):
        print(".env file not found. Please make sure it's present.")
        return {}

    load_dotenv(dotenv_path=env_file_path)

    env_vars = {}
    with open(env_file_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value

    return env_vars

def generate_env_yaml(env_vars):
    for key in ['PORT', 'USER_EMAIL']:
        env_vars.pop(key, None)

    env_vars['ENVIRONMENT'] = 'production'

    os.makedirs(DEPLOY_DIR, exist_ok=True)
    yaml_file_path = os.path.join(DEPLOY_DIR, "env.yaml")
    with open(yaml_file_path, "w") as file:
        yaml.dump(env_vars, file, default_flow_style=False)

    print(f"✅ Environment variables written to {yaml_file_path}")

def run_command(cmd):
    print(f"➡️ Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"❌ Command failed: {cmd}")

def build_push_and_deploy(env_vars):
    project_id = env_vars["PROJECT_ID"]
    image_name = env_vars["IMAGE_NAME"]
    service_name = env_vars["IMAGE_NAME"]
    region = env_vars.get("REGION")

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    tag = f"{image_name}:{timestamp}"
    full_image = f"gcr.io/{project_id}/{tag}"

    print("🔧 Building Docker image...")
    run_command(f"docker build --platform=linux/amd64 -t {full_image} .")

    print("🚀 Pushing Docker image to Google Container Registry...")
    run_command(f"docker push {full_image}")

    print("🌐 Deploying to Google Cloud Run...")
    run_command(
        f"gcloud run deploy {service_name} "
        f"--image {full_image} "
        f"--region {region} "
        f"--platform managed "
        f"--allow-unauthenticated "
        f"--project {project_id} "
        f"--memory 4G "
        f"--cpu 2 "
        f"--service-account {env_vars['SERVICE_ACCOUNT_EMAIL']} "
        f"--env-vars-file={os.path.join(DEPLOY_DIR, 'env.yaml')}"
    )

    print(f"✅ Deployment complete: {tag}")

def setup_gcloud(project_id, region):

    subprocess.run(["gcloud", "--version"], check=True, capture_output=True)  # capture_output added
    print(f"Setting gcloud project to: {project_id}")
    run_command(
        f"gcloud config set project {project_id}"
    )
    print(f"Setting gcloud region to: {region}")
    run_command(
        f"gcloud config set compute/region {region}"
    )

    print("gcloud project and region have been successfully set")
    return True

def main():
    # Load environment variables
    env_vars = load_env_to_dict()
    if not env_vars:
        print("No environment variables found in .env. Exiting.")
        return

    setup_gcloud(env_vars["PROJECT_ID"], env_vars["REGION"])

    # Assign and fix service account roles before deployment
    ensure_correct_roles(dry_run=False)

    # Generate env.yaml for Cloud Run
    generate_env_yaml(env_vars)

    # Build, push and deploy
    build_push_and_deploy(env_vars)

if __name__ == "__main__":
    main()
