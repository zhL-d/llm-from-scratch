#!/usr/bin/env bash
set -euo pipefail

# ====== RUNTIME SETTINGS (Docker) ======
MODULE="${MODULE:-cs336_basics.train_bpe}"     # python -m <module>
LOG_DIR="${LOG_DIR:-cs336_basics/outputs}"     # where logs + health live
OUTPUT_SAS_URL="${OUTPUT_SAS_URL:-}"           # blob container SAS (optional)
NTFY_TOPIC="${NTFY_TOPIC:-}"                   # e.g. bpe-xxxx (optional)
# =======================================

# --- sanity checks (container should already have these installed) ---
command -v uv >/dev/null 2>&1      || { echo "ERROR: uv not found (image must include uv)"; exit 127; }
command -v azcopy >/dev/null 2>&1  || { echo "WARN: azcopy not found; uploads will be skipped"; AZCOPY_MISSING=1 || true; }

# --- prep output paths ---
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/run_$(date -u +%Y%m%dT%H%M%SZ).log"
NOTIFY_FILE="$LOG_DIR/notify_url.txt"

# --- show & persist notification target ---
if [[ -n "${NTFY_TOPIC}" ]]; then
  NOTIFY_URL="https://ntfy.sh/${NTFY_TOPIC}"
  echo "==> Notifications will be sent to:"
  echo "    ${NOTIFY_URL}"
  echo "${NOTIFY_URL}" > "${NOTIFY_FILE}"
else
  echo "==> Notifications disabled (set NTFY_TOPIC to enable)."
  echo "(notifications disabled)" > "${NOTIFY_FILE}"
fi
echo

# --- tiny notifier helper (optional) ---
notify() {
  local msg="$1"
  [[ -z "${NTFY_TOPIC}" ]] && return 0
  curl -fsS -d "$msg" "https://ntfy.sh/${NTFY_TOPIC}" >/dev/null || true
}

# --- upload helper (optional) ---
upload_outputs() {
  [[ -z "${OUTPUT_SAS_URL}" ]] && { echo "INFO: OUTPUT_SAS_URL not set; skipping upload"; return 0; }
  [[ -n "${AZCOPY_MISSING:-}" ]] && { echo "WARN: azcopy unavailable; skipping upload"; return 0; }
  echo "==> Uploading ${LOG_DIR}/* to Blob..."
  azcopy copy "${LOG_DIR}/*" "${OUTPUT_SAS_URL}" --recursive >/dev/null
  echo "==> Upload complete."
}

# --- run job ---
START_TS=$(date +%s)
set +e
# Keep deps in sync with lockfile; idempotent in container
uv sync --frozen
uv run python -m "$MODULE" 2>&1 | tee -a "$LOG_FILE"

# venv already active via PATH -> just use python
# ensure project is importable + provides package metadata
# python -m pip install -q -e .   # editable install from /app into /opt/venv

# python -m "$MODULE" 2>&1 | tee -a "$LOG_FILE"

STATUS=${PIPESTATUS[0]}
set -e
END_TS=$(date +%s)

# --- post-run ---
DUR=$(( END_TS - START_TS ))
H=$(( DUR/3600 )); M=$(( (DUR%3600)/60 )); S=$(( DUR%60 ))
# simple health signal for compose healthcheck (optional)
# touch "$LOG_DIR/health.ok"

# always try to upload artifacts/logs if configured
upload_outputs || true

if [[ $STATUS -eq 0 ]]; then
  notify "✅ BPE training: SUCCESS on $(hostname) | ${H}h ${M}m ${S}s"
else
  notify "❌ BPE training: FAILED (exit $STATUS) on $(hostname) | ${H}h ${M}m ${S}s"
fi

exit $STATUS
