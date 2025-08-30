#!/usr/bin/env bash
set -euo pipefail

# ====== USER / ENV SETTINGS ======
RG="${RG:-bpe-rg}"                         # Resource group (only for auto-deallocate)
VM_NAME="${VM_NAME:-trial-bpe}"            # VM name (only for auto-deallocate)
REPO_DIR="${REPO_DIR:-$HOME/stf-assignment1-basics}"
MODULE="${MODULE:-cs336_basics.train_bpe}" # python -m <module>
NTFY_TOPIC="${NTFY_TOPIC:-bpe-$(openssl rand -hex 4)}"

# SAS URL with write perms to your container (container-level URL recommended)
# Example: https://<account>.blob.core.windows.net/bpe-out?<SAS>
OUTPUT_SAS_URL="${OUTPUT_SAS_URL:-}"

# Auto stop VM when done (requires system-assigned identity + role; see notes)
AUTO_DEALLOCATE="${AUTO_DEALLOCATE:-false}"

# For small VMs keep parallelism low unless you override
# export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
# =================================

cd "$REPO_DIR"

echo "==> Open to receive notifications:"
echo "    https://ntfy.sh/${NTFY_TOPIC}"
echo

# --- helpers ---
ensure_azcopy() {
  if ! command -v azcopy >/dev/null 2>&1; then
    echo "==> Installing azcopy into \$HOME/tools..."
    mkdir -p "$HOME/tools"
    local oldpwd; oldpwd="$(pwd)"
    cd "$HOME/tools"
    curl -sL https://aka.ms/downloadazcopy-v10-linux | bash >/dev/null 2>&1
    cd "$oldpwd" >/dev/null
    # add to PATH for this shell
    local AZC
    AZC=$(find "$HOME/tools" -maxdepth 1 -type d -name 'azcopy_linux_*' | head -n1 || true)
    [[ -n "${AZC:-}" ]] && export PATH="$AZC:$PATH"
  fi
  command -v azcopy >/dev/null 2>&1 || { echo "ERROR: azcopy not found"; exit 127; }
}

upload_outputs() {
  [[ -z "${OUTPUT_SAS_URL}" ]] && { echo "WARN: OUTPUT_SAS_URL not set; skipping upload"; return 0; }
  ensure_azcopy
  echo "==> Uploading cs336_basics/outputs/* to Blob..."
  azcopy copy "cs336_basics/outputs/*" "${OUTPUT_SAS_URL}" >/dev/null
  echo "==> Upload complete."
}

notify() {
  local msg="$1"
  curl -fsS -d "$msg" "https://ntfy.sh/${NTFY_TOPIC}" >/dev/null || true
}
# ---------------

# Ensure tools
command -v uv >/dev/null 2>&1 || { echo "ERROR: uv not found on PATH"; exit 127; }

# Log file
mkdir -p cs336_basics/outputs
LOG_FILE="cs336_basics/outputs/run_$(date -u +%Y%m%dT%H%M%SZ).log"
echo "    https://ntfy.sh/${NTFY_TOPIC}" > cs336_basics/outputs/notify_url.txt

START_TS=$(date +%s)
set +e
uv run python -m "$MODULE" 2>&1 | tee -a "$LOG_FILE"
STATUS=${PIPESTATUS[0]}
set -e
END_TS=$(date +%s)

DUR=$(( END_TS - START_TS ))
H=$(( DUR/3600 )); M=$(( (DUR%3600)/60 )); S=$(( DUR%60 ))

# Always attempt upload
upload_outputs || true

if [[ $STATUS -eq 0 ]]; then
  notify "✅ BPE training: SUCCESS on $(hostname) | ${H}h ${M}m ${S}s"
else
  notify "❌ BPE training: FAILED (exit $STATUS) on $(hostname) | ${H}h ${M}m ${S}s"
fi

# Optional: auto-deallocate to save credit
#if [[ "${AUTO_DEALLOCATE}" == "true" ]]; then
#  # Requires: VM has system-assigned identity + role 'Virtual Machine Contributor'
#  # az vm identity assign -g "$RG" -n "$VM_NAME"
#  # az role assignment create --assignee-object-id "$(az vm show -g "$RG" -n "$VM_NAME" --query identity.principalId -o tsv)" \
#  #   --role "Virtual Machine Contributor" --scope "$(az vm show -g "$RG" -n "$VM_NAME" --query id -o tsv)"
#  az login --identity >/dev/null 2>&1 || true
#  az vm deallocate -g "$RG" -n "$VM_NAME" >/dev/null 2>&1 || true
#fi

exit $STATUS

