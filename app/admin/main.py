"""Admin backend v2 — adiciona endpoints JSON para o frontend Next.js."""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path
from typing import Annotated, Any

import httpx
import redis
from fastapi import Depends, FastAPI, Form, HTTPException, Request, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

import sys
sys.path.insert(0, "/app")

try:
    sys.path.insert(0, '/app')
    from app.agents.cenario import classify_cenario as _cls_cenario
except Exception:
    def _cls_cenario(p): return "indefinido"

def classify_cenario(p):
    return _cls_cenario(p)


ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "andradelemos2026")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
WHATSAPP_URL = "http://whatsapp:3001"
API_URL = "http://api:8000"
KNOWLEDGE_DIR = Path("/app/app/knowledge")

app = FastAPI(title="Andrade & Lemos - Admin")
templates = Jinja2Templates(directory="/app/app/admin/templates")
security = HTTPBasic()

# CORS for Next.js admin frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_r = None
def rd() -> redis.Redis:
    global _r
    if _r is None:
        _r = redis.from_url(REDIS_URL, decode_responses=True)
    return _r


def auth(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    ok_u = secrets.compare_digest(credentials.username, ADMIN_USER)
    ok_p = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (ok_u and ok_p):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def _br_now() -> datetime:
    return datetime.utcnow() - timedelta(hours=3)


def _get_calendar_data():
    try:
        from app.scheduling.google_calendar import _calendar_service, _br_tz
        from app.config import get_settings
        return _calendar_service(), get_settings().google_calendar_id, _br_tz()
    except Exception:
        return None, None, None


def _all_profiles() -> list[dict]:
    r = rd()
    profiles = []
    for key in r.scan_iter("profile:*"):
        try:
            data = json.loads(r.get(key))
            data["_phone"] = key.replace("profile:", "")
            data["_stage"] = r.get(f"stage:{data['_phone']}") or "?"
            profiles.append(data)
        except Exception:
            continue
    return profiles


# =====================================================================
# JSON API (/api/admin/*)
# =====================================================================

@app.get("/api/admin/dashboard")
async def api_dashboard(user: str = Depends(auth)):
    # status
    wa_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{WHATSAPP_URL}/status")
            wa_status = r.json().get("status", "unknown")
    except Exception:
        pass
    api_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{API_URL}/api/v1/health")
            api_status = r.json().get("status", "unknown")
    except Exception:
        pass

    profiles = _all_profiles()
    metrics = {"total_leads": len(profiles), "agendados": 0, "qualificando": 0, "handoff": 0, "novos_24h": 0}
    operadoras = Counter()
    modalidades = Counter()
    funil = Counter()
    leads_por_dia = Counter()

    today = _br_now().date()
    for p in profiles:
        if p.get("confirmed_slot"):
            metrics["agendados"] += 1
        elif p.get("lead_status") == "waiting_human":
            metrics["handoff"] += 1
        else:
            metrics["qualificando"] += 1
        op = p.get("operadora") or "—"
        if op != "?":
            operadoras[op] += 1
        mod = p.get("tipo_plano") or "—"
        if mod != "?":
            modalidades[mod] += 1
        stage = p.get("_stage", "?")
        if stage and stage != "?":
            funil[stage] += 1

    # leads_por_dia (mock estimate baseado em handoff_updated_at ou agora)
    # como nao temos timestamp de criacao salvo, fica vazio por enquanto
    # vamos preencher com base no dia atual
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        leads_por_dia[d.isoformat()] = 0

    # consultas proximas 7 dias
    consultas = []
    service, cal_id, br_tz = _get_calendar_data()
    if service and cal_id:
        try:
            now = datetime.now(br_tz)
            end = now + timedelta(days=7)
            evs = service.events().list(
                calendarId=cal_id,
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=15,
            ).execute().get("items", [])
            for ev in evs:
                s = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
                summ = ev.get("summary", "")
                desc = ev.get("description", "")
                consultas.append({
                    "titulo": summ,
                    "inicio": s[:16].replace("T", " "),
                    "criado_pelo_bot": ("via WhatsApp" in desc) or ("Consulta " in summ and "—" in summ),
                })
        except Exception:
            pass

    # Distribuição por cenário
    cenarios = Counter()
    cenario_labels = {
        "falso_coletivo": "Falso Coletivo",
        "multifamiliar": "Multifamiliar",
        "coletivo_adesao": "Coletivo Adesão",
        "individual": "Individual/Familiar",
        "inviavel": "Inviável",
        "indefinido": "Indefinido",
    }
    for p in profiles:
        c = classify_cenario(p)
        cenarios[cenario_labels.get(c, c)] += 1

    # Coletas multimodais (audios/imagens processados)
    multimodal = {"audios": 0, "imagens": 0}
    for p in profiles:
        multimodal["audios"] += int(p.get("_count_audio", 0))
        multimodal["imagens"] += int(p.get("_count_image", 0))

    return {
        "wa_status": wa_status,
        "api_status": api_status,
        "total_leads": metrics["total_leads"],
        "agendados": metrics["agendados"],
        "qualificando": metrics["qualificando"],
        "handoff": metrics["handoff"],
        "novos_24h": 0,
        "upcoming_consultas": consultas,
        "leads_por_dia": [{"date": k[5:], "count": v} for k, v in sorted(leads_por_dia.items())],
        "por_operadora": [{"name": k, "value": v} for k, v in operadoras.most_common(8)],
        "funil": [{"etapa": k.replace("_", " "), "count": v} for k, v in funil.most_common(10)],
        "por_modalidade": [{"name": k, "value": v} for k, v in modalidades.most_common(8)],
        "por_cenario": [{"name": k, "value": v} for k, v in cenarios.most_common()],
        "multimodal": multimodal,
    }


@app.get("/api/admin/conversations")
async def api_conversations(user: str = Depends(auth)):
    out = []
    for p in _all_profiles():
        slot = p.get("confirmed_slot") or {}
        slot_str = ""
        if isinstance(slot, dict) and slot.get("start"):
            slot_str = slot["start"][:16].replace("T", " ")
        out.append({
            "phone": p["_phone"],
            "name": p.get("name", "?"),
            "name_full": p.get("name_full", ""),
            "email": p.get("email", ""),
            "valor_atual": p.get("valor_atual", "?"),
            "operadora": p.get("operadora", "?"),
            "tipo_plano": p.get("tipo_plano", "?"),
            "stage": p["_stage"],
            "confirmed_slot_str": slot_str,
            "lead_status": p.get("lead_status", "?"),
            "last_message_at": p.get("handoff_updated_at", ""),
            "ai_summary": p.get("ai_summary", ""),
            "cenario": classify_cenario(p),
            "last_followup_day": int(p.get("last_followup_day") or 0),
        })
    out.sort(key=lambda x: x["confirmed_slot_str"] or "", reverse=True)
    return out


@app.get("/api/admin/conversations/{phone}")
async def api_conversation(phone: str, user: str = Depends(auth)):
    r = rd()
    profile_raw = r.get(f"profile:{phone}")
    profile = json.loads(profile_raw) if profile_raw else {}
    history_raw = r.get(f"history:{phone}")
    history = json.loads(history_raw) if history_raw else []
    stage = r.get(f"stage:{phone}") or "?"
    slot = profile.get("confirmed_slot") or {}
    slot_str = ""
    if isinstance(slot, dict) and slot.get("start"):
        slot_str = slot["start"][:16].replace("T", " ")
    return {
        "phone": phone,
        "profile": profile,
        "history": history,
        "stage": stage,
        "slot_str": slot_str,
        "cenario": classify_cenario(profile),
    }


@app.get("/api/admin/agenda")
async def api_agenda(days: int = 30, user: str = Depends(auth)):
    out = []
    service, cal_id, br_tz = _get_calendar_data()
    if service and cal_id:
        try:
            now = datetime.now(br_tz)
            end = now + timedelta(days=days)
            evs = service.events().list(
                calendarId=cal_id,
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=500,
            ).execute().get("items", [])
            for ev in evs:
                s = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
                e = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date", "")
                summ = ev.get("summary", "")
                desc = ev.get("description", "")
                out.append({
                    "id": ev.get("id"),
                    "titulo": summ,
                    "descricao": desc,
                    "inicio": s,
                    "fim": e,
                    "all_day": "T" not in s,
                    "criado_pelo_bot": ("via WhatsApp" in desc) or ("Consulta " in summ and "—" in summ),
                    "html_link": ev.get("htmlLink", ""),
                })
        except Exception as e:
            return JSONResponse([{"id": "", "titulo": f"Erro: {e}", "descricao": "", "inicio": "", "fim": "", "all_day": False, "criado_pelo_bot": False, "html_link": ""}])
    return out


@app.get("/api/admin/knowledge")
async def api_knowledge_list(user: str = Depends(auth)):
    files = []
    for f in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        files.append({
            "name": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m %H:%M"),
        })
    return files


@app.get("/api/admin/knowledge/{filename}")
async def api_knowledge_get(filename: str, user: str = Depends(auth)):
    path = KNOWLEDGE_DIR / filename
    if not path.exists() or not filename.endswith(".txt"):
        raise HTTPException(404)
    return {"content": path.read_text(encoding="utf-8")}


@app.post("/api/admin/knowledge/{filename}")
async def api_knowledge_save(filename: str, body: dict = Body(...), user: str = Depends(auth)):
    path = KNOWLEDGE_DIR / filename
    if not path.exists() or not filename.endswith(".txt"):
        raise HTTPException(404)
    content = body.get("content", "")
    backup = path.parent / (filename + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(content, encoding="utf-8")
    try:
        chroma_path = Path("/app/data/chroma/knowledge_index.json")
        if chroma_path.exists():
            chroma_path.unlink()
    except Exception:
        pass
    return {"saved": True, "size": len(content)}


@app.get("/api/admin/logs")
async def api_logs(user: str = Depends(auth)):
    files = [
        ("/var/log/whatsapp-watchdog.log", "Watchdog"),
        ("/var/log/whatsapp-followup.log", "Follow-up D+N (cron 1h)"),
        ("/var/log/whatsapp-reminder.log", "Lembrete reunião (cron 5min)"),
        ("/var/log/whatsapp-backup.log", "Backup auth_state"),
        ("/var/log/whatsapp-git-autocommit.log", "Auto-commit Git"),
    ]
    out = []
    for path, label in files:
        try:
            with open(path) as f:
                content = "".join(f.readlines()[-100:])
        except Exception:
            content = "(arquivo nao encontrado)"
        out.append({"label": label, "path": path, "content": content or "(vazio)"})
    return out


@app.get("/api/admin/llm-info")
async def api_llm_info(user: str = Depends(auth)):
    """Retorna config dos LLMs."""
    try:
        from app.config import get_settings
        s = get_settings()
        return {
            "primary": s.llm_primary,
            "fallback": s.llm_fallback,
            "openai_model": s.openai_model,
            "openai_model_fallback": getattr(s, "openai_model_fallback", ""),
            "openrouter_model": s.openrouter_model,
            "openai_configured": bool(s.openai_api_key),
            "openrouter_configured": bool(s.openrouter_api_key),
            "calendar_id": s.google_calendar_id,
            "lawyer_email": getattr(s, "lawyer_email", ""),
            "meeting_duration_min": s.meeting_duration_min,
            "scheduling_slots_count": s.scheduling_slots_count,
        }
    except Exception as e:
        return {"error": str(e)[:200]}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "admin-panel"}


# ============================================================
# CONTROL — endpoints reais (requer pid:host + docker.sock mount)
# ============================================================
from app.admin import control_patch  # type: ignore


@app.get("/api/admin/control/status")
async def api_control_status(user: str = Depends(auth)):
    return control_patch.action_status()


@app.post("/api/admin/control/pause")
async def api_control_pause(user: str = Depends(auth)):
    return control_patch.action_pause()


@app.post("/api/admin/control/resume")
async def api_control_resume(user: str = Depends(auth)):
    return control_patch.action_resume()


@app.post("/api/admin/control/reset")
async def api_control_reset(user: str = Depends(auth)):
    return control_patch.action_reset()


@app.get("/api/admin/control/whatsapp-logs")
async def api_control_wa_logs(tail: int = 60, user: str = Depends(auth)):
    return control_patch.action_logs_whatsapp(tail)


# =====================================================================
# Legacy HTML pages (mantem compat com painel antigo)
# =====================================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: str = Depends(auth)):
    return RedirectResponse(url="/legacy", status_code=302)


@app.get("/legacy", response_class=HTMLResponse)
async def dashboard(request: Request, user: str = Depends(auth)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "wa_status": "—",
        "api_status": "—",
        "metrics": {"total_leads": 0, "agendados": 0, "qualificando": 0, "perdidos": 0},
        "consultas": [],
        "now": _br_now().strftime("%d/%m/%Y %H:%M"),
    })
