"""Extrator de preferência de agendamento a partir da fala do cliente.

Detecta período (manhã/tarde), dia da semana, data específica, horário exato,
e janelas relativas ("semana que vem", "hoje", "amanhã").
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta

WEEKDAY_MAP = {
    "segunda": 0, "segunda-feira": 0, "seg": 0,
    "terca": 1, "terça": 1, "terca-feira": 1, "terça-feira": 1, "ter": 1,
    "quarta": 2, "quarta-feira": 2, "qua": 2,
    "quinta": 3, "quinta-feira": 3, "qui": 3,
    "sexta": 4, "sexta-feira": 4, "sex": 4,
}

MONTH_MAP = {
    "janeiro": 1, "jan": 1, "fevereiro": 2, "fev": 2,
    "marco": 3, "março": 3, "mar": 3, "abril": 4, "abr": 4,
    "maio": 5, "mai": 5, "junho": 6, "jun": 6,
    "julho": 7, "jul": 7, "agosto": 8, "ago": 8,
    "setembro": 9, "set": 9, "outubro": 10, "out": 10,
    "novembro": 11, "nov": 11, "dezembro": 12, "dez": 12,
}


@dataclass
class SchedulingPreference:
    weekday: int | None = None
    period: str | None = None  # "manha" | "tarde"
    target_date: date | None = None
    specific_time: tuple[int, int] | None = None
    week_offset: int | None = None  # 0 = essa semana, 1 = próxima

    def has_any(self) -> bool:
        return any(
            v is not None
            for v in (self.weekday, self.period, self.target_date, self.specific_time, self.week_offset)
        )

    def describe(self) -> str:
        parts = []
        if self.target_date:
            parts.append(self.target_date.strftime("dia %d/%m"))
        if self.weekday is not None:
            dias = ["segunda", "terça", "quarta", "quinta", "sexta"]
            parts.append(dias[self.weekday])
        if self.week_offset == 1:
            parts.append("semana que vem")
        elif self.week_offset == 0:
            parts.append("esta semana")
        if self.period == "manha":
            parts.append("de manhã")
        elif self.period == "tarde":
            parts.append("à tarde")
        if self.specific_time:
            h, m = self.specific_time
            parts.append(f"às {h:02d}:{m:02d}")
        return " ".join(parts) if parts else ""


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def extract_scheduling_preference(text: str, today: date | None = None) -> SchedulingPreference:
    today = today or date.today()
    pref = SchedulingPreference()
    raw = text.strip()
    norm = _strip_accents(raw.lower())

    # === Período do dia ===
    if re.search(r"\b(manha|de manha|pela manha|cedo|amanhecer)\b", norm):
        pref.period = "manha"
    elif re.search(r"\b(tarde|a tarde|de tarde|pela tarde|fim de tarde)\b", norm):
        pref.period = "tarde"

    # === Janela relativa ===
    if re.search(r"\b(semana que vem|proxima semana|próxima semana|semana proxima)\b", norm):
        pref.week_offset = 1
    elif re.search(r"\b(essa semana|esta semana|nessa semana|nesta semana)\b", norm):
        pref.week_offset = 0

    # === Dia da semana ===
    for term, wd in sorted(WEEKDAY_MAP.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{_strip_accents(term)}\b", norm):
            pref.weekday = wd
            break

    # === Data específica DD/MM[/YYYY] ===
    m = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,2})(?:\s*/\s*(\d{2,4}))?\b", raw)
    if m:
        try:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else today.year
            if year < 100:
                year += 2000
            candidate = date(year, month, day)
            # se a data já passou neste ano, assume próximo ano
            if candidate < today and not m.group(3):
                candidate = date(year + 1, month, day)
            pref.target_date = candidate
        except (ValueError, TypeError):
            pass

    # === "dia X" sozinho ===
    if not pref.target_date:
        m = re.search(r"\bdia\s+(\d{1,2})\b", norm)
        if m:
            try:
                day = int(m.group(1))
                candidate = date(today.year, today.month, day)
                if candidate < today:
                    if today.month == 12:
                        candidate = date(today.year + 1, 1, day)
                    else:
                        candidate = date(today.year, today.month + 1, day)
                pref.target_date = candidate
            except ValueError:
                pass

    # === "X de mês" ===
    if not pref.target_date:
        for month_name, month_num in MONTH_MAP.items():
            pattern = rf"\b(\d{{1,2}})\s+de\s+{_strip_accents(month_name)}\b"
            m = re.search(pattern, norm)
            if m:
                try:
                    day = int(m.group(1))
                    year = today.year
                    candidate = date(year, month_num, day)
                    if candidate < today:
                        candidate = date(year + 1, month_num, day)
                    pref.target_date = candidate
                    break
                except ValueError:
                    pass

    # === Hoje / amanhã / depois de amanhã ===
    if not pref.target_date:
        if re.search(r"\bhoje\b", norm):
            pref.target_date = today
        elif re.search(r"\b(amanha|amanhã)\b", norm) and not re.search(r"depois de amanha|depois de amanhã", norm):
            pref.target_date = today + timedelta(days=1)
        elif re.search(r"\bdepois de amanha\b|\bdepois de amanhã\b", norm):
            pref.target_date = today + timedelta(days=2)

    # === Horário específico ===
    # 14h30, 14:30, 14h, às 14, 14 horas
    time_patterns = [
        r"\b(\d{1,2})\s*[h:]\s*(\d{2})\b",
        r"\bas\s+(\d{1,2})\s*[h:]\s*(\d{2})\b",
        r"\bàs\s+(\d{1,2})\s*[h:]\s*(\d{2})\b",
        r"\b(\d{1,2})\s*h\b",
        r"\bas\s+(\d{1,2})\b(?!\s*/)",
        r"\bàs\s+(\d{1,2})\b(?!\s*/)",
        r"\b(\d{1,2})\s+horas?\b",
    ]
    for pat in time_patterns:
        m = re.search(pat, norm)
        if m:
            try:
                h = int(m.group(1))
                mn = int(m.group(2)) if (m.lastindex and m.lastindex >= 2 and m.group(2)) else 0
                if 0 <= h <= 23 and 0 <= mn <= 59:
                    pref.specific_time = (h, mn)
                    break
            except (ValueError, IndexError):
                pass

    return pref
