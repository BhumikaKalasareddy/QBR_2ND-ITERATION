import google.auth
from google.cloud import bigquery
from app.core.config import settings

def get_bigquery_client() -> bigquery.Client:
    """Initializes BigQuery client using Application Default Credentials (ADC)."""
    credentials, project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return bigquery.Client(
        credentials=credentials,
        project=settings.GCP_PROJECT_ID or project_id
    )