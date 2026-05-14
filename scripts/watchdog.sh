#!/bin/bash
# Watchdog do bot WhatsApp - Andrade & Lemos
# Roda a cada 2 min via cron. Detecta queda e envia alerta.

ALERT_PHONE="5551989889898"
WA_URL="http://localhost:3001"
STATE_FILE="/var/run/whatsapp-watchdog.state"
LOG_FILE="/var/log/whatsapp-watchdog.log"
CONTAINER="whatsapp-agent_whatsapp_1"

mkdir -p /var/run /var/log
touch "$STATE_FILE" "$LOG_FILE"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

send_alert() {
    local msg="$1"
    curl -s -m 10 -X POST "$WA_URL/send" \
        -H 'Content-Type: application/json' \
        -d "{\"phone\":\"$ALERT_PHONE\",\"message\":\"🤖 *Bot Andrade & Lemos*\\n\\n$msg\"}" \
        >/dev/null 2>&1
    log "alert sent: $msg"
}

# Obter status atual
RAW=$(curl -s -m 5 "$WA_URL/status" 2>/dev/null)
if [ -z "$RAW" ]; then
    CURRENT="unreachable"
else
    CURRENT=$(echo "$RAW" | grep -oE '"status":"[^"]+"' | cut -d: -f2 | tr -d '"')
    [ -z "$CURRENT" ] && CURRENT="unknown"
fi

LAST=$(cat "$STATE_FILE" 2>/dev/null || echo "unknown")
echo "$CURRENT" > "$STATE_FILE"

# Container container_status
CONTAINER_STATE=$(docker inspect "$CONTAINER" --format '{{.State.Status}}' 2>/dev/null || echo "missing")

# Caso 1: container parado - tenta levantar
if [ "$CONTAINER_STATE" = "exited" ] || [ "$CONTAINER_STATE" = "dead" ]; then
    log "container $CONTAINER em $CONTAINER_STATE — tentando start"
    docker start "$CONTAINER" >/dev/null 2>&1
    sleep 20
    NEW_RAW=$(curl -s -m 5 "$WA_URL/status" 2>/dev/null)
    NEW_STATUS=$(echo "$NEW_RAW" | grep -oE '"status":"[^"]+"' | cut -d: -f2 | tr -d '"')
    if [ "$NEW_STATUS" = "connected" ]; then
        send_alert "Container estava parado. Religado e CONECTADO ✅"
    else
        log "ALERTA: container subiu mas status=$NEW_STATUS"
    fi
    exit 0
fi

# Caso 2: transição de connected -> outro
if [ "$LAST" = "connected" ] && [ "$CURRENT" != "connected" ]; then
    log "CAIU: $LAST -> $CURRENT"
    sleep 25
    RAW2=$(curl -s -m 5 "$WA_URL/status" 2>/dev/null)
    CUR2=$(echo "$RAW2" | grep -oE '"status":"[^"]+"' | cut -d: -f2 | tr -d '"')
    if [ "$CUR2" = "connected" ]; then
        log "reconectou sozinho"
    else
        send_alert "⚠️ Bot DESCONECTOU do WhatsApp. Status: $CUR2. Verifique http://187.127.12.125:3001"
    fi

# Caso 3: voltou a conectar
elif [ "$LAST" != "connected" ] && [ "$CURRENT" = "connected" ]; then
    log "reconectou: $LAST -> connected"
    send_alert "✅ Bot RECONECTADO ao WhatsApp. Operando normalmente."

# Caso 4: ficou tempo em waiting - QR não foi escaneado
elif [ "$CURRENT" = "waiting" ]; then
    WAITING_SINCE=$(cat /var/run/whatsapp-waiting-since 2>/dev/null)
    NOW=$(date +%s)
    if [ -z "$WAITING_SINCE" ]; then
        echo "$NOW" > /var/run/whatsapp-waiting-since
    else
        DIFF=$((NOW - WAITING_SINCE))
        if [ $DIFF -gt 3600 ]; then  # 1 hora aguardando scan
            LAST_NOTIFY=$(cat /var/run/whatsapp-waiting-notified 2>/dev/null || echo 0)
            if [ $((NOW - LAST_NOTIFY)) -gt 7200 ]; then  # avisa no maximo 1x a cada 2h
                send_alert "⏰ Bot aguarda QR ser escaneado há $(($DIFF/60)) min. Reescaneie em http://187.127.12.125:3001"
                echo "$NOW" > /var/run/whatsapp-waiting-notified
            fi
        fi
    fi
else
    rm -f /var/run/whatsapp-waiting-since
fi

log "ok $LAST -> $CURRENT (container=$CONTAINER_STATE)"
