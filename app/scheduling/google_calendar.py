"""Google Calendar integration v3 — com filtro de preferência e exclude_slots."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import get_settings
from app.agents.scheduling_intent import SchedulingPreference

logger = logging.getLogger(__name__)

BUSINESS_DAYS = {0, 1, 2, 3, 4}
BUSINESS_HOUR_START = 8
BUSINESS_HOUR_END = 18
TZ_OFFSET_HOURS = -3
SCOPES = ["https://www.googleapis.com/auth/calendar"]


@dataclass(frozen=True)
class Slot:
    start: datetime
    end: datetime

    def format_pt(self) -> str:
        dias = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
        wd = dias[self.start.weekday()]
        return f"{wd} {self.start.strftime('%d/%m')} às {self.start.strftime('%H:%M')}"


def _br_tz() -> timezone:
    return timezone(timedelta(hours=TZ_OFFSET_HOURS))


def _now_br() -> datetime:
    return datetime.now(_br_tz())


@lru_cache(maxsize=1)
def _calendar_service():
    settings = get_settings()
    sa_path = Path(settings.google_sa_path)
    if not sa_path.exists():
        raise RuntimeError(f"Service Account file não encontrado em {sa_path}")
    creds = service_account.Credentials.from_service_account_file(
        str(sa_path), scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _list_busy(start: datetime, end: datetime, calendar_id: str) -> list[tuple[datetime, datetime]]:
    try:
        service = _calendar_service()
        body = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": calendar_id}],
        }
        result = service.freebusy().query(body=body).execute()
        busy_raw = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])
        out = []
        for item in busy_raw:
            s = datetime.fromisoformat(item["start"].replace("Z", "+00:00")).astimezone(_br_tz())
            e = datetime.fromisoformat(item["end"].replace("Z", "+00:00")).astimezone(_br_tz())
            out.append((s, e))
        return out
    except HttpError as exc:
        logger.error("freebusy falhou: %s", exc)
        return []


def _generate_business_slots(days_ahead: int, duration_min: int) -> list[Slot]:
    now = _now_br()
    cursor = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    end_window = now + timedelta(days=days_ahead)
    slots: list[Slot] = []
    while cursor < end_window:
        if (
            cursor.weekday() in BUSINESS_DAYS
            and BUSINESS_HOUR_START <= cursor.hour < BUSINESS_HOUR_END
        ):
            slot_end = cursor + timedelta(minutes=duration_min)
            if slot_end.hour <= BUSINESS_HOUR_END or (
                slot_end.hour == BUSINESS_HOUR_END and slot_end.minute == 0
            ):
                slots.append(Slot(start=cursor, end=slot_end))
        cursor += timedelta(minutes=duration_min)
    return slots


def _matches_preference(slot: Slot, pref: SchedulingPreference) -> bool:
    """Verifica se o slot atende à preferência do cliente."""
    s = slot.start
    if pref.period == "manha" and s.hour >= 12:
        return False
    if pref.period == "tarde" and s.hour < 12:
        return False
    if pref.weekday is not None and s.weekday() != pref.weekday:
        return False
    if pref.target_date is not None and s.date() != pref.target_date:
        return False
    if pref.specific_time is not None:
        h, m = pref.specific_time
        # match exato (mesmo horário e minuto)
        if s.hour != h or s.minute != m:
            return False
    if pref.week_offset is not None:
        now = _now_br()
        this_monday = now.date() - timedelta(days=now.weekday())
        target_monday = this_monday + timedelta(weeks=pref.week_offset)
        target_sunday = target_monday + timedelta(days=6)
        if not (target_monday <= s.date() <= target_sunday):
            return False
    return True


async def get_available_slots(
    preference: SchedulingPreference | None = None,
    exclude_slots: list[tuple[str, str]] | None = None,
    slots_count: int | None = None,
    duration_min: int | None = None,
    days_ahead: int = 21,
) -> list[Slot]:
    settings = get_settings()
    slots_count = slots_count or settings.scheduling_slots_count
    duration_min = duration_min or settings.meeting_duration_min
    cal_id = settings.google_calendar_id
    exclude_set = set()
    if exclude_slots:
        exclude_set = {(s, e) for s, e in exclude_slots}

    def _sync() -> list[Slot]:
        candidates = _generate_business_slots(days_ahead, duration_min)
        if preference and preference.has_any():
            candidates = [s for s in candidates if _matches_preference(s, preference)]
        if not candidates:
            return []

        window_start = candidates[0].start
        window_end = candidates[-1].end
        busy = _list_busy(window_start, window_end, cal_id)

        free: list[Slot] = []
        for slot in candidates:
            # exclude_set: slots já oferecidos anteriormente (não repetir)
            slot_key = (slot.start.isoformat(), slot.end.isoformat())
            if slot_key in exclude_set:
                continue
            overlaps = any(
                slot.start < b_end and slot.end > b_start for b_start, b_end in busy
            )
            if not overlaps:
                free.append(slot)
            if len(free) >= slots_count:
                break
        return free

    return await asyncio.to_thread(_sync)


async def create_event(
    start: datetime,
    attendee_name: str,
    attendee_phone: str,
    duration_min: int | None = None,
    summary: str | None = None,
    description: str | None = None,
) -> dict:
    settings = get_settings()
    duration_min = duration_min or settings.meeting_duration_min
    cal_id = settings.google_calendar_id
    summary = summary or f"Consulta — {attendee_name or attendee_phone}"
    description = description or (
        f"Consulta agendada via WhatsApp pelo agente Andrade & Lemos.\n"
        f"Cliente: {attendee_name or '(sem nome)'}\n"
        f"Telefone: {attendee_phone}"
    )

    end = start + timedelta(minutes=duration_min)
    if start.tzinfo is None:
        start = start.replace(tzinfo=_br_tz())
        end = end.replace(tzinfo=_br_tz())

    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": end.isoformat(), "timeZone": "America/Sao_Paulo"},
        "reminders": {"useDefault": True},
    }

    def _sync() -> dict:
        try:
            service = _calendar_service()
            event = service.events().insert(calendarId=cal_id, body=body).execute()
            return {
                "id": event.get("id"),
                "htmlLink": event.get("htmlLink"),
                "start": start.isoformat(),
                "end": end.isoformat(),
            }
        except HttpError as exc:
            logger.error("create_event falhou: %s", exc)
            raise

    return await asyncio.to_thread(_sync)
