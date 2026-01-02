#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  PHANTOM RAG - Google Cloud Platform Setup                      ║
# ║  Configura projeto GCP, APIs, service account e credentials     ║
# ╚══════════════════════════════════════════════════════════════════╝

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-phantom-rag-prod}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_ACCOUNT_NAME="phantom-rag-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
CREDENTIALS_DIR="${HOME}/.config/gcp"
CREDENTIALS_FILE="${CREDENTIALS_DIR}/phantom-rag-key.json"

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    log_success "gcloud CLI found"
}

# ═══════════════════════════════════════════════════════════════════
# SETUP STEPS
# ═══════════════════════════════════════════════════════════════════

echo -e "${BLUE}"
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════╗
║      PHANTOM RAG - Google Cloud Platform Setup                  ║
║      Enterprise-Grade RAG Infrastructure                         ║
╚══════════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

log_info "Project ID: ${PROJECT_ID}"
log_info "Region: ${REGION}"
log_info "Service Account: ${SERVICE_ACCOUNT_EMAIL}"
echo ""

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Check gcloud installation
# ═══════════════════════════════════════════════════════════════════

log_info "Step 1: Checking gcloud CLI..."
check_gcloud

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Authenticate user
# ═══════════════════════════════════════════════════════════════════

log_info "Step 2: Authenticating with Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log_warning "No active authentication found. Running gcloud auth login..."
    gcloud auth login
fi
log_success "Authenticated"

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Create or select project
# ═══════════════════════════════════════════════════════════════════

log_info "Step 3: Setting up GCP project..."

if gcloud projects describe "${PROJECT_ID}" &>/dev/null; then
    log_success "Project '${PROJECT_ID}' already exists"
else
    log_warning "Project '${PROJECT_ID}' not found"
    read -p "Create new project? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud projects create "${PROJECT_ID}" --name="Phantom RAG Production"
        log_success "Project created"
    else
        log_error "Project creation cancelled. Exiting."
        exit 1
    fi
fi

gcloud config set project "${PROJECT_ID}"
log_success "Active project: ${PROJECT_ID}"

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Enable billing (manual verification)
# ═══════════════════════════════════════════════════════════════════

log_info "Step 4: Checking billing..."
if gcloud beta billing projects describe "${PROJECT_ID}" &>/dev/null; then
    BILLING_ACCOUNT=$(gcloud beta billing projects describe "${PROJECT_ID}" --format="value(billingAccountName)")
    if [ -n "${BILLING_ACCOUNT}" ]; then
        log_success "Billing enabled: ${BILLING_ACCOUNT}"
    else
        log_warning "Billing not enabled!"
        log_info "Enable billing at: https://console.cloud.google.com/billing/linkedaccount?project=${PROJECT_ID}"
        read -p "Press ENTER once billing is enabled..."
    fi
else
    log_warning "Cannot verify billing status. Please check manually."
    log_info "URL: https://console.cloud.google.com/billing/linkedaccount?project=${PROJECT_ID}"
    read -p "Press ENTER to continue..."
fi

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Enable required APIs
# ═══════════════════════════════════════════════════════════════════

log_info "Step 5: Enabling required GCP APIs..."

