"""Reminder worker: dispara lembrete 30 min antes de consultas no Calendar.

Roda via cron (a cada 5 min).
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timedelta, timezone

import httpx

sys.path.insert(0, "/app")
from app.memory.user_memory import get_redis
from app.scheduling.google_calendar import _calendar_service, _br_tz
from app.config import get_settings

logger = logging.getLogger("reminder")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

WHATSAPP_SEND = "http://whatsapp:3001/send"


async def send(phone: str, msg: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(WHATSAPP_SEND, json={"phone": phone, "message": msg})
            return r.status_code == 200
    except Exception as e:
        logger.error("send falhou %s: %s", phone, e)
        return False


def _phone_from_description(desc: str) -> str | None:
    # description tem "Telefone: +5511987654321"
    m = re.search(r"Telefone:\s*(\+?\d[\d\s\-]+)", desc or "")
    if m:
        return re.sub(r"\D", "", m.group(1))
    return None


async def main():
    settings = get_settings()
    try:
        service = _calendar_service()
        cal_id = settings.google_calendar_id
    except Exception as e:
        logger.error("calendar init falhou: %s", e)
        return

    br = _br_tz()
    now = datetime.now(br)
    # Janela: eventos que começam em 25-35 min
    window_start = now + timedelta(minutes=25)
    window_end = now + timedelta(minutes=35)

    r = get_redis()
    try:
        evs = service.events().list(
            calendarId=cal_id,
            timeMin=window_start.isoformat(),
            timeMax=window_end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=10,
        ).execute().get("items", [])
    except Exception as e:
        logger.error("freebusy/list falhou: %s", e)
        return

    for ev in evs:
        event_id = ev.get("id", "")
        if not event_id:
            continue
        # Já enviou lembrete pra esse evento?
        if r.get(f"reminded:{event_id}"):
            continue
        # Só lembrar eventos criados pelo bot (têm "via WhatsApp" na descrição)
        desc = ev.get("description", "")
        if "via WhatsApp" not in desc and "Consulta" not in ev.get("summary", ""):
            continue
        phone = _phone_from_description(desc)
        if not phone:
            continue
        # Nome do cliente
        profile_raw = r.get(f"profile:{phone}") or "{}"
        try:
            profile = json.loads(profile_raw)
            name = profile.get("name", "")
        except Exception:
            name = ""
        prefix = f"{name}, " if name else ""
        msg = (
            f"{prefix}tudo bem? Te envio o link da reunião com o Dr. Filipe "
            "em 30 minutos, ok? 📅"
        )
        ok = await send(phone, msg)
        if ok:
            # Marca como lembrado (TTL 4h)
            r.setex(f"reminded:{event_id}", 4 * 3600, "1")
            logger.info("lembrete enviado: evento %s → %s", event_id, phone)


if __name__ == "__main__":
    asyncio.run(main())
