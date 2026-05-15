"""Controle real com lógica de estado funcional.

Estados retornados (campo bot_state):
- "paused"     -> container parado
- "waiting_qr" -> container rodando, WhatsApp esperando scan
- "active"     -> container rodando + WhatsApp connected
- "error"      -> container rodando mas WhatsApp não responde
- "missing"    -> container não existe
"""
import os
import signal
import subprocess
import time
import json as _json
import urllib.request


WHATSAPP_NAME = "whatsapp-agent_whatsapp_1"
WHATSAPP_INTERNAL_URL = "http://whatsapp:3001/status"


def _docker(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = subprocess.run(["docker"] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return 127, "", "docker CLI not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def _container_state(name: str) -> dict:
    rc, out, _ = _docker(["inspect", "--format", "{{.State.Status}}|{{.State.Pid}}", name])
    if rc != 0:
        return {"status": "missing", "pid": 0}
    parts = out.split("|")
    return {"status": parts[0], "pid": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0}


def _force_kill_pid(pid: int) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, signal.SIGKILL)
        return True
    except ProcessLookupError:
        return True
    except PermissionError:
        return False


def _wa_status() -> str | None:
    try:
        with urllib.request.urlopen(WHATSAPP_INTERNAL_URL, timeout=3) as r:
            return _json.loads(r.read().decode()).get("status")
    except Exception:
        return None


def _compute_bot_state(container_status: str, wa_status: str | None) -> tuple[str, str]:
    if container_status == "missing":
        return "missing", "Container não existe"
    if container_status in ("exited", "dead"):
        return "paused", "Pausado — bot não recebe mensagens"
    if container_status != "running":
        return "error", f"Estado anômalo: {container_status}"
    if wa_status == "connected":
        return "active", "Ativo — bot atendendo normalmente"
    if wa_status == "waiting":
        return "waiting_qr", "Aguardando escaneamento do QR Code"
    if wa_status is None:
        return "error", "WhatsApp não responde (sessão pode estar corrompida)"
    return "error", f"Estado WhatsApp: {wa_status}"


def action_status() -> dict:
    containers = {}
    for name in [WHATSAPP_NAME, "whatsapp-agent-api-1", "whatsapp-agent-redis-1"]:
        containers[name] = _container_state(name)
    wa_cs = containers[WHATSAPP_NAME]["status"]
    wa_app = _wa_status() if wa_cs == "running" else None
    state, label = _compute_bot_state(wa_cs, wa_app)
    return {
        "containers": containers,
        "bot_state": state,
        "bot_state_label": label,
        "wa_app_status": wa_app,
    }


def action_pause() -> dict:
    state = _container_state(WHATSAPP_NAME)
    if state["status"] != "running":
        return {"ok": True, "msg": f"Bot já estava {state['status']}", "state": action_status()}
    _docker(["update", "--restart=no", WHATSAPP_NAME])
    _force_kill_pid(state["pid"])
    time.sleep(3)
    s = action_status()
    return {"ok": s["bot_state"] == "paused", "msg": s["bot_state_label"], "state": s}


def action_resume() -> dict:
    rc, _, err = _docker(["start", WHATSAPP_NAME])
    if rc != 0:
        return {"ok": False, "msg": f"docker start falhou: {err}", "state": action_status()}
    _docker(["update", "--restart=unless-stopped", WHATSAPP_NAME])
    for _ in range(25):
        time.sleep(1)
        s = action_status()
        if s["bot_state"] in ("active", "waiting_qr"):
            return {"ok": True, "msg": s["bot_state_label"], "state": s}
    return {"ok": False, "msg": "Container subiu mas WhatsApp ainda inicializando…", "state": action_status()}


def action_reset() -> dict:
    state = _container_state(WHATSAPP_NAME)
    if state["pid"]:
        _docker(["update", "--restart=no", WHATSAPP_NAME])
        _force_kill_pid(state["pid"])
        time.sleep(3)
    _docker(["rm", "-f", WHATSAPP_NAME])
    _docker(["volume", "rm", "whatsapp-agent_whatsapp_auth"])
    _docker(["compose", "-f", "/root/whatsapp-agent/docker-compose.yml", "up", "-d", "--no-deps", "whatsapp"], timeout=120)
    time.sleep(8)
    # rename automatico do compose v2
    _, names, _ = _docker(["ps", "--filter", "label=com.docker.compose.service=whatsapp", "--format", "{{.Names}}"])
    if names and names != WHATSAPP_NAME:
        _docker(["rename", names, WHATSAPP_NAME])
    for _ in range(25):
        time.sleep(1)
        s = action_status()
        if s["bot_state"] in ("waiting_qr", "active"):
            return {"ok": True, "msg": s["bot_state_label"], "state": s}
    return {"ok": False, "msg": "Recriado, aguarde alguns segundos…", "state": action_status()}


def action_logs_whatsapp(tail: int = 60) -> dict:
    rc, out, err = _docker(["logs", "--tail", str(tail), WHATSAPP_NAME])
    return {"ok": rc == 0, "logs": out or err}
