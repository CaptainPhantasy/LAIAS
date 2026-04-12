#!/bin/bash
# Daily SMB Hunter — Runs at 7 PM via cron
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
[ -f /Volumes/Storage/LAIAS/.env ] && export $(grep -v '^#' /Volumes/Storage/LAIAS/.env | xargs)
cd /Volumes/Storage/LAIAS
echo "============================================"
echo "Daily SMB Hunter — $(date)"
echo "============================================"
/opt/homebrew/bin/python3.11 -c "from agents.daily_smb_hunter.flow import run_hunter; run_hunter()"
echo "============================================"
echo "Completed — $(date)"
echo "============================================"
