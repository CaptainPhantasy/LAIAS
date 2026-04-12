#!/bin/bash
# PSI Realtor Pipeline
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
[ -f /Volumes/Storage/LAIAS/.env ] && export $(grep -v '^#' /Volumes/Storage/LAIAS/.env | xargs)
cd /Volumes/Storage/LAIAS
echo "=== PSI Realtor Pipeline — $(date) ==="
/opt/homebrew/bin/python3.11 -c "from agents.psi_realtor_pipeline.flow import run_pipeline; run_pipeline()"
echo "=== Completed — $(date) ==="
