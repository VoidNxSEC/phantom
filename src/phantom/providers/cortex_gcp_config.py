"""
╔══════════════════════════════════════════════════════════════════╗
║  PHANTOM RAG - Google Cloud Platform Configuration Manager      ║
║  Handles credentials, project setup, and GCP client              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Google Cloud imports
try:
    from google.auth import default as get_default_credentials
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import aiplatform, bigquery, storage
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    print("⚠️  Google Cloud libraries not installed. Run: pip install google-cloud-aiplatform google-cloud-bigquery google-cloud-storage")


@dataclass
class GCPConfig:
    """Google Cloud Platform configuration"""
    project_id: str
    region: str
    credentials_path: Path | None = None

    # Vertex AI
    vertex_location: str = "us-central1"
    embedding_model: str = "textembedding-gecko@003"  # 768-dim, $0.025/1k chars

    # BigQuery
    bigquery_dataset: str = "phantom_rag"

    # Cloud Storage
    storage_bucket: str | None = None

    # Retry & Rate Limiting
    max_retries: int = 3
    retry_delay_seconds: int = 2
    max_requests_per_minute: int = 60


class GCPConfigManager:
    """Manages GCP configuration and credentials"""

    def __init__(self, config: GCPConfig | None = None):
        """
        Initialize GCP configuration manager

        Args:
            config: GCPConfig object. If None, loads from environment variables
        """
        if not GCP_AVAILABLE:
            raise ImportError(
                "Google Cloud libraries not available. "
                "Install with: pip install google-cloud-aiplatform google-cloud-bigquery google-cloud-storage"
            )

        self.config = config or self._load_from_env()
        self._validate_config()
        self._setup_credentials()

    def _load_from_env(self) -> GCPConfig:
        """Load configuration from environment variables"""

        # Required
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "GCP_PROJECT_ID environment variable not set. "
                "Run scripts/gcp_setup.sh or source ~/.config/phantom/gcp.env"
            )

        region = os.getenv("GCP_REGION", "us-central1")

        # Credentials
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            credentials_path = Path(credentials_path)

        # Optional overrides
        config = GCPConfig(
            project_id=project_id,
            region=region,
            credentials_path=credentials_path,
            vertex_location=os.getenv("VERTEX_AI_LOCATION", region),
            embedding_model=os.getenv("VERTEX_AI_EMBEDDING_MODEL", "textembedding-gecko@003"),
            bigquery_dataset=os.getenv("GCP_BIGQUERY_DATASET", "phantom_rag"),
            storage_bucket=os.getenv("GCP_STORAGE_BUCKET"),
        )

        return config

    def _validate_config(self):
        """Validate configuration"""

        if not self.config.project_id:
            raise ValueError("GCP project_id is required")

        if not self.config.region:
            raise ValueError("GCP region is required")

        # Check credentials file if provided
        if self.config.credentials_path:
            if not self.config.credentials_path.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {self.config.credentials_path}"
                )

            # Validate JSON
            try:
                with open(self.config.credentials_path) as f:
                    creds = json.load(f)
                    if "type" not in creds or creds["type"] != "service_account":
                        raise ValueError("Credentials file must be a service account JSON key")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid credentials JSON: {e}")

    def _setup_credentials(self):
        """Setup Google Cloud credentials"""

        # Set environment variable for all Google Cloud clients
        if self.config.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(self.config.credentials_path)

        # Test authentication
        try:
            credentials, project = get_default_credentials()
            print(f"✓ Authenticated with project: {project}")
        except DefaultCredentialsError as e:
            raise RuntimeError(
                f"Failed to authenticate with Google Cloud: {e}\n"
                "Make sure GOOGLE_APPLICATION_CREDENTIALS is set or you've run 'gcloud auth application-default login'"
            )

    def initialize_vertex_ai(self):
        """Initialize Vertex AI client"""

        aiplatform.init(
            project=self.config.project_id,
            location=self.config.vertex_location,
        )

        print(f"✓ Vertex AI initialized (project={self.config.project_id}, location={self.config.vertex_location})")

    def get_bigquery_client(self) -> bigquery.Client:
        """Get BigQuery client"""

        client = bigquery.Client(project=self.config.project_id)
        print(f"✓ BigQuery client created (project={self.config.project_id})")
        return client

    def get_storage_client(self) -> storage.Client:
        """Get Cloud Storage client"""

        client = storage.Client(project=self.config.project_id)
        print(f"✓ Cloud Storage client created (project={self.config.project_id})")
        return client

    def get_config_summary(self) -> dict[str, Any]:
        """Get configuration summary"""

        return {
            "project_id": self.config.project_id,
            "region": self.config.region,
            "vertex_location": self.config.vertex_location,
            "embedding_model": self.config.embedding_model,
            "bigquery_dataset": self.config.bigquery_dataset,
            "storage_bucket": self.config.storage_bucket,
            "credentials_path": str(self.config.credentials_path) if self.config.credentials_path else None,
        }


# ═══════════════════════════════════════════════════════════════════
# TESTING & VALIDATION
# ═══════════════════════════════════════════════════════════════════

def test_gcp_setup():
    """Test GCP configuration and connectivity"""

    print("🧪 Testing GCP Setup...")
    print("=" * 70)

    try:
        # Load config
        manager = GCPConfigManager()

        print("\n📋 Configuration:")
        for key, value in manager.get_config_summary().items():
            print(f"  • {key}: {value}")

        # Test Vertex AI
        print("\n🔮 Testing Vertex AI...")
        manager.initialize_vertex_ai()
        print("✓ Vertex AI connection successful")

        # Test BigQuery
        print("\n📊 Testing BigQuery...")
        bq_client = manager.get_bigquery_client()

        # List datasets
        datasets = list(bq_client.list_datasets())
        print(f"✓ BigQuery connection successful ({len(datasets)} datasets found)")

        # Check if phantom_rag dataset exists
        dataset_id = manager.config.bigquery_dataset
        try:
            bq_client.get_dataset(dataset_id)
            print(f"✓ Dataset '{dataset_id}' exists")
        except Exception:
            print(f"⚠️  Dataset '{dataset_id}' not found (will be created on first use)")

        # Test Cloud Storage
        print("\n📦 Testing Cloud Storage...")
        storage_client = manager.get_storage_client()

        # List buckets
        buckets = list(storage_client.list_buckets())
        print(f"✓ Cloud Storage connection successful ({len(buckets)} buckets found)")

        if manager.config.storage_bucket:
            try:
                bucket = storage_client.get_bucket(manager.config.storage_bucket)
                print(f"✓ Bucket '{manager.config.storage_bucket}' exists")
            except Exception:
                print(f"⚠️  Bucket '{manager.config.storage_bucket}' not found")

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED! GCP is configured correctly.")
        print("\nNext steps:")
        print("  1. Run: python3 cortex_vertex.py --test")
        print("  2. Start using Vertex AI embeddings in your pipeline!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you've run: scripts/gcp_setup.sh")
        print("  2. Source environment: source ~/.config/phantom/gcp.env")
        print("  3. Check credentials: echo $GOOGLE_APPLICATION_CREDENTIALS")
        return False

    return True


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        success = test_gcp_setup()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python3 cortex_gcp_config.py --test")
        print("\nOr use as a library:")
        print("  from cortex_gcp_config import GCPConfigManager")
        print("  manager = GCPConfigManager()")
