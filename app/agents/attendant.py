"""Main attendant agent - orchestrates the full conversation flow."""

import logging
import re
from datetime import datetime

from app.agents.cenario import classify_cenario, diagnostic_message, is_viable
from app.agents.router import (
    BUSINESS_DAYS,
    BUSINESS_HOUR_END,
    BUSINESS_HOUR_START,
    DateTimeInfo,
    IntentRouter,
    extract_datetime,
)
from app.memory.user_memory import (
    get_user_profile,
    save_user_profile,
    get_chat_history,
    add_to_history,
    get_stage,
    set_stage,
)
from app.agents.scheduling_intent import extract_scheduling_preference
from app.outbound.service import sync_outbound_state_after_stage_change
from app.rag.chain import generate_response
from app.scheduling.oncehub import (
    confirm_and_book,
    fetch_suggestion_message,
    format_confirmation_message,
    get_scheduling_message,
    parse_slot_choice,
)

logger = logging.getLogger(__name__)

WEEKDAYS_PT = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
QUALIFICATION_FIELD_LABELS = {
    "valor atual do plano": ("valor_atual",),
    "operadora": ("operadora",),
    "modalidade (individual, familiar, coletivo por adesão ou empresarial)": ("tipo_plano",),
    "se os beneficiários são todos da mesma família": ("beneficiarios_familia",),
    "ano de contratação do plano": ("data_adesao",),
}
MINIMUM_QUALIFICATION_KEYS = (
    "operadora",
    "tipo_plano",
    "valor_atual",
    "data_adesao",
    "beneficiarios_familia",
)
COST_QUESTION_PATTERNS = (
    r"\b(?:tem\s+(?:algum\s+)?(?:custo|preco|valor)|quanto\s+(?:custa|sai|fica|cobra)|"
    r"\bcobra(?:m|ria)?\b|valor\s+da\s+consulta|preco\s+da\s+consulta|"
    r"honor[aá]rios?|porcentagem|fee\s+de\s+[eê]xito|sinal\s+inicial|"
    r"qual\s+o\s+valor|qual\s+o\s+preco|qual\s+o\s+custo|"
    r"\b[eé]\s+gratuit[oa]\b|\b[eé]\s+gr[aá]tis\b|\bsem\s+custo\b|"
    r"vou\s+pagar\s+quanto|tenho\s+que\s+pagar)\b",
)

