#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="cuba-news"
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/adk-agent"
JOB_NAME="cuba-news-adk-job"

echo "Creating temporary cloudbuild.yaml..."
cat <<EOF > cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '$IMAGE_NAME', '-f', 'Dockerfile.adk', '.']
images: ['$IMAGE_NAME']
EOF

echo "Building and pushing Docker image..."
gcloud builds submit --config cloudbuild.yaml .
rm cloudbuild.yaml

echo "Creating/Updating Cloud Run Job..."
# Check if job exists
if gcloud run jobs describe $JOB_NAME --region $REGION > /dev/null 2>&1; then
    gcloud run jobs update $JOB_NAME \
        --image $IMAGE_NAME \
        --region $REGION \
        --set-env-vars="NON_INTERACTIVE=true,BCC_EMAILS=dania.g.y.56@gmail.com,GMAIL_USER=renier.perez@gmail.com" \
        --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest,GMAIL_PASSWORD=GMAIL_PASSWORD:latest"
else
    gcloud run jobs create $JOB_NAME \
        --image $IMAGE_NAME \
        --region $REGION \
        --set-env-vars="NON_INTERACTIVE=true,BCC_EMAILS=dania.g.y.56@gmail.com,GMAIL_USER=renier.perez@gmail.com" \
        --set-secrets="GOOGLE_API_KEY=GOOGLE_API_KEY:latest,GMAIL_PASSWORD=GMAIL_PASSWORD:latest"
fi

echo "Cloud Run Job $JOB_NAME created/updated."
echo "You can now create a Cloud Scheduler job to run this job daily."
