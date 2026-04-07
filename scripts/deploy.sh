#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Bomber Memorial Site — Deploy Script
# Usage: ./scripts/deploy.sh staging|production
# =============================================================================
#
# Requires a .env.deploy file in the repo root (gitignored) with:
#   CPANEL_HOST=django.ukhosted.net
#   CPANEL_PORT=2083
#   CPANEL_USER=kbwellbe
#   CPANEL_API_TOKEN_NAME=HollyDomainManager
#   CPANEL_API_TOKEN=<token>
#
# Or export those variables in your shell before running.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Colours -----------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()     { error "$*"; exit 1; }

# --- Argument ----------------------------------------------------------------
TARGET="${1:-}"
if [[ "$TARGET" != "staging" && "$TARGET" != "production" ]]; then
  die "Usage: $0 staging|production"
fi

# --- Load credentials --------------------------------------------------------
ENV_FILE="$REPO_ROOT/.env.deploy"
if [[ -f "$ENV_FILE" ]]; then
  info "Loading credentials from .env.deploy"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

# Validate required env vars are set
: "${CPANEL_HOST:?CPANEL_HOST not set — add to .env.deploy or environment}"
: "${CPANEL_PORT:?CPANEL_PORT not set}"
: "${CPANEL_USER:?CPANEL_USER not set}"
: "${CPANEL_API_TOKEN_NAME:?CPANEL_API_TOKEN_NAME not set}"
: "${CPANEL_API_TOKEN:?CPANEL_API_TOKEN not set}"

CPANEL_BASE_URL="https://${CPANEL_HOST}:${CPANEL_PORT}"
# Auth constructed in API helper section below

# --- Deploy targets ----------------------------------------------------------
STAGING_DIR="/home/kbwellbe/staging.bombermemorial.co.uk"
PRODUCTION_DIR="/home/kbwellbe/public_html/bombermemorial.co.uk"

if [[ "$TARGET" == "staging" ]]; then
  DOCUMENT_ROOT="$STAGING_DIR"
  SITE_URL="https://staging.bombermemorial.co.uk"
else
  DOCUMENT_ROOT="$PRODUCTION_DIR"
  SITE_URL="https://bombermemorial.co.uk"
fi

TARBALL="bomber-memorial-deploy.tar.gz"

info "Target:        $TARGET"
info "Document root: $DOCUMENT_ROOT"
info "Site URL:      $SITE_URL"
echo ""

# --- Production confirmation -------------------------------------------------
if [[ "$TARGET" == "production" ]]; then
  warn "You are about to deploy to PRODUCTION."
  warn "This will update $SITE_URL for all visitors."
  echo ""
  read -r -p "Type 'yes' to confirm: " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    die "Deployment cancelled."
  fi
  echo ""
fi

# --- Step 1: Validate memorials ----------------------------------------------
VALIDATOR="$REPO_ROOT/scripts/validate-memorials.js"
if [[ -f "$VALIDATOR" ]]; then
  info "Running JSON Schema validator..."
  if ! node "$VALIDATOR"; then
    die "Validation failed — fix memorial data before deploying."
  fi
  success "Validation passed."
else
  warn "validate-memorials.js not found — skipping validation."
fi
echo ""

# --- Step 2: Build -----------------------------------------------------------
info "Running npm run build..."
cd "$REPO_ROOT"
if ! npm run build; then
  die "Build failed — fix errors before deploying."
fi
success "Build complete."
echo ""

# --- Step 3: Prepare out/ directory ------------------------------------------
info "Copying static assets into out/..."

if [[ -f "$REPO_ROOT/public/.htaccess" ]]; then
  cp "$REPO_ROOT/public/.htaccess" "$REPO_ROOT/out/.htaccess"
  success "Copied .htaccess"
fi

if [[ -f "$REPO_ROOT/public/robots.txt" ]]; then
  cp "$REPO_ROOT/public/robots.txt" "$REPO_ROOT/out/robots.txt"
  success "Copied robots.txt"
fi

if [[ -f "$REPO_ROOT/public/sitemap.xml" ]]; then
  cp "$REPO_ROOT/public/sitemap.xml" "$REPO_ROOT/out/sitemap.xml"
  success "Copied sitemap.xml"
fi

# Staging: inject .htpasswd protection (user: keith, pass: bmr-staging-2026)
if [[ "$TARGET" == "staging" ]]; then
  info "Adding .htpasswd protection for staging..."
  cat >> "$REPO_ROOT/out/.htaccess" << 'HTPASSWD'

# Staging password protection
AuthType Basic
AuthName "Bomber Memorial Staging"
AuthUserFile /home/kbwellbe/staging.bombermemorial.co.uk/.htpasswd
Require valid-user
HTPASSWD
  success ".htpasswd auth block added to .htaccess"
