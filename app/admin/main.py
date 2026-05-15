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


# =====================================================================
# NEW: Gestao total pela UI — Lead actions, Workers, Funnel, Env, Templates
# =====================================================================
import subprocess
import re as _re

ENV_FILE = "/root/whatsapp-agent/.env"  # bind-mounted read-only in container
TEMPLATES_FILE = Path("/app/app/knowledge/templates.json")

EDITABLE_ENV_KEYS = {
    "OPENAI_MODEL", "OPENAI_MODEL_FALLBACK", "LLM_PRIMARY", "LLM_FALLBACK",
    "MEETING_DURATION_MIN", "SCHEDULING_SLOTS_COUNT",
    "GOOGLE_CALENDAR_ID", "LAWYER_EMAIL",
    "ADMIN_USER", "ADMIN_PASS",
    "OPENROUTER_MODEL",
}

SAFE_LEAD_STATUSES = {
    "ai_active", "waiting_human", "scheduled", "won",
    "contrato_fechado", "sem_interesse", "1_2_viavel", "inviavel",
    "outbound_pending",
}


def _read_env() -> dict:
    out = {}
    try:
        for line in Path(ENV_FILE).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    except Exception:
        pass
    return out


def _write_env(updates: dict) -> bool:
    try:
        path = Path(ENV_FILE)
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        keys_seen = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if (not stripped) or stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue
            k = stripped.split("=", 1)[0].strip()
            if k in updates and k in EDITABLE_ENV_KEYS:
                new_lines.append(f"{k}={updates[k]}")
                keys_seen.add(k)
            else:
                new_lines.append(line)
        for k, v in updates.items():
            if k in EDITABLE_ENV_KEYS and k not in keys_seen:
                new_lines.append(f"{k}={v}")
        backup = Path(ENV_FILE + "." + datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak")
        if path.exists():
            backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return True
    except Exception as e:
        print("write_env err:", e)
        return False


@app.get("/api/admin/env")
async def api_env_get(user: str = Depends(auth)):
    """Retorna apenas vars editáveis, mascarando secrets."""
    env = _read_env()
    out = {}
    for k in EDITABLE_ENV_KEYS:
        v = env.get(k, "")
        out[k] = v if k != "ADMIN_PASS" else ("●" * min(len(v), 8))
    return out


@app.post("/api/admin/env")
async def api_env_set(body: dict = Body(...), user: str = Depends(auth)):
    updates = {k: str(v) for k, v in body.items() if k in EDITABLE_ENV_KEYS}
    if not updates:
        raise HTTPException(400, "Nenhuma chave editável fornecida")
    # Não sobrescreve ADMIN_PASS se vier mascarado
    if "ADMIN_PASS" in updates and set(updates["ADMIN_PASS"]) == {"●"}:
        updates.pop("ADMIN_PASS")
    ok = _write_env(updates)
    if not ok:
        raise HTTPException(500, "Falha ao escrever .env")
    return {"saved": True, "keys": list(updates.keys()), "note": "Reinicie containers para aplicar"}


# ---- Templates de mensagens (followup + pos-reuniao) ------------------

DEFAULT_TEMPLATES = {
    "followup": {
        "1": "Olá! Tudo bem? Conseguiu ver minha mensagem? Seu reajuste pode estar acima do permitido.",
        "3": "Muitas pessoas só descobrem que o reajuste é abusivo depois de meses pagando. Quer verificar o seu hoje?",
        "5": "Posso te enviar um resumo simples de como funciona esse pedido de revisão?",
        "7": "Quer que eu veja horários para nossa consulta?",
        "10": "Hoje estamos finalizando os horários dessa semana para análise de reajuste. Quer que eu reserve uma vaga para você agora ou prefere que eu te procure em outro momento?",
        "13": "{nome}, caso mude de ideia, estamos à disposição. Basta me chamar aqui. Boa sorte!",
    },
    "post_meeting": {
        "1": "Oi, {nome}. Tudo bem?\n\nGostaria de reforçar um ponto importante: seu caso realmente apresenta fundamentos sólidos para revisão do reajuste.\n\nSe fizer sentido para você, já podemos seguir com os próximos passos ainda essa semana.",
        "2": "Olá, {nome}.\n\nVocê conseguiu avaliar com calma tudo o que conversamos na reunião?\n\nSe quiser, posso te relembrar de forma objetiva os benefícios práticos de iniciar agora.",
        "3": "{nome}, queria te fazer uma pergunta direta:\n\nQuanto você ainda pretende pagar a mais aguardando para decidir?\n\nQuanto antes iniciarmos, antes você interrompe esse impacto financeiro.",
        "4": "Quero reforçar algo importante:\n\nA ação serve justamente para proteger seu contrato e evitar qualquer risco de cancelamento enquanto discutimos o reajuste.\n\nSe essa era uma preocupação sua, pode ficar tranquilo.\n\nQuer que a gente avance?",
        "5": "{nome}, estou organizando os casos que vão avançar essa semana.\n\nPrefere que eu já reserve sua entrada agora ou quer retomar em outro momento específico?",
        "6": "Posso facilitar para você:\n\nPrefere que eu envie novamente o link para assinatura do contrato ou quer que eu te ligue para alinharmos rapidamente?",
        "7": "{nome}, deixo essa como minha última mensagem por agora para respeitar seu tempo.\n\nQuando decidir seguir com a revisão do plano, é só me avisar que retomamos imediatamente.\n\nEstou à disposição.",
    },
}


def _load_templates() -> dict:
    try:
        if TEMPLATES_FILE.exists():
            return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULT_TEMPLATES


def _save_templates(data: dict) -> bool:
    try:
        TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
        if TEMPLATES_FILE.exists():
            backup = TEMPLATES_FILE.with_suffix(".json.bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
            backup.write_text(TEMPLATES_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        TEMPLATES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        print("save_templates err:", e)
        return False


@app.get("/api/admin/templates")
async def api_templates_get(user: str = Depends(auth)):
    return _load_templates()


@app.post("/api/admin/templates")
async def api_templates_set(body: dict = Body(...), user: str = Depends(auth)):
    current = _load_templates()
    for section in ("followup", "post_meeting"):
        if section in body and isinstance(body[section], dict):
            current[section] = {str(k): str(v) for k, v in body[section].items()}
    ok = _save_templates(current)
    if not ok:
        raise HTTPException(500, "Falha ao salvar templates")
    return {"saved": True}


# ---- Acoes por lead --------------------------------------------------

@app.post("/api/admin/leads/{phone}/status")
async def api_lead_status(phone: str, body: dict = Body(...), user: str = Depends(auth)):
    new_status = str(body.get("lead_status", "")).strip()
    if new_status not in SAFE_LEAD_STATUSES:
        raise HTTPException(400, f"Status invalido. Aceitos: {sorted(SAFE_LEAD_STATUSES)}")
    r = rd()
    raw = r.get(f"profile:{phone}")
    if not raw:
        raise HTTPException(404, "Lead nao encontrado")
    profile = json.loads(raw)
    profile["lead_status"] = new_status
    profile["lead_status_updated_at"] = _br_now().isoformat()
    profile["lead_status_updated_by"] = user
    r.set(f"profile:{phone}", json.dumps(profile))
    return {"phone": phone, "lead_status": new_status}


@app.post("/api/admin/leads/{phone}/pause")
async def api_lead_pause(phone: str, body: dict = Body(default={}), user: str = Depends(auth)):
    """Pausa a IA somente para este lead (handoff humano)."""
    reason = str(body.get("reason", "manual via admin"))
    r = rd()
    raw = r.get(f"profile:{phone}")
    if not raw:
        raise HTTPException(404)
    profile = json.loads(raw)
    profile["lead_status"] = "waiting_human"
    profile["handoff_requested"] = True
    profile["handoff_reason"] = reason
    profile["handoff_updated_at"] = _br_now().isoformat()
    r.set(f"profile:{phone}", json.dumps(profile))
    return {"phone": phone, "paused": True}


@app.post("/api/admin/leads/{phone}/resume")
async def api_lead_resume(phone: str, user: str = Depends(auth)):
    r = rd()
    raw = r.get(f"profile:{phone}")
    if not raw:
        raise HTTPException(404)
    profile = json.loads(raw)
    profile["lead_status"] = "ai_active"
    profile["handoff_requested"] = False
    profile["handoff_reason"] = ""
    profile["handoff_updated_at"] = _br_now().isoformat()
    r.set(f"profile:{phone}", json.dumps(profile))
    return {"phone": phone, "resumed": True}


@app.post("/api/admin/leads/{phone}/send")
async def api_lead_send(phone: str, body: dict = Body(...), user: str = Depends(auth)):
    """Envia mensagem manual via whatsapp-service e adiciona ao histórico."""
    msg = str(body.get("message", "")).strip()
    if not msg:
        raise HTTPException(400, "Mensagem vazia")
    # 1) Envia
    sent_ok = False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{WHATSAPP_URL}/send", json={"phone": phone, "message": msg})
            sent_ok = r.status_code == 200
    except Exception as e:
        raise HTTPException(502, f"Falha ao enviar: {e}")
    if not sent_ok:
        raise HTTPException(502, "whatsapp-service retornou erro")
    # 2) Adiciona ao history
    rds = rd()
    hist_raw = rds.get(f"history:{phone}") or "[]"
    try:
        hist = json.loads(hist_raw)
    except Exception:
        hist = []
    hist.append({
        "role": "assistant",
        "content": msg,
        "ts": _br_now().isoformat(),
        "manual_by": user,
    })
    rds.set(f"history:{phone}", json.dumps(hist))
    return {"phone": phone, "sent": True}


# ---- Funil de conversao ----------------------------------------------

@app.get("/api/admin/funnel")
async def api_funnel(user: str = Depends(auth)):
    profiles = _all_profiles()
    total = len(profiles)
    qualificados = sum(1 for p in profiles if classify_cenario(p) in {"falso_coletivo", "multifamiliar", "coletivo_adesao", "individual"})
    agendados = sum(1 for p in profiles if p.get("confirmed_slot"))
    concluidos = sum(1 for p in profiles if p.get("lead_status") in {"won", "contrato_fechado"})
    pos_reuniao = sum(1 for p in profiles if int(p.get("post_meeting_day") or 0) > 0)
    perdidos = sum(1 for p in profiles if p.get("lead_status") == "sem_interesse")
    return {
        "etapas": [
            {"label": "Total Leads", "value": total},
            {"label": "Qualificados", "value": qualificados},
            {"label": "Agendados", "value": agendados},
            {"label": "Pós-Reunião", "value": pos_reuniao},
            {"label": "Fechados", "value": concluidos},
        ],
        "perdidos": perdidos,
        "conversao_total": round((concluidos / total * 100), 1) if total else 0.0,
        "conversao_agendamento": round((agendados / total * 100), 1) if total else 0.0,
        "conversao_fechamento": round((concluidos / agendados * 100), 1) if agendados else 0.0,
    }


# ---- Workers / Cron --------------------------------------------------

@app.get("/api/admin/workers")
async def api_workers(user: str = Depends(auth)):
    """Lista cron jobs com último log e status estimado."""
    jobs = [
        {"name": "Watchdog WhatsApp", "schedule": "*/2 * * * *", "log": "/var/log/whatsapp-watchdog.log", "script": "watchdog.sh"},
        {"name": "Follow-up D+1..D+13", "schedule": "0 * * * *", "log": "/var/log/whatsapp-followup.log", "script": "followup_worker.sh"},
        {"name": "Pós-reunião Dia 1..7", "schedule": "0 10 * * *", "log": "/var/log/post_meeting.log", "script": "post_meeting_worker.sh"},
        {"name": "Lembrete 30min antes", "schedule": "*/5 * * * *", "log": "/var/log/whatsapp-reminder.log", "script": "reminder_worker.sh"},
        {"name": "Backup auth_state", "schedule": "0 4 * * *", "log": "/var/log/whatsapp-backup.log", "script": "backup_auth.sh"},
        {"name": "Auto-commit Git", "schedule": "0 5 * * *", "log": "/var/log/whatsapp-git-autocommit.log", "script": "auto_commit.sh"},
        {"name": "DuckDNS update", "schedule": "*/5 * * * *", "log": "", "script": "duckdns"},
    ]
    out = []
    for j in jobs:
        last_line = ""
        last_mod = ""
        size = 0
        try:
            if j["log"]:
                p = Path(j["log"])
                if p.exists():
                    size = p.stat().st_size
                    last_mod = datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")
                    tail = p.read_text(encoding="utf-8", errors="replace").splitlines()
                    if tail:
                        last_line = tail[-1][:300]
        except Exception:
            pass
        out.append({**j, "last_line": last_line, "last_mod": last_mod, "log_size": size})
    return out

