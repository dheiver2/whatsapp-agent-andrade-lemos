#!/bin/bash
# Follow-up worker - executa a cada hora via cron
# Verifica leads em silêncio e envia mensagens D+1..D+13
# Bot Andrade & Lemos

LOG=/var/log/whatsapp-followup.log
echo "[$(date '+%F %T')] tick" >> $LOG

# Roda dentro do container API que tem todas as deps
docker exec whatsapp-agent-api-1 python -m app.scripts.followup_tick >> $LOG 2>&1
