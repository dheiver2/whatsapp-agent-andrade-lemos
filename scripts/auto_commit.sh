#!/bin/bash
# Auto-commit diario do estado da VPS
set -eu
cd /root/whatsapp-agent
git add -A
if git diff --cached --quiet; then
    echo "[$(date '+%F %T')] nada a commitar" >> /var/log/whatsapp-git-autocommit.log
    exit 0
fi
DATE=$(date '+%Y-%m-%d %H:%M')
git commit -m "auto: snapshot $DATE" >> /var/log/whatsapp-git-autocommit.log 2>&1
git push origin main >> /var/log/whatsapp-git-autocommit.log 2>&1
echo "[$(date '+%F %T')] commit + push OK" >> /var/log/whatsapp-git-autocommit.log
