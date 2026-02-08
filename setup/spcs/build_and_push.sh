#!/bin/bash
#=============================================================================
# VIGIL Risk Planning - Build and Push Script
#=============================================================================
# Builds Docker images and pushes to Snowflake Image Repository
#
# Prerequisites:
# 1. Docker installed and running
# 2. Snowflake CLI (snow) installed and configured
# 3. Run 06_spcs_deployment.sql first to create image repository
#=============================================================================

set -e

# Configuration
ACCOUNT="${SNOWFLAKE_ACCOUNT:-your-account}"
ORG="${SNOWFLAKE_ORG:-your-org}"
DATABASE="RISK_PLANNING_DB"
SCHEMA="SPCS"
REPO="APP_REPO"
VERSION="${1:-latest}"

# Construct repository URL
REPO_URL="${ORG}-${ACCOUNT}.registry.snowflakecomputing.com/${DATABASE,,}/${SCHEMA,,}/${REPO,,}"

echo "=============================================="
echo "VIGIL Risk Planning - Docker Build & Push"
echo "=============================================="
echo "Repository: ${REPO_URL}"
echo "Version: ${VERSION}"
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../.."
cd "${PROJECT_ROOT}"

echo "[1/5] Logging in to Snowflake registry..."
# Use Snowflake CLI to get registry token
snow spcs image-registry login

echo "[2/5] Building backend image..."
docker build \
    -f setup/spcs/Dockerfile.backend \
    -t vigil-backend:${VERSION} \
    -t ${REPO_URL}/vigil-backend:${VERSION} \
    .

echo "[3/5] Building frontend image..."
docker build \
    -f setup/spcs/Dockerfile.frontend \
    -t vigil-frontend:${VERSION} \
    -t ${REPO_URL}/vigil-frontend:${VERSION} \
    .

echo "[4/5] Pushing backend image..."
docker push ${REPO_URL}/vigil-backend:${VERSION}

echo "[5/5] Pushing frontend image..."
docker push ${REPO_URL}/vigil-frontend:${VERSION}

echo ""
echo "=============================================="
echo "Build and push complete!"
echo "=============================================="
echo ""
echo "Images pushed:"
echo "  - ${REPO_URL}/vigil-backend:${VERSION}"
echo "  - ${REPO_URL}/vigil-frontend:${VERSION}"
echo ""
echo "Next steps:"
echo "  1. Upload spec.yaml: PUT file://setup/spcs/spec.yaml @${DATABASE}.${SCHEMA}.APP_STAGE"
echo "  2. Create/update service in Snowflake"
echo "  3. Run: SHOW ENDPOINTS IN SERVICE ${SCHEMA}.VIGIL_SERVICE"
echo ""