META_RESPONSE_PATTERNS = (
    r"^\s*\(.*(?:usei|t[eé]cnica|gatilho|cta|call[- ]to[- ]action|mensagem curta|"
    r"foco na solu[cç][aã]o|linguagem simples|alternativas controladas|"
    r"confirma[cç][aã]o de viabilidade).*\)\s*$",
    # Comentarios meta entre parenteses como "(Nota: ...)", "(Mantive ...)", "(Seguindo ...)"
    r"^\s*\(\s*(?:nota|obs|observa[cç][aã]o|coment[aá]rio|aviso|mantive|segui|seguindo|conforme|de acordo|orienta[cç][aã]o|orienta[cç][oõ]es|aten[cç][aã]o ao tom|de forma|usei a)\s*[:\-,].*\)\s*$",
    # Linhas inteiras de meta-comentario fora de parenteses
    r"^\s*(?:nota|observa[cç][aã]o|coment[aá]rio)\s*[:\-]\s*.*$",
    r"^\s*usei\s+.*$",
    r"^\s*observa[cç][oõ]es?\s+estrat[eé]gicas?:?\s*$",
    # "(mantive o tom XXX, conforme orientacoes)" e variantes
    r"^\s*\(.*?conforme orienta[cç][oõ]es.*?\)\s*$",
    r"^\s*\(.*?seguindo a?s? orienta[cç][oõ]es.*?\)\s*$",
)
HUMAN_HANDOFF_PATTERNS = (
    r"\batendente\b",
    r"\bhumano\b",
    r"\balgu[eé]m da equipe\b",
    r"\bfalar com (?:uma )?pessoa\b",
    r"\bfalar com (?:um )?atendente\b",
    r"\bquero falar com (?:um )?humano\b",
    r"\bme liga\b",
    r"\bme ligue\b",
    r"\bliga pra mim\b",
)
CONSULTIVE_INVITE_PATTERNS = (
    r"\bvc tira d[uú]vidas\b",
    r"\bvoc[eê] tira d[uú]vidas\b",
    r"\btira(?:r)? d[uú]vidas\b",
    r"\btenho (?:uma )?d[uú]vida\b",
    r"\bposso perguntar\b",
)
SOFTENING_REPLACEMENTS = (
    (r"\bclaramente abusiv[oa]\b", "com sinais de possível abuso"),
    (r"\bhá indícios fortes de abusividade\b", "há sinais que merecem análise cuidadosa"),
    (r"\bhá fortes indícios de abusividade\b", "há sinais que merecem análise cuidadosa"),
    (r"\bhá indícios fortes\b", "há indícios relevantes"),
    (
        r"\ba ação serve justamente para proteger seu contrato e evitar qualquer risco de cancelamento\b",
        "a análise busca avaliar medidas para preservar seu contrato e reduzir riscos durante a discussão",
    ),
    (
        r"\ba ação jurídica serve justamente para proteger seu contrato\b",
        "a análise jurídica busca avaliar medidas para preservar seu contrato",
    ),
    (
        r"\ba ação judicial justamente busca proteger seu contrato\b",
        "a análise jurídica busca avaliar medidas para preservar seu contrato",
    ),
    (
        r"\ba ação serve justamente para proteger seu contrato\b",
        "a análise busca avaliar medidas para preservar seu contrato",
    ),
    (
        r"\ba maioria das decisões judiciais até proíbe a operadora de cancelar o plano durante o processo\b",
        "em muitos casos, existem medidas que ajudam a reduzir esse risco enquanto a situação é analisada",
    ),
    (
        r"\bsem colocar o contrato em risco\b",
        "buscando reduzir riscos ao contrato",
    ),
    (
        r"\bprotegem seu contrato e reduzem riscos\b",
        "podem ajudar a preservar seu contrato e reduzir riscos",
    ),
    (r"\bcom certeza podemos ajudar a reverter\b", "podemos analisar com cuidado"),
    (r"\bcom certeza podemos ajudar\b", "podemos avaliar o cenário com cuidado"),
    (r"\bcom certeza\b", "ao que tudo indica"),
    (r"\bprecisamos marcar uma consulta rápida\b", "o próximo passo pode ser uma consulta rápida"),
    (r"\bna minha experiência, planos desse período têm boas chances de revisão\b", "em muitos casos, planos desse período merecem uma análise cuidadosa"),
    (r"\btem boas chances de revisão\b", "merece uma análise cuidadosa"),
    (r"\bestá muito acima da média\b", "merece uma análise cuidadosa"),
    (r"\bcomo podemos buscar uma redução desse valor\b", "quais caminhos podem ser analisados no seu caso"),
    (r"\bte mostrar quanto pode ser reduzido\b", "te explicar quais caminhos podem fazer sentido"),
    (r"\bquanto desse aumento pode ser revertido\b", "quais caminhos podem fazer sentido para analisar esse aumento"),
    (r"\bverificar se esse reajuste foi abusivo\b", "verificar se esse reajuste pode ser questionado"),
    (r"\btem grande potencial de redução\b", "merece uma análise cuidadosa"),
    (r"\btem ótimas chances de reverter esse valor\b", "tem bons elementos para análise"),
    (r"\btem ótimas chances\b", "tem bons indícios"),
    (r"\bpodemos ajudar a reverter isso\b", "podemos analisar esse cenário"),
    (r"\bmelhor estratégia para reverter esse aumento\b", "melhor forma de analisar esse aumento"),
    (r"\bmelhor estratégia para questionar esse aumento\b", "melhor forma de analisar esse aumento"),
    (r"\bmelhor estratégia\b", "melhor caminho"),
    (r"\bavaliar as melhores estratégias para\b", "avaliar com calma caminhos possíveis, como"),
    (r"\breduzir o valor do plano\b", "ver se o reajuste pode ser revisto"),
    (r"\bpreservar sua cobertura\b", "entender os cuidados com a cobertura"),
    (r"\bmantenham a cobertura ativa\b", "ajudem a preservar a cobertura"),
    (r"\bevitem qualquer risco de cancelamento\b", "reduzam riscos durante a discussão"),
    (r"\bgarantam seus direitos\b", "busquem resguardar seus direitos"),
    (r"\bgarantir que tudo seja feito dentro da legalidade\b", "conduzir tudo com segurança jurídica"),
    (
        r"\bcomo proteger seu plano enquanto busca a revisão desse aumento\b",
        "os cuidados com o contrato enquanto esse aumento é analisado",
    ),
    (
        r"\bsem prejudicar a continuidade do plano\b",
        "considerando os cuidados com a continuidade do plano",
    ),
    (
        r"\bquer que eu reserve um horário\b",
        "Quer que eu te envie um horário disponível",
    ),
    (
        r"\bexatamente como isso funciona na prática\b",
        "com calma como isso pode funcionar no seu caso",
    ),
    (
        r"\bposso reservar um horário para você hoje mesmo\b",
        "posso te enviar um horário disponível hoje mesmo",
    ),
    (
        r"\bsem prejudicar seu plano\b",
        "com os cuidados adequados para o seu plano",
    ),
    (
        r"\bnormalmente, quando entramos com o pedido, solicitamos também medidas preventivas para evitar qualquer risco de cancelamento enquanto o caso é analisado\b",
        "quando necessário, a equipe avalia medidas para reduzir riscos enquanto o caso é analisado",
    ),
    (
        r"\bcomo podemos agir com segurança\b",
        "quais caminhos podem fazer sentido no seu caso",
    ),
    (r"\bvalor acima do justo\b", "valor que pode merecer revisão"),
    (r"\breverter esse valor\b", "questionar esse reajuste"),
    (r"\breduzir significativamente os valores\b", "buscar uma redução dos valores"),
    (r"\bquanto você pode economizar\b", "qual pode ser o melhor caminho para o seu caso"),
    (r"\bvalor justo\b", "valor mais adequado"),
)



EMAIL_RE = re.compile(r"\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b")


