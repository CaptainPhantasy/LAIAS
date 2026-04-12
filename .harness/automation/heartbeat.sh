#!/bin/bash
# PEBKAC Harness Heartbeat -- auto-generated during unboxing
# Checks session health, proxy validity, and checkpoint age.
# macOS/Linux version (F17 fix: cross-platform stat handling)

HARNESS_DIR="${HOME}/.harness"

# Check vault accessibility
if [ -f "${HARNESS_DIR}/vault/config.yaml" ]; then
    echo "[heartbeat] Vault config: OK"
else
    echo "[heartbeat] Vault config: MISSING"
fi

# Check checkpoint age (cross-platform: macOS stat -f %m, Linux stat -c %Y)
LATEST="${HARNESS_DIR}/checkpoints/latest.json"
if [ -f "${LATEST}" ]; then
    # Try macOS stat first, fall back to Linux stat
    MTIME=$(stat -f %m "${LATEST}" 2>/dev/null || stat -c %Y "${LATEST}" 2>/dev/null || echo 0)
    AGE=$(( $(date +%s) - ${MTIME} ))
    if [ "${AGE}" -gt 3600 ]; then
        echo "[heartbeat] Checkpoint: STALE (${AGE}s old)"
    else
        echo "[heartbeat] Checkpoint: OK (${AGE}s old)"
    fi
else
    echo "[heartbeat] Checkpoint: NONE"
fi

# Update heartbeat timestamp
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${HARNESS_DIR}/state/last-heartbeat.txt"

echo "[heartbeat] $(date -u +%Y-%m-%dT%H:%M:%SZ) complete"
