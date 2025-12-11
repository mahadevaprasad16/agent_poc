Agentic AI POC

Gemini + ServiceNow Agentic AI POC

This project demonstrates a real-time Agentic AI application built using Streamlit, LangGraph, and the Gemini API, securely connecting to a ServiceNow instance via its REST API to fetch and summarize incident data. The application is designed for robust, automated deployment using Google Cloud Build and Cloud Run.

Architecture Overview
Streamlit -> Frontend UI for the chat interface.
Gemini 2.5 Flash -> The Large Language Model (LLM) for reasoning and summarization.
LangGraph -> Orchestrates the tool-calling logic (ReAct pattern) and manages the multi-step conversation.
ServiceNow API - Provides real-time incident data via the Table API (/api/now/table/incident).
Cloud Build -> CI/CD pipeline manager (builds Docker image, pushes to AR, triggers deployment).
Cloud Run -> Serverless hosting for the containerized Streamlit application.
Artifact Registry -> Secure, versioned storage for the Docker image.

Prerequisites

Software
Python (3.9+)
Docker
Google Cloud CLI (gcloud)
Git

Accounts & Credentials

Google Cloud Platform (GCP) Project: Billing enabled, and necessary APIs enabled (listed below).
Gemini API Key: Required for the LLM (GEMINI_API_KEY).
ServiceNow Developer Instance: Required credentials for API access:
Instance URL (e.g., devXXXXX.service-now.com)

📂 Project Files

agent_poc.py -> The main Streamlit application code, containing the LangGraph agent setup and the get_servicenow_incidents tool.
Dockerfile -> Defines the container image for running the Streamlit app on Cloud Run.
requirements.txt -> Python dependencies (LangChain, LangGraph, Streamlit, requests).
cloudbuild.yaml -> The CI/CD pipeline definition for Google Cloud Build.
.env -> (Optional) File for local testing of environment variables.

1. Local Development Setup
To test the application locally before deploying:
Clone the Repository:
git clone https://github.com/mahadevaprasad16/agent_poc.git
cd [repo-name]
Install Dependencies:
pip install -r requirements.txt
Set Environment Variables:
Create a file named .env in the root directory:
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
SN_INSTANCE="devXXXXX.service-now.com"
SN_USERNAME="admin"
SN_PASSWORD="yourpassword"

Run the Application:
The agent_poc.py loads variables from the .env file using dotenv.
streamlit run agent_poc.py
The application will start, typically at http://localhost:8501.

2. Google Cloud Platform CI/CD Deployment

This section walks through the steps to automate the build and deployment process using the provided cloudbuild.yaml.

2.1. Initial GCP Configuration

Set Project and Region:

# IMPORTANT: Replace YOUR_PROJECT_ID with your actual project ID
export PROJECT_ID="YOUR_PROJECT_ID"
gcloud config set project $PROJECT_ID
export REGION="us-central1" # Consistent with cloudbuild.yaml
export AR_REPO_NAME="agentic-ai-poc"
export SERVICE_NAME="agentic-ai"

Enable Required APIs:

gcloud services enable \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    run.googleapis.com

Create Artifact Registry Repository:
Artifact Registry requires the repository to exist before the build can push an image.

gcloud artifacts repositories create $AR_REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for $SERVICE_NAME"

2.2. Manual Initial Deployment (Crucial for Secrets)

Before setting up the CI/CD trigger, you must run the deployment once to create the Cloud Run service and securely configure all the environment secrets. Subsequent automatic deployments will inherit these secrets.

Build and Push the Image Locally (for the first deployment):

docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO_NAME/$SERVICE_NAME:latest .
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO_NAME/$SERVICE_NAME:latest


Deploy the Service and Set Secrets:
Use this command ONCE to initialize the service and its secrets. Replace the placeholder values with your real credentials.

gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO_NAME/$SERVICE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8501 \
  --set-env-vars \
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY",\
    SN_INSTANCE="devXXXXX.service-now.com",\
    SN_USERNAME="admin",\
    SN_PASSWORD="YOUR_SN_PASSWORD"


2.3. Set up the Cloud Build Trigger
Connect Repository:
In the GCP Console, navigate to Cloud Build -> Triggers.
Click Create trigger.
Connect to your preferred source (GitHub, GitLab, etc.).
Configure Trigger:
Name: ci-cd-agentic-ai
Event: Push to a branch
Branch: ^main$ (or your main branch)
Build Configuration: Cloud Build configuration file (yaml or json)
Cloud Build file: cloudbuild.yaml
Substitution Variables (Required): You must define the following two variables, which the cloudbuild.yaml uses:
_REGION: us-central1
_AR_REPO_NAME: agentic-ai-poc

Run Build:
Test the trigger by pushing a small change or by clicking Run on the trigger page. The pipeline will now automatically build, tag, and deploy your code changes to the existing Cloud Run service.

3. Usage Examples

Once deployed, access the Cloud Run URL and interact with the agent:

"Show me the New incidents."

"Are there any active tickets right now?"

"Summarize the Resolved incidents from the past week."

