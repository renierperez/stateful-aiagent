# GCP Architect Guide: ADK News Agent Deployment

This guide provides detailed instructions for a Google Cloud Architect to deploy and manage the ADK-based News Agent.

## Architecture Overview

The agent uses a **Brain-Memory-Action** architecture, refactored with the Google Agent Development Kit (ADK) for improved modularity.

-   **Brain:** Vertex AI (Gemini 2.5 Pro) with Google Search Grounding.
-   **Memory:** Cloud Firestore (Native Mode) with Vector Search.
-   **Action:** Cloud Run Jobs (Serverless, scheduled).
-   **Security:** Secret Manager.

## Deployment Steps

### 1. Prerequisites & API Enablement

Ensure the following APIs are enabled in the Google Cloud Project:

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    firestore.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com
```

### 2. Firestore Setup

Initialize Firestore in Native mode and create the vector index required for semantic deduplication.

```bash
# Create Vector Index
gcloud firestore indexes composite create \
    --collection-group=news_agent_memory_topics \
    --query-scope=COLLECTION \
    --field-config=vector-config='{"dimension":"768","flat": "{}"}',field-path=embedding
```

### 3. Secret Management

Store sensitive credentials in Secret Manager.

```bash
# 1. Google API Key (for ADK/Vertex AI)
echo -n "YOUR_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# 2. Gmail App Password
echo -n "YOUR_GMAIL_APP_PASSWORD" | gcloud secrets create GMAIL_PASSWORD --data-file=-

# Grant Access to Cloud Run Service Account
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GOOGLE_API_KEY --member="serviceAccount:${SERVICE_ACCOUNT}" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding GMAIL_PASSWORD --member="serviceAccount:${SERVICE_ACCOUNT}" --role="roles/secretmanager.secretAccessor"
```

### 4. Agent Deployment (ADK)

Use the provided deployment script to build and deploy the ADK agent.

```bash
# Configure variables in deploy_adk.sh if needed, then run:
chmod +x deploy_adk.sh
./deploy_adk.sh
```

The script performs the following:
1.  Builds the Docker image using Cloud Build.
2.  Pushes the image to Artifact Registry.
3.  Creates/Updates the Cloud Run Job `cuba-news-adk-job` with correct environment variables and secret mappings.

### 5. Scheduling

Schedule the agent to run daily.

```bash
gcloud scheduler jobs create http cuba-news-adk-scheduler \
    --location=us-central1 \
    --schedule="0 8 * * *" \
    --time-zone="America/Santiago" \
    --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/cuba-news-adk-job:run" \
    --http-method=POST \
    --oauth-service-account-email=${SERVICE_ACCOUNT}
```

## Monitoring & Maintenance

-   **Logs:** View execution logs in Cloud Logging under the resource `Cloud Run Job: cuba-news-adk-job`.
-   **Firestore:** Monitor the `news_agent_memory` and `news_agent_memory_topics` collections.
-   **Secrets:** Rotate `GMAIL_PASSWORD` or `GOOGLE_API_KEY` by adding new versions to Secret Manager; Cloud Run will automatically use the `latest` version on next execution.
