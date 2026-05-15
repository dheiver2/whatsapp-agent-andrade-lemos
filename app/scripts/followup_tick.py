"""Follow-up worker: percorre leads, calcula days_since_last_msg, envia mensagem do dia.

Roda via cron (a cada hora).
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta, timezone

import httpx

sys.path.insert(0, "/app")
from app.memory.user_memory import get_redis

logger = logging.getLogger("followup")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

WHATSAPP_SEND = "http://whatsapp:3001/send"
BR_TZ = timezone(timedelta(hours=-3))

# Mensagens D+N (do documento oficial)
FOLLOWUP_MESSAGES = {
    1: "Olá! Tudo bem? Conseguiu ver minha mensagem? Seu reajuste pode estar acima do permitido.",
    3: "Muitas pessoas só descobrem que o reajuste é abusivo depois de meses pagando. Quer verificar o seu hoje?",
    5: "Posso te enviar um resumo simples de como funciona esse pedido de revisão?",
    7: "Quer que eu veja horários para nossa consulta?",
    10: "Hoje estamos finalizando os horários dessa semana para análise de reajuste. Quer que eu reserve uma vaga para você agora ou prefere que eu te procure em outro momento?",
    13: "{nome}, caso mude de ideia, estamos à disposição. Basta me chamar aqui. Boa sorte!",
}


async def send_whatsapp(phone: str, message: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(WHATSAPP_SEND, json={"phone": phone, "message": message})
            return r.status_code == 200
    except Exception as e:
        logger.error("send falhou %s: %s", phone, e)
        return False


def _days_since(iso: str) -> int:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (datetime.now(BR_TZ) - dt.astimezone(BR_TZ)).days
    except Exception:
        return -1


async def process_lead(phone: str, profile: dict, history: list) -> None:
    # Se já agendado/ganho/handoff → não fazer follow-up
    lead_status = profile.get("lead_status", "")
    if lead_status in ("scheduled", "won", "waiting_human", "sem_interesse"):
        return

    # Última mensagem do USUÁRIO (não do bot)
    last_user_at = None
    for msg in reversed(history):
        if msg.get("role") == "user" and msg.get("content"):
            last_user_at = msg.get("ts") or profile.get("last_user_at")
            break
    if not last_user_at:
        return

    days = _days_since(last_user_at)
    if days < 1:
        return

    # Verifica último D+N enviado
    last_followup_day = int(profile.get("last_followup_day") or 0)

    # Encontra qual D+N enviar agora
    target_day = None
    for d in sorted(FOLLOWUP_MESSAGES.keys()):
        if d <= days and d > last_followup_day:
            target_day = d

    if not target_day:
        return  # já enviou tudo até esse dia

    msg = FOLLOWUP_MESSAGES[target_day].format(nome=profile.get("name", ""))
    ok = await send_whatsapp(phone, msg)
    if not ok:
        logger.error("falha ao enviar D+%d para %s", target_day, phone)
        return

    logger.info("enviado D+%d para %s (%s)", target_day, phone, profile.get("name", ""))

    # Atualiza Redis
    r = get_redis()
    profile["last_followup_day"] = target_day
    profile["last_followup_at"] = datetime.now(BR_TZ).isoformat()
    if target_day >= 13:
        profile["lead_status"] = "sem_interesse"
    r.set(f"profile:{phone}", json.dumps(profile))


async def main():
    r = get_redis()
    count = 0
    for key in r.scan_iter("profile:*"):
        try:
            phone = key.replace("profile:", "")
            profile = json.loads(r.get(key) or "{}")
            history_raw = r.get(f"history:{phone}") or "[]"
            history = json.loads(history_raw)
            await process_lead(phone, profile, history)
            count += 1
        except Exception as e:
            logger.error("erro no perfil %s: %s", key, e)
    logger.info("tick OK %d leads processados", count)


if __name__ == "__main__":
    asyncio.run(main())