fi

echo ""

# --- Step 4: Create tarball --------------------------------------------------
# Tar the contents of out/ directly so they extract into the document root
# (not into an out/ subdirectory on the server)
info "Creating tarball..."
cd "$REPO_ROOT/out"
tar czf "$REPO_ROOT/$TARBALL" .
cd "$REPO_ROOT"
success "Created ${TARBALL} ($(du -sh "$TARBALL" | cut -f1))"
echo ""

# --- cPanel API v2 helper ----------------------------------------------------
# Uses cPanel API v2 (not UAPI) — confirmed working with HollyDomainManager token
# Rate limit: minimum 5 seconds between calls
CPANEL_API_V2="${CPANEL_BASE_URL}/json-api/cpanel?cpanel_jsonapi_version=2"
CPANEL_AUTH_HEADER="cpanel ${CPANEL_USER}:${CPANEL_API_TOKEN}"

check_api_response() {
  local response="$1"
  local label="$2"
  local result
  result=$(echo "$response" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    r = d.get('cpanelresult', {})
    if r.get('event', {}).get('result') == 1:
        print('OK')
    else:
        print(r.get('error', 'unknown error'))
except:
    print('parse error')
" 2>/dev/null)
  if [[ "$result" == "OK" ]]; then
    success "$label"
    return 0
  else
    error "$label failed: $result"
    return 1
  fi
}

url_encode() {
  python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

# --- Step 5: Upload tarball to cPanel ----------------------------------------
info "Uploading tarball to cPanel (${CPANEL_HOST})..."

UPLOAD_RESPONSE=$(curl -s -k \
  -H "Authorization: ${CPANEL_AUTH_HEADER}" \
  -F "dir=${DOCUMENT_ROOT}" \
  -F "file-1=@${REPO_ROOT}/${TARBALL}" \
  "${CPANEL_API_V2}&cpanel_jsonapi_module=Fileman&cpanel_jsonapi_func=uploadfiles")

check_api_response "$UPLOAD_RESPONSE" "Upload complete" || die "Upload failed — aborting."

info "Waiting 5 seconds (cPanel rate limit)..."
sleep 5

# --- Step 6: Extract on server -----------------------------------------------
info "Extracting tarball to ${DOCUMENT_ROOT}..."

ENCODED_SOURCE=$(url_encode "${DOCUMENT_ROOT}/${TARBALL}")
ENCODED_DEST=$(url_encode "${DOCUMENT_ROOT}")

EXTRACT_RESPONSE=$(curl -s -k \
  -H "Authorization: ${CPANEL_AUTH_HEADER}" \
  "${CPANEL_API_V2}&cpanel_jsonapi_module=Fileman&cpanel_jsonapi_func=fileop&op=extract&sourcefiles=${ENCODED_SOURCE}&destfiles=${ENCODED_DEST}")

check_api_response "$EXTRACT_RESPONSE" "Extraction complete" || die "Extraction failed — aborting."

info "Waiting 5 seconds (cPanel rate limit)..."
sleep 5

# --- Step 7: Remove tarball from server --------------------------------------
info "Removing tarball from server..."

ENCODED_TARBALL=$(url_encode "${DOCUMENT_ROOT}/${TARBALL}")

DELETE_RESPONSE=$(curl -s -k \
  -H "Authorization: ${CPANEL_AUTH_HEADER}" \
  "${CPANEL_API_V2}&cpanel_jsonapi_module=Fileman&cpanel_jsonapi_func=fileop&op=unlink&sourcefiles=${ENCODED_TARBALL}")

check_api_response "$DELETE_RESPONSE" "Server tarball removed" \
  || warn "Could not remove server tarball (non-fatal) — delete it manually."

# --- Clean up local tarball --------------------------------------------------
rm -f "$REPO_ROOT/$TARBALL"
success "Local tarball removed."
echo ""

# --- Step 8: Production git tag ----------------------------------------------
if [[ "$TARGET" == "production" ]]; then
  info "Production deploy succeeded."
  read -r -p "Create a git release tag? Enter version (e.g. v1.2.0) or press Enter to skip: " VERSION

  if [[ -n "$VERSION" ]]; then
    cd "$REPO_ROOT"
    git tag -a "$VERSION" -m "Release ${VERSION} — deployed to production $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git push origin "$VERSION"
    success "Tagged and pushed: $VERSION"
  else
    info "Skipped git tag."
  fi
fi

# --- Done --------------------------------------------------------------------
echo ""
success "============================================"
success "Deployed to: $SITE_URL"
success "============================================"
echo ""
