"""Scheduling helpers — fluxo conversacional com preferências."""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime

from app.agents.scheduling_intent import SchedulingPreference, extract_scheduling_preference
from app.scheduling.google_calendar import Slot, create_event, get_available_slots

logger = logging.getLogger(__name__)

ORDINALS = {
    "1": 0, "1°": 0, "1º": 0, "primeira": 0, "primeiro": 0,
    "primeira opcao": 0, "primeira opção": 0, "opcao 1": 0, "opção 1": 0,
    "2": 1, "2°": 1, "2º": 1, "segunda": 1, "segundo": 1,
    "segunda opcao": 1, "segunda opção": 1, "opcao 2": 1, "opção 2": 1,
    "3": 2, "terceira": 2, "terceiro": 2,
    "4": 3, "quarta": 3, "quarto": 3,
    "5": 4, "quinta": 4, "quinto": 4,
}

# Conjunto de palavras que indicam que o cliente está escolhendo (não preferindo)
CHOOSING_TOKENS = {"1", "2", "primeira", "segunda", "primeiro", "segundo", "opcao 1", "opcao 2", "opção 1", "opção 2"}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


async def fetch_suggestion_message(
    name: str = "",
    preference: SchedulingPreference | None = None,
    exclude: list[dict] | None = None,
) -> tuple[str, list[Slot]]:
    exclude_tuples = []
    if exclude:
        exclude_tuples = [(s["start"], s["end"]) for s in exclude]

    slots = await get_available_slots(preference=preference, exclude_slots=exclude_tuples)
    prefix = f"{name}, " if name else ""

    if not slots:
        # Tenta de novo sem a preferência (mostra alternativas)
        if preference and preference.has_any():
            slots_any = await get_available_slots(exclude_slots=exclude_tuples)
            if slots_any:
                pref_desc = preference.describe()
                lines = [f"{prefix}não tenho horário livre {pref_desc}."]
                lines.append("Posso te oferecer:")
                for idx, slot in enumerate(slots_any, start=1):
                    lines.append(f"{idx}. {slot.format_pt()}")
                lines.append("")
                lines.append("Algum desses serve?")
                return "\n".join(lines), slots_any
        return (
            f"{prefix}não consegui localizar horários livres com esses critérios. "
            "Tem outra preferência de dia ou horário?",
            [],
        )

    pref_desc = preference.describe() if preference else ""
    intro = f"{prefix}aqui estão os horários livres"
    if pref_desc:
        intro += f" {pref_desc}"
    intro += ":"
    lines = [intro]
    for idx, slot in enumerate(slots, start=1):
        lines.append(f"{idx}. {slot.format_pt()}")
    lines.append("")
    lines.append("Qual prefere? (pode responder com o número)")
    return "\n".join(lines), slots


def parse_slot_choice(text: str, pending_slots: list[dict]) -> dict | None:
    """Identifica qual slot o usuário escolheu dentre os já oferecidos."""
    if not pending_slots:
        return None

    raw = text.strip().lower()
    norm = _strip_accents(raw)

    # 1) Match por número/ordinal explícito
    for token in re.findall(r"\b[\w°º]+\b", norm):
        if token in ORDINALS:
            idx = ORDINALS[token]
            if idx < len(pending_slots):
                return pending_slots[idx]

    # 2) Match por horário mencionado
    hour_match = re.search(r"\b(\d{1,2})\s*[h:]\s*(\d{1,2})?\b", norm)
    if hour_match:
        hour = int(hour_match.group(1))
        minute = int(hour_match.group(2) or 0)
        for slot in pending_slots:
            start = datetime.fromisoformat(slot["start"])
            if start.hour == hour and (minute == 0 or start.minute == minute):
                return slot

    # 3) Match por data (dd/mm)
    date_match = re.search(r"\b(\d{1,2})/(\d{1,2})\b", norm)
    if date_match:
        day, month = int(date_match.group(1)), int(date_match.group(2))
        for slot in pending_slots:
            start = datetime.fromisoformat(slot["start"])
            if start.day == day and start.month == month:
                return slot

    return None


async def confirm_and_book(slot_dict: dict, name: str, phone: str) -> dict:
    start = datetime.fromisoformat(slot_dict["start"])
    return await create_event(start=start, attendee_name=name, attendee_phone=phone)


def format_confirmation_message(slot_dict: dict, name: str = "") -> str:
    start = datetime.fromisoformat(slot_dict["start"])
    end = datetime.fromisoformat(slot_dict["end"])
    dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    wd = dias[start.weekday()]
    prefix = f"{name}, " if name else ""
    return (
        f"{prefix}prontinho! Consulta agendada com o Dr. Filipe:\n\n"
        f"📅 {wd}, {start.strftime('%d/%m')}\n"
        f"🕐 {start.strftime('%H:%M')} às {end.strftime('%H:%M')}\n\n"
        "É uma análise rápida pelo WhatsApp ou ligação no horário marcado."
    )


# legacy
def get_booking_link() -> str:
    return ""


def get_scheduling_message(nome: str = "") -> str:
    prefix = f"{nome}, " if nome else ""
    return f"{prefix}vou te enviar os horários disponíveis do Dr. Filipe em instantes."
