#!/bin/bash
# Backup diário do volume de autenticação WhatsApp
# Mantém últimos 7 dias automaticamente

BACKUP_DIR=/root/backups/whatsapp-auth
VOLUME=whatsapp-agent_whatsapp_auth
RETAIN_DAYS=7

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
FILENAME="auth_${TIMESTAMP}.tar.gz"

# Criar backup do volume via container alpine temporário
docker run --rm \
    -v "$VOLUME":/data:ro \
    -v "$BACKUP_DIR":/backup \
    alpine sh -c "cd /data && tar czf /backup/$FILENAME ." 2>/dev/null

if [ $? -eq 0 ] && [ -f "$BACKUP_DIR/$FILENAME" ]; then
    SIZE=$(du -h "$BACKUP_DIR/$FILENAME" | cut -f1)
    echo "[$(date)] backup criado: $FILENAME ($SIZE)" >> /var/log/whatsapp-backup.log
else
    echo "[$(date)] BACKUP FALHOU" >> /var/log/whatsapp-backup.log
    exit 1
fi

# Limpa backups antigos
find "$BACKUP_DIR" -name 'auth_*.tar.gz' -mtime +$RETAIN_DAYS -delete

# Lista atual
ls -1 "$BACKUP_DIR" >> /var/log/whatsapp-backup.log