def _parse_nome_email(text: str) -> tuple[str | None, str | None]:
    """Extrai nome completo e email de uma mensagem."""
    email_match = EMAIL_RE.search(text)
    email = email_match.group(0) if email_match else None
    # remove email do texto pra capturar nome
    text_wo = text.replace(email, "") if email else text
    # remove pontuação comum
    text_wo = re.sub(r"[\\n,;]+", " ", text_wo).strip()
    # nome = sequência de palavras com letras (pega 2+ palavras pra ser nome completo)
    name_match = re.search(r"[A-Za-zÀ-ÿ]+(?:\\s+[A-Za-zÀ-ÿ]+){1,}", text_wo)
    name = name_match.group(0).strip() if name_match else None
    return name, email



class AttendantAgent:
    """Orchestrates the WhatsApp conversation flow for Andrade & Lemos."""

    def __init__(self):
        self.router = IntentRouter()

    async def process_message(
        self, phone: str, name: str, text: str
    ) -> dict:
        """Process an incoming message and return the response with metadata."""
        # 1. Load user state
        profile = await get_user_profile(phone)
        if name and not profile.get("name"):
            profile["name"] = name
        current_stage = await get_stage(phone)
        history = await get_chat_history(phone)

        if not history and self.router.classify_intent(text) == "greeting":
            response = self._build_first_contact_response(profile.get("name", ""))
            await add_to_history(phone, "user", text)
            await save_user_profile(phone, profile)
            await set_stage(phone, current_stage)
            await add_to_history(phone, "assistant", response)
            return {"reply": response, "stage": current_stage, "intent": "greeting"}

        if self._is_human_handoff_request(text):
            profile["handoff_requested"] = True
            profile["handoff_reason"] = self._infer_handoff_reason(text)
            profile["handoff_updated_at"] = datetime.now().isoformat()
            profile["lead_status"] = "waiting_human"
            profile["ai_summary"] = self._build_lead_summary(profile, current_stage, history, text)

            response = self._build_handoff_response(profile.get("name", ""))
            await add_to_history(phone, "user", text)
            await save_user_profile(phone, profile)
            await set_stage(phone, current_stage)
            await add_to_history(phone, "assistant", response)
            return {"reply": response, "stage": current_stage, "intent": "human_handoff"}

        # 2a. Pergunta sobre custo -> deflexao deterministica
        if self._is_cost_question(text):
            response = self._build_cost_deflection_response(profile.get("name", ""))
            await add_to_history(phone, "user", text)
            await save_user_profile(phone, profile)
            await set_stage(phone, current_stage)
            await add_to_history(phone, "assistant", response)
            return {"reply": response, "stage": current_stage, "intent": "cost_question"}

        # 2. Classify intent and extract data
        intent = self.router.classify_intent(text)
        objection_type = self.router.detect_objection_type(text)
        qual_data = self.router.extract_qualification_data(text)

        if self._is_consultive_invite_request(text):
            response = self._build_consultive_invite_response(profile.get("name", ""))
            await add_to_history(phone, "user", text)
            await save_user_profile(phone, profile)
            await set_stage(phone, current_stage)
            await add_to_history(phone, "assistant", response)
            return {"reply": response, "stage": current_stage, "intent": "consultive"}

        # 3. Extract date/time from message
        dt_info = extract_datetime(text)
        scheduling_context = self._build_scheduling_context(dt_info)

        # 4. Update profile with extracted data
        if qual_data:
            for key, value in qual_data.items():
                if key == "valores_mencionados":
                    # so seta valor_atual se ainda nao tiver (evita sobrescrever com ano de adesao etc)
                    if value and not profile.get("valor_atual"):
                        profile["valor_atual"] = value[-1]
                else:
                    # nao sobrescreve campos ja preenchidos (exceto se vier vazio)
                    if value and not profile.get(key):
                        profile[key] = value

        # Save detected datetime preference in profile
        if dt_info and dt_info.is_valid:
            profile["preferred_datetime"] = dt_info.format_display()

        # 5. Determine stage transition
        new_stage = self._resolve_stage(current_stage, intent, profile)

        missing_fields = self._get_missing_fields(profile)
        recently_requested_fields = self._infer_recently_requested_fields(history)
        slot_suggestions: list[str] = []
        conversation_guidance = self._build_conversation_guidance(
            text=text,
            profile=profile,
            history=history,
            intent=intent,
            dt_info=dt_info,
            current_stage=new_stage,
            missing_fields=missing_fields,
            recently_requested_fields=recently_requested_fields,
            slot_suggestions=slot_suggestions,
        )

        # 6. Save user message to history
        await add_to_history(phone, "user", text)

        # 7. Build collected data summary
        collected = self._format_collected_data(profile)

        # 8. Generate RAG-powered response with scheduling context
        response = await generate_response(
            user_message=text,
            user_name=profile.get("name", ""),
            user_phone=phone,
            current_stage=new_stage,
            collected_data=collected,
            chat_history=history,
            scheduling_context=scheduling_context,
            conversation_guidance=conversation_guidance,
        )

        allow_scheduling_link = self._should_offer_scheduling_link(profile, new_stage)
        if (
            new_stage == "oferta_consulta"
            and current_stage in {"abordagem_inicial", "qualificacao"}
            and self._has_minimum_qualification(profile)
        ):
            response = f"{self._build_offer_consulta_response(profile.get('name', ''), profile, slot_suggestions)}\n\n[AGENDAR]"
        elif intent == "objection" and objection_type == "cancellation_fear" and allow_scheduling_link:
            response = self._build_cancellation_fear_response(profile.get("name", ""), slot_suggestions)
        elif intent == "scheduling" and allow_scheduling_link and self._is_out_of_hours_request(dt_info):
            response = self._build_out_of_hours_response(profile.get("name", ""), slot_suggestions)
        elif intent == "scheduling" and allow_scheduling_link and dt_info and dt_info.is_valid and dt_info.is_business_hours:
            response = self._build_in_hours_scheduling_response(profile.get("name", ""), dt_info)

        # 9. Handle scheduling — fluxo conversacional via Google Calendar
        response = response.replace("[AGENDAR]", "").strip()
        booking_completed = False
        nome = profile.get("name", "")
        pending_slots = profile.get("pending_slots") or []

        # 9a. Cliente escolheu slot -> primeiro pede nome+email, depois cria evento
        if (
            allow_scheduling_link
            and pending_slots
            and not profile.get("confirmed_slot")
        ):
            # Se já estamos esperando nome+email
            if profile.get("awaiting_name_email"):
                parsed_name, parsed_email = _parse_nome_email(text)
                if parsed_email:
                    profile["name_full"] = parsed_name or profile.get("name", "")
                    profile["email"] = parsed_email
                    profile["awaiting_name_email"] = False
                    chosen = profile.get("chosen_slot")
                    if chosen:
                        try:
                            event = await confirm_and_book(
                                chosen,
                                profile.get("name_full") or profile.get("name", ""),
                                phone,
                            )
                            profile["confirmed_slot"] = chosen
                            profile["calendar_event_id"] = event.get("id")
                            profile["pending_slots"] = []
                            profile.pop("chosen_slot", None)
                            response = format_confirmation_message(
                                chosen, profile.get("name_full") or nome
                            )
                            new_stage = "confirmacao_consulta"
                            booking_completed = True
                        except Exception as exc:
                            logger.exception("Falha ao criar evento: %s", exc)
                            response = (
                                f"{nome + ', ' if nome else ''}tive um problema técnico. "
                                "Vou pedir para alguém da equipe finalizar. Pode aguardar?"
                            )
                else:
                    # Email não veio, pede de novo
                    response = (
                        f"{nome + ', ' if nome else ''}preciso do seu nome completo e email "
                        "para confirmar a reunião. Pode enviar?"
                    )
                    booking_completed = True  # bloqueia outras lógicas

            else:
                chosen = parse_slot_choice(text, pending_slots)
                if chosen:
                    # Em vez de criar evento direto, pede nome+email primeiro (conforme doc)
                    profile["awaiting_name_email"] = True
                    profile["chosen_slot"] = chosen
                    response = (
                        f"{nome + ', ' if nome else ''}ótimo! Para confirmar, "
                        "envie-me seu nome completo e email, por gentileza."
                    )
                    booking_completed = True

        # 9b. Hora de oferecer slots (com preferência do cliente)
        if (
            not booking_completed
            and allow_scheduling_link
            and not profile.get("confirmed_slot")
            and intent in {"scheduling", "confirmation"}
        ):
            try:
                pref = extract_scheduling_preference(text)
                shown_history = profile.get("shown_slots") or []
                msg, slots = await fetch_suggestion_message(
                    nome,
                    preference=pref if pref.has_any() else None,
                    exclude=shown_history,
                )
                if slots:
                    new_slots = [
                        {"start": s.start.isoformat(), "end": s.end.isoformat()}
                        for s in slots
                    ]
                    profile["pending_slots"] = new_slots
                    # acumula slots ja mostrados para nao repetir em proximas sugestoes
                    profile["shown_slots"] = (shown_history + new_slots)[-10:]
                    response = msg
                else:
                    response = msg or response
            except Exception as exc:
                logger.exception("Falha ao buscar slots na agenda: %s", exc)

        response = self._normalize_response(response)

        profile["lead_status"] = self._determine_lead_status(profile, new_stage)
        profile["ai_summary"] = self._build_lead_summary(profile, new_stage, history, text)
        await sync_outbound_state_after_stage_change(phone, profile, new_stage)

        # 10. Save state
        await save_user_profile(phone, profile)
        await set_stage(phone, new_stage)
        await add_to_history(phone, "assistant", response)

        return {"reply": response, "stage": new_stage, "intent": intent}

    def _build_scheduling_context(self, dt_info: DateTimeInfo | None) -> str:
        """Build scheduling context string for the LLM based on detected datetime."""
        if not dt_info:
            return ""

        parts = []

        if dt_info.is_valid:
            parts.append(f"DATA/HORA DETECTADA: {dt_info.format_display()}")

            if dt_info.is_business_hours:
                parts.append(
                    "STATUS: Dentro do horário comercial "
                    f"(seg-sex, {BUSINESS_HOUR_START:02d}h-{BUSINESS_HOUR_END:02d}h)"
                )
            else:
                parts.append("STATUS: FORA do horário comercial!")
                alt = dt_info.suggest_alternative()
                if alt:
                    parts.append(f"SUGESTÃO ALTERNATIVA: {alt}")
                parts.append(
                    "INSTRUÇÃO: Informe educadamente que o horário está fora do expediente "
                    f"(seg-sex, {BUSINESS_HOUR_START:02d}h às {BUSINESS_HOUR_END:02d}h) "
                    "e sugira a alternativa acima."
                )
        else:
            if dt_info.hour is not None:
                parts.append(f"HORÁRIO MENCIONADO: {dt_info.hour:02d}:{dt_info.minute:02d}")
                if dt_info.hour < BUSINESS_HOUR_START or dt_info.hour >= BUSINESS_HOUR_END:
                    parts.append(
                        "STATUS: Fora do horário comercial. "
                        f"Sugira horário entre {BUSINESS_HOUR_START:02d}h e {BUSINESS_HOUR_END:02d}h."
                    )

        return "\n".join(parts)

    def _format_collected_data(self, profile: dict) -> str:
        """Format collected qualification data for the LLM context."""
        parts = []
        fields = {
            "operadora": "Operadora",
            "tipo_plano": "Modalidade",
            "valor_atual": "Valor atual",
            "beneficiarios_familia": "Beneficiários da mesma família",
            "data_adesao": "Ano de contratação",
            "preferred_datetime": "Preferência de horário",
        }
        for key, label in fields.items():
            value = profile.get(key)
            if value:
                parts.append(f"{label}: {value}")
        if not parts:
            return "Nenhum dado coletado ainda"
        return "\n".join(parts)

    def _get_missing_fields(self, profile: dict) -> list[str]:
        missing = []
        for label, keys in QUALIFICATION_FIELD_LABELS.items():
            if not all(profile.get(key) for key in keys):
                missing.append(label)
        return missing

    def _infer_recently_requested_fields(self, history: list[dict]) -> list[str]:
        recent_assistant_text = "\n".join(
            msg.get("content", "").lower()
            for msg in history[-3:]
            if msg.get("role") == "assistant"
        )

        mapping = {
            "valor atual do plano": [
                "valor atual",
                "valor do plano",
                "quanto está pagando",
                "quanto paga",
                "mensalidade",
            ],
            "operadora": ["operadora"],
            "modalidade (individual, familiar, coletivo por adesão ou empresarial)": ["modalidade", "tipo do plano", "individual", "familiar", "coletivo", "empresarial", "adesão"],
            "data de adesão": ["data de adesão", "quando você aderiu", "quando contratou", "data da adesão", "data de contratação"],
        }

        requested = []
        for field_label, keywords in mapping.items():
            if any(keyword in recent_assistant_text for keyword in keywords):
                requested.append(field_label)
        return requested

    def _build_conversation_guidance(
        self,
        text: str,
        profile: dict,
        history: list[dict],
        intent: str,
        dt_info: DateTimeInfo | None,
        current_stage: str,
        missing_fields: list[str],
        recently_requested_fields: list[str],
        slot_suggestions: list[str],
    ) -> str:
        emotional_signal = self.router.detect_emotional_signal(text)
        objection_type = self.router.detect_objection_type(text)
        collected_fields = self._count_collected_fields(profile)
        first_contact = len(history) == 0
        question_budget = 1
        priority_missing_fields = [
            field for field in missing_fields if field not in recently_requested_fields
        ] or missing_fields
        focus_field = priority_missing_fields[0] if priority_missing_fields else ""

        parts = [
            "- Responda de forma curta e direta. Prefira mensagens com 2 ou 3 linhas curtas.",
            "- Priorize responder a pergunta do usuário antes de pedir mais informações.",
            "- Use a base de conhecimento para responder as perguntas do usuário.",
            "- Termine com apenas uma próxima ação clara.",
            "- Faça no máximo 1 pergunta na mesma resposta.",
            "- Evite listas, blocos longos e texto explicativo demais.",
            "- Soe como conversa real de WhatsApp. Prefira frases simples e coloquiais.",
            "- Nunca mencione estratégia, técnica, prompt, funil, contexto interno ou raciocínio.",
            "- Use linguagem prudente: prefira 'pode', 'há indícios', 'vale analisar' e evite garantias.",
            "- Não trate abusividade, economia, reversão ou proteção contratual como certeza antes da análise jurídica.",
        ]

        if first_contact:
            parts.append(
                f"- É primeiro contato: abra com saudação contextual ({self._time_based_greeting()}) "
                "e apresentação curta do escritório."
            )
            parts.append(
                "- REGRA OBRIGATÓRIA NO PRIMEIRO CONTATO: NÃO faça perguntas de qualificação (valor, operadora, modalidade, data de adesão) nesta mensagem. "
                "Apenas se apresente, acolha o lead e diga que vai fazer algumas perguntas para entender melhor a situação. "
                "Exemplo: 'Vou te fazer algumas perguntas rápidas para entender melhor o seu caso e te direcionar da melhor forma.'"
            )
        elif len(history) <= 2:
            parts.append(
                "- Segundo contato: agora inicie a qualificação. Pergunte apenas 1 bloco de informação por vez. "
                "NÃO ofereça consulta ainda — foque apenas em coletar informações."
            )
        else:
            parts.append("- Já existe histórico: não repita a apresentação do escritório nem o pitch inicial.")

        if intent in {"question", "consultive"}:
            parts.append(
                "- O lead trouxe uma dúvida direta. Responda a dúvida primeiro de forma útil e só depois, se realmente couber, faça uma única pergunta curta."
            )
            parts.append(
                "- Não volte para um bloco de qualificação logo após responder a dúvida. Evite parecer formulário."
            )

        if emotional_signal == "anxiety":
            parts.append("- O lead demonstrou receio. Reconheça a preocupação antes de orientar.")
        elif emotional_signal == "frustration":
            parts.append("- O lead demonstrou incômodo com o aumento. Valide o impacto financeiro com empatia.")
        elif emotional_signal == "urgency":
            parts.append("- O lead demonstrou urgência. Seja objetivo e acelere o próximo passo.")
        elif emotional_signal == "hesitation":
            parts.append("- O lead está hesitante. Reduza a pressão e faça uma pergunta simples.")

        if objection_type != "none":
            objection_guidance = {
                "location_concern": (
                    "O lead esperava atendimento presencial ou perto dele. Reconheça empaticamente "
                    "(\"entendo, muitos clientes pensam isso no início\"), reforce que o serviço é 100% "
                    "online e por isso atende todo o Brasil sem perda de qualidade. Convide para uma "
                    "análise rápida de 30 min por vídeo ou ligação, sem compromisso, para o lead "
                    "comprovar na prática. NÃO se despeça — tente reverter."
                ),
                "cancellation_fear": (
                    "Reconheça o receio e explique com prudência que a análise busca avaliar medidas "
                    "para preservar o contrato e reduzir riscos, sem garantir resultado."
                ),
                "spouse_alignment": "Ofereça marcar com o casal junto, sem pressionar.",
                "price_pressure": "Reforce economia, impacto do reajuste e clareza da análise gratuita.",
                "timing": "Reconheça a correria e proponha um próximo passo simples.",
                "thinking": "Resuma valor e convide para um avanço leve, sem agressividade.",
            }
            parts.append(f"- Objeção detectada: {objection_guidance[objection_type]}")

        if focus_field:
            parts.append(
                f"- Se for pedir algum dado nesta resposta, peça SOMENTE: {focus_field}."
            )

        if recently_requested_fields:
            parts.append(
                "- Alguns dados já foram pedidos recentemente. Não repita o mesmo bloco, não use lista numerada e peça no máximo UMA informação por vez."
            )

        if collected_fields >= 3:
            parts.append("- Antes de avançar, reconheça resumidamente o que já foi informado pelo lead.")

        if current_stage in {"oferta_consulta", "tratamento_objecao", "agendamento"}:
            parts.append("- Se fizer sentido, conduza para consulta/análise e use CTA de agendamento.")
        elif not self._has_minimum_qualification(profile):
            parts.append(
                "- BLOQUEIO DE AGENDAMENTO: Ainda faltam dados obrigatórios para avançar. "
                "NÃO mencione consulta, análise gratuita, Dr. Filipe ou agendamento nesta resposta. "
                "Foque APENAS em coletar os dados faltantes de forma natural e empática."
            )

        if intent == "qualification" and priority_missing_fields:
            parts.append("- Evite pedir todos os dados de uma vez. Priorize apenas um próximo dado.")
        if intent == "scheduling" and not self._has_minimum_qualification(profile):
            parts.append(
                "- O lead quer agendar, mas ainda faltam dados mínimos. Reconheça o interesse mas "
                "NÃO fale em horários, consulta ou agendamento. Peça apenas o próximo dado essencial. "
                "Diga algo como: 'Ótimo que você queira avançar! Antes, preciso entender melhor seu caso.'"
            )
        if intent == "scheduling" and dt_info and dt_info.is_valid and dt_info.is_business_hours:
            parts.append(
                "- Se o lead citar um horário válido, diga que ele pode conferir e escolher esse horário direto no link da agenda."
            )

        # Anti-despedida prematura: cliente disse so "obrigada" sem despedida real
        if self._is_thanks_only(text) and not profile.get("confirmed_slot"):
            parts.append(
                "- O cliente disse apenas 'obrigada/valeu' mas NAO se despediu (sem 'tchau', 'ate mais', etc). "
                "NAO se despeca! Tente reativar o interesse: \"De nada! Antes de voce ir: posso te oferecer "
                "um horario rapido com o Dr. Filipe? Sao 30 min e e gratuito.\" Faca uma ultima tentativa "
                "de avancar, mas com leveza, sem insistir."
            )

        return "\n".join(parts)

    def _count_collected_fields(self, profile: dict) -> int:
        keys = [
            "operadora",
            "tipo_plano",
            "valor_atual",
            "data_adesao",
            "preferred_datetime",
        ]
        return sum(1 for key in keys if profile.get(key))

    def _has_minimum_qualification(self, profile: dict) -> bool:
        return all(profile.get(key) for key in MINIMUM_QUALIFICATION_KEYS)

    def _resolve_stage(self, current_stage: str, intent: str, profile: dict) -> str:
        next_stage = self.router.determine_stage_transition(current_stage, intent)
        has_minimum_qualification = self._has_minimum_qualification(profile)

        if current_stage in {"abordagem_inicial", "qualificacao"}:
            if intent == "objection":
                return "tratamento_objecao" if has_minimum_qualification else "qualificacao"
            if intent == "scheduling":
                return "agendamento" if has_minimum_qualification else "qualificacao"
            if has_minimum_qualification:
                return "oferta_consulta"

        return next_stage

    def _should_offer_scheduling_link(self, profile: dict, current_stage: str) -> bool:
        return current_stage in {"oferta_consulta", "tratamento_objecao", "agendamento"}

    def _time_based_greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            return "bom dia"
        if hour < 18:
            return "boa tarde"
        return "boa noite"

    def _is_out_of_hours_request(self, dt_info: DateTimeInfo | None) -> bool:
        if not dt_info:
            return False
        if dt_info.is_valid:
            return not dt_info.is_business_hours
        if dt_info.hour is None:
            return False
        return dt_info.hour < BUSINESS_HOUR_START or dt_info.hour >= BUSINESS_HOUR_END

    def _build_out_of_hours_response(self, name: str, slot_suggestions: list[str]) -> str:
        prefix = f"{name}, " if name else ""
        return (
            f"{prefix}esse horário fica fora do nosso atendimento.\n"
            f"Aqui atendemos de segunda a sexta, das {BUSINESS_HOUR_START:02d}h às {BUSINESS_HOUR_END:02d}h.\n"
            "Se quiser, eu te envio a agenda para escolher um horário disponível."
        )

    def _build_in_hours_scheduling_response(self, name: str, dt_info: DateTimeInfo) -> str:
        prefix = f"{name}, " if name else ""
        selected = dt_info.format_display()
        return (
            f"{prefix}esse horário está dentro do nosso atendimento.\n"
            f"Você pode ver se {selected} está livre na agenda.\n"
            "Se quiser, eu te mando o link."
        )

    def _build_offer_consulta_response(
        self,
        name: str,
        profile: dict,
        slot_suggestions: list[str],
    ) -> str:
        # Usa diagnóstico determinístico do cenário conforme documento oficial
        cenario = classify_cenario(profile)
        diag = diagnostic_message(cenario, name=name, profile=profile)
        if diag:
            # Para cenários viáveis (falso coletivo / multifamiliar), inclui CTA de agenda
            if is_viable(cenario):
                return diag + "\n\nPodemos agendar uma chamada de vídeo com o Dr. Filipe. Quer que eu veja os horários disponíveis?"
            # Para coletivo_adesao, individual, inviavel: só mostra diagnóstico (precisa de info adicional)
            return diag
        # Fallback para o comportamento antigo
        prefix = f"{name}, " if name else ""
        operadora = profile.get("operadora", "seu plano")
        tipo_plano = profile.get("tipo_plano", "plano")
        valor_atual = self._format_currency_value(profile.get("valor_atual"))
        data_adesao = profile.get("data_adesao")

        context_bits = [f"{tipo_plano} da {operadora}"]
        if valor_atual:
            context_bits.append(f"hoje em {valor_atual}")
        if data_adesao:
            context_bits.append(f"adesão em {data_adesao}")
        context = ", ".join(context_bits)

        return (
            f"{prefix}pelo que você me contou sobre o {context}, esse reajuste merece uma análise cuidadosa.\n"
            "Na consulta, o Dr. Filipe pode te explicar os caminhos possíveis no seu caso.\n"
            "Quer marcar? Eu já te sugiro horários disponíveis."
        )

    def _build_cancellation_fear_response(self, name: str, slot_suggestions: list[str]) -> str:
        prefix = f"{name}, " if name else ""
        return (
            f"{prefix}esse receio é bem comum.\n"
            "O mais prudente é analisar seu caso antes de qualquer passo.\n"
            "Se quiser, eu te mando a agenda para falar com o Dr. Filipe."
        )

    def _build_first_contact_response(self, name: str) -> str:
        prefix = f"{name}, " if name else ""
        saudacao = self._time_based_greeting().capitalize()
        return (
            f"{saudacao}, {prefix}aqui é Natasha, do escritório Andrade & Lemos.\n"
            "Posso te ajudar a entender o que aconteceu com seu plano.\n"
            "Me conta o que aconteceu."
        ).replace("  ", " ")

    def _build_consultive_invite_response(self, name: str) -> str:
        prefix = f"{name}, " if name else ""
        return (
            f"{prefix}sim, claro.\n"
            "Me manda sua dúvida do jeito que ficar mais fácil.\n"
            "Eu te respondo primeiro."
        )

    def _format_currency_value(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        formatted = f"{numeric:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R${formatted}"

    def _append_scheduling_message(self, response: str, name: str) -> str:
        cleaned = re.sub(
            r"\(?https?://(?:www\.)?oncehub\.com/[^\s)]+\)?",
            "",
            response,
            flags=re.IGNORECASE,
        )

        cleaned_lines: list[str] = []
        for line in cleaned.splitlines():
            stripped = line.strip()
            lowered = stripped.lower()
            if not stripped:
                cleaned_lines.append("")
                continue
            if "pode clicar no link" in lowered:
                continue
            cleaned_lines.append(line)

        cleaned_response = "\n".join(cleaned_lines)
        cleaned_response = re.sub(r"\n{3,}", "\n\n", cleaned_response).strip()
        scheduling_message = get_scheduling_message(name)
        if not cleaned_response:
            return scheduling_message
        return f"{cleaned_response}\n\n{scheduling_message}"

    def _normalize_response(self, response: str) -> str:
        response = response.replace("\r\n", "\n")

        keycap_numbers = {
            "1️⃣": "1.",
            "2️⃣": "2.",
            "3️⃣": "3.",
            "4️⃣": "4.",
            "5️⃣": "5.",
        }
        for keycap, plain in keycap_numbers.items():
            response = response.replace(keycap, plain)

        response = self._strip_meta_instructions(response)
        response = self._soften_overstatements(response)
        response = re.sub(r"[*_`~]", "", response)
        response = re.sub(r"[\U0001F300-\U0001FAFF]", "", response)
        response = re.sub(r"[ \t]{2,}", " ", response)
        response = re.sub(r"\n{3,}", "\n\n", response)
        response = re.sub(r"[ \t]+\n", "\n", response)
        return response.strip()

    def _strip_meta_instructions(self, response: str) -> str:
        cleaned_lines: list[str] = []
        for line in response.splitlines():
            stripped = line.strip()
            if any(re.search(pattern, stripped, flags=re.IGNORECASE) for pattern in META_RESPONSE_PATTERNS):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def _soften_overstatements(self, response: str) -> str:
        softened = response
        for pattern, replacement in SOFTENING_REPLACEMENTS:
            softened = re.sub(pattern, replacement, softened, flags=re.IGNORECASE)
        return softened

    def _is_human_handoff_request(self, text: str) -> bool:
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in HUMAN_HANDOFF_PATTERNS)

    def _is_consultive_invite_request(self, text: str) -> bool:
        text_lower = text.lower().strip()
        return any(re.search(pattern, text_lower) for pattern in CONSULTIVE_INVITE_PATTERNS)

    def _infer_handoff_reason(self, text: str) -> str:
        text_lower = text.lower()
        if "lig" in text_lower:
            return "cliente pediu contato humano por ligação"
        if "atendente" in text_lower or "humano" in text_lower or "pessoa" in text_lower:
            return "cliente pediu atendimento humano"
        return "cliente pediu apoio da equipe"

    def _build_handoff_response(self, name: str) -> str:
        prefix = f"{name}, " if name else ""
        return (
            f"{prefix}vou deixar seu atendimento sinalizado para a nossa equipe continuar com você.\n\n"
            "Já registrei seu contexto aqui para facilitar o próximo passo e evitar que você precise repetir tudo."
        )


    def _is_thanks_only(self, text: str) -> bool:
        """Cliente disse so 'obrigada/valeu' SEM despedida explicita."""
        t = text.lower().strip()
        if not t or len(t) > 30:
            return False
        thanks = ["obrigada", "obrigado", "obg", "valeu", "vlw", "grata", "grato"]
        goodbye = ["tchau", "bom dia", "boa tarde", "boa noite", "até mais", "ate mais", "até logo", "ate logo", "até breve", "ate breve", "abraço", "abraco"]
        has_thanks = any(w in t for w in thanks)
        has_goodbye = any(w in t for w in goodbye)
        return has_thanks and not has_goodbye

    def _is_explicit_goodbye(self, text: str) -> bool:
        t = text.lower().strip()
        goodbye_terms = ["tchau", "até mais", "ate mais", "até logo", "ate logo", "até breve", "ate breve", "boa noite", "fui", "falou", "abraço", "abraco"]
        return any(g in t for g in goodbye_terms)


    def _is_cost_question(self, text: str) -> bool:
        text_lower = text.lower().strip()
        return any(re.search(p, text_lower) for p in COST_QUESTION_PATTERNS)

    def _build_cost_deflection_response(self, name: str) -> str:
        prefix = f"{name}, " if name else ""
        return (
            f"{prefix}essa parte de valores e honorários o Dr. Filipe te explica pessoalmente na consulta, "
            "porque depende da análise do seu caso específico.\n"
            "Posso te oferecer um horário com ele agora? Assim você conversa direto com quem cuida disso."
        )

    def _determine_lead_status(self, profile: dict, stage: str) -> str:
        if profile.get("handoff_requested"):
            return "waiting_human"
        if profile.get("outbound_enabled") and profile.get("outbound_status") in {"queued", "contacted"}:
            return "outbound_pending"
        if stage == "confirmacao_consulta":
            return "scheduled"
        if stage in {"fechamento", "indicacao_ativa"}:
            return "won"
        return "ai_active"

    def _build_lead_summary(
        self,
        profile: dict,
        stage: str,
        history: list[dict],
        latest_user_message: str,
    ) -> str:
        pieces: list[str] = []
        name = profile.get("name")
        if name:
            pieces.append(name)

        operadora = profile.get("operadora")
        tipo_plano = profile.get("tipo_plano")
        if operadora or tipo_plano:
            plan_context = " / ".join(part for part in [operadora, tipo_plano] if part)
            pieces.append(plan_context)

        valor_atual = self._format_currency_value(profile.get("valor_atual"))
        if valor_atual:
            pieces.append(f"valor atual {valor_atual}")

        data_adesao = profile.get("data_adesao")
        if data_adesao:
            pieces.append(f"adesão {data_adesao}")

        pieces.append(f"etapa {stage.replace('_', ' ')}")

        if profile.get("handoff_reason"):
            pieces.append(profile["handoff_reason"])

        recent_user_lines = [
            msg.get("content", "").strip()
            for msg in history[-4:]
            if msg.get("role") == "user" and msg.get("content", "").strip()
        ]
        if latest_user_message.strip():
            recent_user_lines.append(latest_user_message.strip())
        if recent_user_lines:
            pieces.append(f"última demanda: {recent_user_lines[-1][:120]}")

        return " | ".join(pieces[:6])
