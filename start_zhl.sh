#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
#                 RUNTIME SETTINGS & ENVIRONMENT VARIABLES
# ==============================================================================

# --- Core Settings ---
MODULE="${MODULE:-cs336_basics.train_bpe}"
LOG_DIR="${LOG_DIR:-cs336_basics/outputs}"

# --- Environment Context ---
# Set RUN_CONTEXT to "AZURE" in your Container App Job environment to use cloud-native features
RUN_CONTEXT="${RUN_CONTEXT:-LOCAL}"

# --- Local Development Tools (used when RUN_CONTEXT is "LOCAL") ---
OUTPUT_SAS_URL="${OUTPUT_SAS_URL:-}"           # SAS URL for uploading artifacts from local
NTFY_TOPIC="${NTFY_TOPIC:-}"                   # ntfy.sh topic for simple local notifications

# --- Azure Cloud Tools (used when RUN_CONTEXT is "AZURE") ---
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-}"         # Storage account name for MSI-based uploads
ARTIFACTS_CONTAINER="${ARTIFACTS_CONTAINER:-bpe-artifacts}" # Target container for artifacts
AZURE_MONITOR_WEBHOOK="${AZURE_MONITOR_WEBHOOK:-}" # Webhook URL for an Azure Logic App/Action Group

# ==============================================================================
#                          HELPER FUNCTIONS
# ==============================================================================

# --- Notification Helper ---
# Sends a notification based on the execution context.
notify() {
  local msg="$1"
  local title="$2"
  
  if [[ "$RUN_CONTEXT" == "AZURE" ]]; then
    [[ -z "${AZURE_MONITOR_WEBHOOK}" ]] && return 0
    # Example payload for a Logic App or webhook
    local payload
    payload=$(printf '{"title": "%s", "message": "%s"}' "$title" "$msg")
    curl -fsS -X POST -H "Content-Type: application/json" -d "$payload" "$AZURE_MONITOR_WEBHOOK" >/dev/null || true
  else
    [[ -z "${NTFY_TOPIC}" ]] && return 0
    curl -fsS -H "Title: $title" -d "$msg" "https://ntfy.sh/${NTFY_TOPIC}" >/dev/null || true
  fi
}

# --- Artifact Upload Helper ---
# Uploads logs and metadata to Azure Storage.
upload_outputs() {
  local run_id="$1"
  [[ -n "${AZCOPY_MISSING:-}" ]] && { echo "WARN: azcopy unavailable; skipping upload"; return 0; }

  local dest_url=""
  if [[ "$RUN_CONTEXT" == "AZURE" ]]; then
    [[ -z "${STORAGE_ACCOUNT}" ]] && { echo "INFO: STORAGE_ACCOUNT not set for Azure context; skipping upload."; return 0; }
    echo "==> Authenticating azcopy with Managed Identity..."
    export AZCOPY_AUTO_LOGIN_TYPE="MSI"
    local azcopy_args=(--identity)
    if [[ -n "${AZCOPY_MSI_CLIENT_ID:-}" ]]; then
      azcopy_args+=(--identity-client-id "${AZCOPY_MSI_CLIENT_ID}")
    fi
    # export AZCOPY_DISABLE_KEYRING=1
    export AZCOPY_DISABLE_PERSISTENT_CONFIG=TRUE
    azcopy login "${azcopy_args[@]}" || { echo "ERROR: MSI login failed."; return 1; }
    dest_url="https://${STORAGE_ACCOUNT}.blob.core.windows.net/${ARTIFACTS_CONTAINER}/${run_id}/"
    echo "==> Uploading outputs to ${dest_url} via MI..."
  else
    [[ -z "${OUTPUT_SAS_URL}" ]] && { echo "INFO: OUTPUT_SAS_URL not set for local context; skipping upload."; return 0; }
    dest_url="$OUTPUT_SAS_URL"
    echo "==> Uploading outputs to Blob container via SAS URL..."
  fi
  
  azcopy copy "${LOG_DIR}/*" "${dest_url}" --recursive >/dev/null
  echo "==> Upload complete."
}

# ==============================================================================
#                             MAIN EXECUTION
# ==============================================================================

# --- Setup ---
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$(date -u +%Y%m%dT%H%M%SZ).log"
START_TS=$(date +%s)
RUN_TS_UTC=$(date -u +%Y%m%dT%H%M%SZ)
RUN_ID="${RUN_TS_UTC}-${IMAGE_TAG:-unknown}"

command -v uv >/dev/null 2>&1 || { echo "ERROR: uv not found"; exit 127; }
command -v azcopy >/dev/null 2>&1 || { echo "WARN: azcopy not found; uploads will be skipped"; AZCOPY_MISSING=1; }

echo "==> Starting Job in ${RUN_CONTEXT} mode."
echo "==> Logging to ${LOG_FILE}"

# --- Dependency Sync ---
echo "==> Syncing Python dependencies..."
uv sync --frozen

# --- Run the Python Module ---
echo "==> Running module: $MODULE"
set +e # Disable exit on error to capture the status code
uv run python -m "$MODULE" 2>&1 | tee -a "$LOG_FILE"
STATUS=${PIPESTATUS[0]} # Capture the exit code of the Python script
set -e # Re-enable exit on error
echo "==> Module finished with exit code: $STATUS"

# --- Post-Run Tasks ---
END_TS=$(date +%s)
DUR=$(( END_TS - START_TS ))
H=$(( DUR/3600 )); M=$(( (DUR%3600)/60 )); S=$(( DUR%60 ))
DURATION_STR="${H}h ${M}m ${S}s"

# --- Write Run Metadata ---
META_FILE="${LOG_DIR}/run_metadata.json"
echo "==> Writing metadata to ${META_FILE}"
CPU_COUNT=$( (command -v nproc >/dev/null && nproc) || getconf _NPROCESSORS_ONLN )
CG_MEM_MAX=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo "unknown")

{
  echo "{";
  echo "  \"run_id\": \"${RUN_ID}\",";
  echo "  \"image_tag\": \"${IMAGE_TAG:-unknown}\",";
  echo "  \"status\": ${STATUS},";
  echo "  \"start_ts_utc\": \"${RUN_TS_UTC}\",";
  echo "  \"duration_seconds\": ${DUR},";
  echo "  \"duration_str\": \"${DURATION_STR}\",";
  echo "  \"cpu_count\": \"${CPU_COUNT}\",";
  echo "  \"cgroup_memory_max\": \"${CG_MEM_MAX}\"";
  echo "}";
} > "$META_FILE"

# --- Upload Artifacts & Send Notifications ---
upload_outputs "$RUN_ID" || echo "WARN: Upload failed."

if [[ $STATUS -eq 0 ]]; then
  notify "✅ Success on $(hostname) | ${DURATION_STR}" "BPE Job Success"
else
  notify "❌ FAILED (exit $STATUS) on $(hostname) | ${DURATION_STR}" "BPE Job Failed"
fi

exit $STATUS
