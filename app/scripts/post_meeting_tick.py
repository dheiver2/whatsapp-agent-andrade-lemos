"""Post-meeting follow-up: sequência Dia 1..7 após a reunião com Dr. Filipe.

Conforme Jornada Prescritiva Natasha v4.0 - seção "Follow pós reunião".
Roda via cron (1x ao dia, 10h BRT).
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

logger = logging.getLogger("post_meeting")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

WHATSAPP_SEND = "http://whatsapp:3001/send"
BR_TZ = timezone(timedelta(hours=-3))

POST_MEETING_MESSAGES = {
    1: (
        "Oi, {nome}. Tudo bem?\n\n"
        "Gostaria de reforçar um ponto importante: seu caso realmente apresenta "
        "fundamentos sólidos para revisão do reajuste.\n\n"
        "Se fizer sentido para você, já podemos seguir com os próximos passos "
        "ainda essa semana."
    ),
    2: (
        "Olá, {nome}.\n\n"
        "Você conseguiu avaliar com calma tudo o que conversamos na reunião?\n\n"
        "Se quiser, posso te relembrar de forma objetiva os benefícios práticos "
        "de iniciar agora."
    ),
    3: (
        "{nome}, queria te fazer uma pergunta direta:\n\n"
        "Quanto você ainda pretende pagar a mais aguardando para decidir?\n\n"
        "Quanto antes iniciarmos, antes você interrompe esse impacto financeiro."
    ),
    4: (
        "Quero reforçar algo importante:\n\n"
        "A ação serve justamente para proteger seu contrato e evitar qualquer "
        "risco de cancelamento enquanto discutimos o reajuste.\n\n"
        "Se essa era uma preocupação sua, pode ficar tranquilo.\n\n"
        "Quer que a gente avance?"
    ),
    5: (
        "{nome}, estou organizando os casos que vão avançar essa semana.\n\n"
        "Prefere que eu já reserve sua entrada agora ou quer retomar em outro "
        "momento específico?"
    ),
    6: (
        "Posso facilitar para você:\n\n"
        "Prefere que eu envie novamente o link para assinatura do contrato ou "
        "quer que eu te ligue para alinharmos rapidamente?"
    ),
    7: (
        "{nome}, deixo essa como minha última mensagem por agora para respeitar "
        "seu tempo.\n\n"
        "Quando decidir seguir com a revisão do plano, é só me avisar que "
        "retomamos imediatamente.\n\n"
        "Estou à disposição."
    ),
}


async def send_whatsapp(phone: str, message: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(WHATSAPP_SEND, json={"phone": phone, "message": message})
            return r.status_code == 200
    except Exception as e:
        logger.error("send falhou %s: %s", phone, e)
        return False


def _meeting_ended(profile: dict) -> tuple[bool, int]:
    slot = profile.get("confirmed_slot") or profile.get("meeting_end")
    if not slot:
        return False, -1
    try:
        dt = datetime.fromisoformat(str(slot).replace("Z", "+00:00"))
        end = dt + timedelta(minutes=30)
        now = datetime.now(BR_TZ)
        if now < end:
            return False, -1
        days = (now.astimezone(BR_TZ).date() - end.astimezone(BR_TZ).date()).days
        return True, days
    except Exception:
        return False, -1


async def process_lead(r, phone: str, profile: dict) -> None:
    if not profile.get("calendar_event_id") and not profile.get("confirmed_slot"):
        return

    lead_status = profile.get("lead_status", "")
    if lead_status in ("won", "contrato_fechado", "sem_interesse"):
        return

    ended, days = _meeting_ended(profile)
    if not ended or days < 1:
        return

    last_pm_day = int(profile.get("post_meeting_day") or 0)

    target_day = None
    for d in sorted(POST_MEETING_MESSAGES.keys()):
        if d <= days and d > last_pm_day:
            target_day = d

    if not target_day:
        return

    nome = (profile.get("name_full") or profile.get("name") or "").split()
    nome = nome[0] if nome else ""
    msg = POST_MEETING_MESSAGES[target_day].format(nome=nome)
    ok = await send_whatsapp(phone, msg)
    if not ok:
        logger.error("falha pós-reunião Dia %d para %s", target_day, phone)
        return

    logger.info("pós-reunião Dia %d → %s (%s)", target_day, phone, nome)

    profile["post_meeting_day"] = target_day
    profile["post_meeting_last_at"] = datetime.now(BR_TZ).isoformat()
    if target_day >= 7:
        profile["lead_status"] = "sem_interesse"
    await r.set(f"profile:{phone}", json.dumps(profile))


async def main():
    r = await get_redis()
    count = 0
    async for key in r.scan_iter("profile:*"):
        try:
            phone = key.replace("profile:", "")
            raw = await r.get(key)
            profile = json.loads(raw or "{}")
            await process_lead(r, phone, profile)
            count += 1
        except Exception as e:
            logger.error("erro %s: %s", key, e)
    logger.info("post-meeting tick OK %d leads", count)


if __name__ == "__main__":
    asyncio.run(main())
