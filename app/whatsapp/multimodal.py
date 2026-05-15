"""Endpoints multimodais: Whisper (áudio) + Vision (imagem). Starlette puro."""
from __future__ import annotations

import base64
import json
import logging
import os
import tempfile

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)


async def transcribe_audio(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "JSON inválido"}, status_code=400)

    settings = get_settings()
    if not settings.openai_api_key:
        return JSONResponse({"detail": "OPENAI_API_KEY ausente"}, status_code=500)

    audio_b64 = body.get("audio_base64", "")
    mime = body.get("mime", "audio/ogg")
    ext = mime.split("/")[-1].split(";")[0] or "ogg"

    if not audio_b64:
        return JSONResponse({"detail": "audio_base64 obrigatório"}, status_code=400)

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        return JSONResponse({"detail": "base64 inválido"}, status_code=400)

    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            with open(tmp_path, "rb") as f:
                audio_data = f.read()
            files = {"file": (f"audio.{ext}", audio_data, mime)}
            data = {"model": "whisper-1", "language": "pt"}
            r = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                files=files,
                data=data,
            )
            r.raise_for_status()
            text = r.json().get("text", "").strip()
            return JSONResponse({"ok": True, "text": text})
    except httpx.HTTPStatusError as e:
        logger.error("whisper falhou: %s", e.response.text[:300])
        return JSONResponse({"detail": f"Whisper {e.response.status_code}"}, status_code=502)
    except Exception as e:
        logger.exception("whisper exception")
        return JSONResponse({"detail": str(e)[:300]}, status_code=500)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


async def extract_image(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "JSON inválido"}, status_code=400)

    settings = get_settings()
    if not settings.openai_api_key:
        return JSONResponse({"detail": "OPENAI_API_KEY ausente"}, status_code=500)

    image_b64 = body.get("image_base64", "")
    mime = body.get("mime", "image/jpeg")
    if not image_b64:
        return JSONResponse({"detail": "image_base64 obrigatório"}, status_code=400)

    system_prompt = (
        "Você é um extrator de dados. O cliente envia foto de boleto, "
        "contrato ou comunicado de plano de saúde. Extraia em JSON:\n"
        "- operadora (string)\n"
        "- valor_atual (string, só o número)\n"
        "- tipo_plano (individual/familiar/coletivo por adesão/coletivo empresarial/null)\n"
        "- data_adesao (string ou null)\n"
        "- percentual_reajuste (string ou null)\n"
        "- observacoes (1 frase com detalhes importantes)\n\n"
        "Responda APENAS JSON puro, sem ```json. Use null se não souber."
    )

    user_content = [
        {"type": "text", "text": "Extraia os dados desta imagem do plano de saúde."},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
    ]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 400,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                },
            )
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            try:
                cleaned = text.replace("```json", "").replace("```", "").strip()
                extracted = json.loads(cleaned)
            except Exception:
                extracted = {}
            return JSONResponse({"ok": True, "text": text, "extracted": extracted})
    except httpx.HTTPStatusError as e:
        logger.error("vision falhou: %s", e.response.text[:300])
        return JSONResponse({"detail": f"Vision {e.response.status_code}"}, status_code=502)
    except Exception as e:
        logger.exception("vision exception")
        return JSONResponse({"detail": str(e)[:300]}, status_code=500)