APIS=(
    "aiplatform.googleapis.com"       # Vertex AI
    "bigquery.googleapis.com"         # BigQuery
    "storage.googleapis.com"          # Cloud Storage
    "cloudresourcemanager.googleapis.com"
    "serviceusage.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "Enabling ${api}..."
    gcloud services enable "${api}" --project="${PROJECT_ID}"
done

log_success "All APIs enabled"

# ═══════════════════════════════════════════════════════════════════
# STEP 6: Create service account
# ═══════════════════════════════════════════════════════════════════

log_info "Step 6: Creating service account..."

if gcloud iam service-accounts describe "${SERVICE_ACCOUNT_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
    log_success "Service account '${SERVICE_ACCOUNT_NAME}' already exists"
else
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
        --display-name="Phantom RAG Service Account" \
        --description="Service account for Phantom RAG system (Vertex AI, BigQuery, GCS)" \
        --project="${PROJECT_ID}"
    log_success "Service account created"
fi

# ═══════════════════════════════════════════════════════════════════
# STEP 7: Grant IAM roles
# ═══════════════════════════════════════════════════════════════════

log_info "Step 7: Granting IAM permissions..."

ROLES=(
    "roles/aiplatform.user"          # Vertex AI access
    "roles/bigquery.admin"           # BigQuery full access
    "roles/storage.admin"            # Cloud Storage full access
)

for role in "${ROLES[@]}"; do
    log_info "Granting ${role}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
        --role="${role}" \
        --condition=None \
        >/dev/null
done

log_success "IAM roles granted"

# ═══════════════════════════════════════════════════════════════════
# STEP 8: Generate and download credentials
# ═══════════════════════════════════════════════════════════════════

log_info "Step 8: Generating service account credentials..."

mkdir -p "${CREDENTIALS_DIR}"

if [ -f "${CREDENTIALS_FILE}" ]; then
    log_warning "Credentials file already exists: ${CREDENTIALS_FILE}"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping credential generation"
    else
        gcloud iam service-accounts keys create "${CREDENTIALS_FILE}" \
            --iam-account="${SERVICE_ACCOUNT_EMAIL}" \
            --project="${PROJECT_ID}"
        log_success "New credentials generated"
    fi
else
    gcloud iam service-accounts keys create "${CREDENTIALS_FILE}" \
        --iam-account="${SERVICE_ACCOUNT_EMAIL}" \
        --project="${PROJECT_ID}"
    log_success "Credentials generated: ${CREDENTIALS_FILE}"
fi

chmod 600 "${CREDENTIALS_FILE}"

# ═══════════════════════════════════════════════════════════════════
# STEP 9: Create BigQuery dataset
# ═══════════════════════════════════════════════════════════════════

log_info "Step 9: Creating BigQuery dataset..."

DATASET_ID="phantom_rag"

if bq show --project_id="${PROJECT_ID}" "${DATASET_ID}" &>/dev/null; then
    log_success "BigQuery dataset '${DATASET_ID}' already exists"
else
    bq mk --project_id="${PROJECT_ID}" --location="${REGION}" --dataset "${DATASET_ID}"
    log_success "BigQuery dataset created: ${DATASET_ID}"
fi

# ═══════════════════════════════════════════════════════════════════
# STEP 10: Create Cloud Storage bucket
# ═══════════════════════════════════════════════════════════════════

log_info "Step 10: Creating Cloud Storage bucket..."

BUCKET_NAME="${PROJECT_ID}-documents"

if gsutil ls "gs://${BUCKET_NAME}" &>/dev/null; then
    log_success "Bucket 'gs://${BUCKET_NAME}' already exists"
else
    gsutil mb -p "${PROJECT_ID}" -l "${REGION}" "gs://${BUCKET_NAME}"
    log_success "Bucket created: gs://${BUCKET_NAME}"
fi

# ═══════════════════════════════════════════════════════════════════
# STEP 11: Export environment variables
# ═══════════════════════════════════════════════════════════════════

log_info "Step 11: Setting up environment variables..."

ENV_FILE="${HOME}/.config/phantom/gcp.env"
mkdir -p "$(dirname "${ENV_FILE}")"

cat > "${ENV_FILE}" << EOF
# PHANTOM RAG - Google Cloud Platform Configuration
# Generated: $(date -Iseconds)

export GCP_PROJECT_ID="${PROJECT_ID}"
export GCP_REGION="${REGION}"
export GOOGLE_APPLICATION_CREDENTIALS="${CREDENTIALS_FILE}"
export GCP_BIGQUERY_DATASET="${DATASET_ID}"
export GCP_STORAGE_BUCKET="${BUCKET_NAME}"

# Vertex AI Endpoints
export VERTEX_AI_LOCATION="${REGION}"
export VERTEX_AI_EMBEDDING_MODEL="textembedding-gecko@003"

# Optional: Enable detailed logging
# export GOOGLE_CLOUD_LOG_LEVEL="DEBUG"
EOF

log_success "Environment file created: ${ENV_FILE}"

# ═══════════════════════════════════════════════════════════════════
# FINAL OUTPUT
# ═══════════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ GCP SETUP COMPLETE!                                           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

log_info "Configuration Summary:"
echo "  • Project ID:       ${PROJECT_ID}"
echo "  • Region:           ${REGION}"
echo "  • Service Account:  ${SERVICE_ACCOUNT_EMAIL}"
echo "  • Credentials:      ${CREDENTIALS_FILE}"
echo "  • BigQuery Dataset: ${DATASET_ID}"
echo "  • Storage Bucket:   gs://${BUCKET_NAME}"
echo ""

log_info "Next Steps:"
echo "  1. Source environment variables:"
echo "     ${YELLOW}source ${ENV_FILE}${NC}"
echo ""
echo "  2. Verify setup:"
echo "     ${YELLOW}python3 cortex_vertex.py --test${NC}"
echo ""
echo "  3. Start using Vertex AI embeddings in CORTEX v2.0!"
echo ""

log_success "You can now use your Google Cloud credits for enterprise RAG! 🚀"
