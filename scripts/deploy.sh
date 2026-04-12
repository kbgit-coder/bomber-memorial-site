#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Bomber Memorial Site — Deploy Script
# Usage: ./scripts/deploy.sh staging|production
#
# Deploys via FTP (lftp mirror) using domain-scoped FTP accounts.
# Requires a .env.deploy file in the repo root (gitignored) with:
#   FTP_HOST=django.ukhosted.net
#   FTP_PROD_USER=<user@domain>
#   FTP_PROD_PASS=<password>
#   FTP_STAGING_USER=<user@staging.domain>
#   FTP_STAGING_PASS=<password>
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

# --- Check lftp --------------------------------------------------------------
command -v lftp >/dev/null 2>&1 || die "lftp not installed — run: apt-get install -y lftp"

# --- Load credentials --------------------------------------------------------
ENV_FILE="$REPO_ROOT/.env.deploy"
if [[ -f "$ENV_FILE" ]]; then
  info "Loading credentials from .env.deploy"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

: "${FTP_HOST:?FTP_HOST not set — add to .env.deploy}"
: "${FTP_USER:?FTP_USER not set}"
: "${FTP_PASS:?FTP_PASS not set}"

if [[ "$TARGET" == "staging" ]]; then
  FTP_PATH="${FTP_STAGING_PATH:-staging.bombermemorial.co.uk/}"
  SITE_URL="https://staging.bombermemorial.co.uk"
else
  FTP_PATH="${FTP_PROD_PATH:-public_html/bombermemorial.co.uk/}"
  SITE_URL="https://bombermemorial.co.uk"
fi

info "Target:   $TARGET"
info "FTP user: $FTP_USER"
info "FTP path: $FTP_PATH"
info "Site URL: $SITE_URL"
echo ""

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

# --- Step 1b: Section relevancy quality gate ---------------------------------
RELEVANCY="$REPO_ROOT/scripts/section-relevancy-scorer.py"
if [[ -f "$RELEVANCY" ]]; then
  info "Running section relevancy scorer..."
  python3 "$RELEVANCY"
  # Run again in dry-run to check if anything was missed
  REMAINING=$(python3 "$RELEVANCY" --dry-run 2>&1 | grep "Files modified:" | awk '{print $NF}')
  if [[ "$REMAINING" != "0" ]]; then
    die "Section relevancy scorer is not idempotent — $REMAINING files still need fixing."
  fi
  success "Section relevancy gate passed (idempotent)."
fi

# --- Step 1c: Crew data quality gate -----------------------------------------
CREW_CLEANUP="$REPO_ROOT/scripts/crew-data-cleanup.py"
if [[ -f "$CREW_CLEANUP" ]]; then
  info "Running crew data cleanup..."
  python3 "$CREW_CLEANUP"
  REMAINING=$(python3 "$CREW_CLEANUP" --dry-run 2>&1 | grep "Files modified:" | awk '{print $NF}')
  if [[ "$REMAINING" != "0" ]]; then
    die "Crew data cleanup is not idempotent — $REMAINING files still need fixing."
  fi
  success "Crew data quality gate passed."
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

# Fix directory index pages — Apache serves 403 for directories without index.html
for section_page in "$REPO_ROOT"/out/*.html; do
  section_name=$(basename "$section_page" .html)
  section_dir="$REPO_ROOT/out/$section_name"
  if [[ -d "$section_dir" && ! -f "$section_dir/index.html" ]]; then
    cp "$section_page" "$section_dir/index.html"
    success "Copied $section_name.html → $section_name/index.html"
  fi
done

if [[ -f "$REPO_ROOT/public/sitemap.xml" ]]; then
  cp "$REPO_ROOT/public/sitemap.xml" "$REPO_ROOT/out/sitemap.xml"
  success "Copied sitemap.xml"
fi

# Staging: inject .htpasswd protection
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

# --- Step 4: FTP mirror to server -------------------------------------------
info "Deploying via FTP mirror to $TARGET..."
info "This uploads only changed files (differential sync)."
echo ""

lftp -c "
  set ssl:verify-certificate no;
  set net:max-retries 3;
  set net:reconnect-interval-base 5;
  open -u '$FTP_USER','$FTP_PASS' ftp://$FTP_HOST;
  mirror --reverse --delete --verbose --parallel=4 --exclude .htpasswd $REPO_ROOT/out/ $FTP_PATH;
  quit;
"

success "FTP deploy complete."
echo ""

# --- Step 5: Production git tag ----------------------------------------------
if [[ "$TARGET" == "production" ]]; then
  info "Production deploy succeeded."
  echo ""
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
