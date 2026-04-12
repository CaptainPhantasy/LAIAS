#!/bin/bash
# SMB Website Prospector
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
[ -f /Volumes/Storage/LAIAS/.env ] && export $(grep -v '^#' /Volumes/Storage/LAIAS/.env | xargs)
cd /Volumes/Storage/LAIAS
echo "=== SMB Website Prospector — $(date) ==="
/opt/homebrew/bin/python3.11 -c "from agents.smb_website_prospector.flow import run_prospector; run_prospector()"
echo "=== Completed — $(date) ==="
