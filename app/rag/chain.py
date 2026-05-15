import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.config import get_settings
from app.rag.retriever import format_context, retrieve_context_with_scores
from app.rag.types import Document

WEEKDAYS_PT = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
END = "__end__"
MAX_HISTORY_MESSAGES = 10
MAX_RETRIEVED_DOCS = 5
RELEVANCE_THRESHOLD = 0.12

STAGE_QUERY_HINTS = {
    "abordagem_inicial": "abordagem inicial acolhimento qualificação reajuste plano de saúde",
    "qualificacao": "qualificação operadora modalidade plano valor atual data de adesão",
    "oferta_consulta": "viabilidade confirmada próxima etapa consulta agendamento",
    "tratamento_objecao": "tratamento de objeções cancelamento consulta segurança jurídica",
    "agendamento": "agendamento consulta horário comercial Dr Filipe disponibilidade",
    "confirmacao_consulta": "confirmação de consulta agendamento horário comercial",
    "pos_reuniao": "pós reunião fechamento próximos passos",
    "followup_pos_reuniao": "follow-up pós reunião fechamento",
    "fechamento": "fechamento indicação cliente satisfeito",
    "indicacao_ativa": "indicação ativa clientes contatos recomendação",
}

SYSTEM_PROMPT = """Você é Natasha, assistente jurídica do escritório Andrade & Lemos Advogados (sede em Maceió/AL — atende todo Brasil online), especializada em ação judicial de reajuste abusivo de plano de saúde.

DATA E HORA ATUAL: {current_datetime}
DIA DA SEMANA: {current_weekday}

ATENÇÃO: o atendimento segue OBRIGATORIAMENTE a jornada prescritiva descrita na knowledge base abaixo. NÃO improvise fora dela.

INFORMAÇÕES INSTITUCIONAIS (fonte de verdade):
- Sede física: Maceió, Alagoas (AL)
- Atendimento: 100% online (WhatsApp / ligação / videoconferência)
- Atende clientes de TODOS os estados do Brasil
- Responsável: Dr. Filipe Andrade
- NUNCA diga que o escritório fica em outra cidade que não seja Maceió/AL.

REGRA SOBRE CUSTO/VALORES/HONORÁRIOS (PRIORIDADE MÁXIMA):
- NUNCA fale em valores, preço, honorários, sinal, comissão, fee de êxito, porcentagem, gratuita, gratuito, sem custo.
- Se o cliente perguntar, responda: "Na consulta o Dr. Filipe explica tudo sobre valores e funcionamento. Primeiro preciso entender seu caso. Pode responder as perguntas?"

JORNADA — 7 FASES (siga rigorosamente):

FASE 1 — Saudação + Apresentação (2 mensagens em sequência IMEDIATA):
Msg 1: "Olá! Aqui é do escritório Andrade & Lemos. Vi que você demonstrou interesse em entender se o reajuste do seu plano de saúde pode ser abusivo. Muitos planos aumentaram muito acima do permitido, e em vários casos conseguimos reduzir o valor rapidamente."
Msg 2: "Vou te fazer algumas perguntas para entender o seu momento e te direcionar melhor."

FASE 2 — Qualificação (5 PERGUNTAS em UMA ÚNICA mensagem):
"• Qual é o valor atual do plano?
• Qual é a operadora?
• O plano é individual, familiar, coletivo por adesão ou empresarial?
• Os beneficiários do plano são todos da mesma família?
• Qual foi o ano da contratação do plano?"

FASE 3 — Coleta:
- Aceitar respostas em qualquer formato (texto, separado, parcial).
- Se faltar, peça SOMENTE os dados faltantes: "Obrigado! Só faltam: ..."
- Se vier áudio, peça texto. Se vier foto, peça confirmação por texto.
- Se cliente pedir ligação, peça os dados ANTES de ligar.

FASE 4 — Diagnóstico (5 cenários — classifique o caso e responda conforme):

CENÁRIO 1 - FALSO COLETIVO (empresarial + mesma família + operadora privada):
"Seu plano é de fato um falso coletivo. É possível reduzir a mensalidade em até 50% e restituir o que pagou a mais nos últimos 3 anos (se for muito antigo, mais de 10 anos, dá até para reduzir mais)."
REGRA: SEMPRE mencionar os DOIS benefícios (redução + restituição).
→ Avança para Fase 5.

CENÁRIO 2 - MULTIFAMILIAR (empresarial + famílias DIFERENTES):
"Seu caso tem particularidades. Precisamos de análise mais detalhada na consulta."
Explicar que é tese menos viável mas ainda possível, especialmente se plano alto (>R$10-15k).
→ Avança para Fase 5.

CENÁRIO 3 - COLETIVO POR ADESÃO (sindicato, associação):
Fazer perguntas adicionais:
1) "Sabe qual a entidade contratante do plano? Normalmente está no cartão ou contrato."
2) "Tem vínculo efetivo com a entidade/associação/sindicato contratante?"
Se SEM vínculo → "falso coletivo por adesão" → marca consulta.
Se COM vínculo → pedir contrato + histórico de reajustes.

CENÁRIO 4 - INDIVIDUAL/FAMILIAR puro:
"Planos individuais têm reajuste regulado pela ANS. Vamos verificar se houve cobrança indevida."
Perguntar: de quanto foi o aumento e que tipo (idade ou anual).

CENÁRIO 5 - INVIÁVEL (autogestão como GEAP/Cassi, estatal, cancelado):
"Nesses casos, precisamos do valor atual do plano, idade dos beneficiários, e no caso de Cassi, saber se é Cassi Família I ou Cassi Família II e a data de adesão."

FASE 5 — Proposta de Reunião (3 mensagens em sequência):
Msg 1 (proposta): "Podemos agendar uma chamada de vídeo com o Dr. Filipe, sócio do Andrade e Lemos Advogados. Na consulta ele explica como podemos te ajudar e o quanto você pode economizar com seu plano ao longo dos próximos 5 anos, além dos valores que tem direito a receber."
Msg 2 (reforço): "Isso vai te permitir ter clareza quanto a essa questão, e com certeza te ajudará a tomar uma decisão relativa a esses aumentos abusivos."
Msg 3 (CTA): "Quer que eu veja os horários disponíveis para você?"

Após cliente aceitar:
1) Sistema consulta Google Calendar e injeta 2 horários disponíveis.
2) Cliente escolhe.
3) Bot pede: "Envie-me seu nome completo e email, por gentileza."
4) Confirma: "Agendado! Às [hora] [dia] te enviamos o link, ok?"

REGRAS DO AGENDAMENTO:
- NUNCA envie link externo (OnceHub etc.). Tudo conversacional no chat.
- NUNCA invente horários. Use somente os fornecidos pelo sistema.
- NUNCA confirme agendamento por conta própria — só após o sistema criar o evento.
- Horário comercial: seg-sex, 9h-18h.

FASE 6 — Lembrete da Reunião (sistema dispara):
- 30 min antes: "Boa tarde, [nome]! Tudo bem? Te envio o link da reunião em 30 minutos, ok?"
- No horário: envia link Google Meet
- +10 min sem entrar: "[Nome], quando estiver disponível me confirma que abro a chamada, ok?"
- +30 min sem entrar: "Olá! Como não houve comparecimento, vamos remarcar nossa reunião?"
O bot NÃO cria a chamada — apenas envia o link.

FASE 7 — Follow-up (sistema dispara em silêncio):
D+1, D+3, D+5, D+7, D+10, D+13 com mensagens específicas (ver knowledge).
D+13 sem resposta → SEM INTERESSE.

PROIBIÇÕES:
- NUNCA inventar caso passado, jurisprudência, número, estatística, "muitos clientes ganharam".
- NUNCA escrever meta-comentários "(Nota: mantive o tom...)" no final.
- NUNCA usar emojis exceto se o cliente usar primeiro.
- NUNCA juridiquês excessivo. Use "você" (nunca "tu"). Português BR.
- Máximo 3 mensagens seguidas sem resposta do lead (exceto follow-up).

ESCALONAMENTO HUMANO: se o lead pedir humano explicitamente:
"Vou transferir para nosso atendente. Um momento!" + sinalizar handoff.

CLIENTE JÁ ATIVO (ALCLIENTE) perguntando sobre processo:
"Para acompanhamento de processos, temos um número específico de atendimento pós-contrato. Vou pedir para a equipe te direcionar."

CONTEXTO DA BASE DE CONHECIMENTO (jornada completa):
{context}

INFORMAÇÕES DO LEAD:
Nome: {user_name}
Telefone: {user_phone}
Etapa atual: {current_stage}
Dados coletados: {collected_data}

AGENDAMENTO:
- Ano atual: {current_year}
{scheduling_context}

HISTÓRICO DO LEAD: use para manter continuidade. Não repita perguntas já respondidas.

GUIDANCE OPERACIONAL ESPECÍFICA PARA ESTA RESPOSTA:
{conversation_guidance}

Responda de forma natural como WhatsApp real. Mensagens curtas, diretas, profissionais.
"""


@dataclass(slots=True)
class RAGGraphState:
    user_message: str
    user_name: str
    user_phone: str
    current_stage: str
    collected_data: str
    chat_history: list[dict]
    scheduling_context: str = ""
    now: datetime = field(default_factory=datetime.now)
    history_messages: list[dict[str, str]] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    fallback_queries: list[str] = field(default_factory=list)
    retrieved_docs: list[tuple[Document, float]] = field(default_factory=list)
    context: str = ""
    conversation_guidance: str = ""
    response: str = ""


GraphNode = Callable[[RAGGraphState], RAGGraphState | Awaitable[RAGGraphState]]
GraphRouter = Callable[[RAGGraphState], str]


class StateGraph:
    def __init__(self, start_node: str):
        self.start_node = start_node
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, str] = {}
        self.conditional_edges: dict[str, tuple[GraphRouter, dict[str, str]]] = {}

    def add_node(self, name: str, node: GraphNode) -> None:
        self.nodes[name] = node

    def add_edge(self, source: str, target: str) -> None:
        self.edges[source] = target

    def add_conditional_edges(
        self,
        source: str,
        router: GraphRouter,
        targets: dict[str, str],
    ) -> None:
        self.conditional_edges[source] = (router, targets)

    async def ainvoke(self, state: RAGGraphState) -> RAGGraphState:
        current = self.start_node
        steps = 0

        while current != END:
            steps += 1
            if steps > len(self.nodes) + len(self.conditional_edges) + 4:
                raise RuntimeError("RAG graph entered an unexpected loop")

            node = self.nodes[current]
            result = node(state)
            state = await result if inspect.isawaitable(result) else result

            if current in self.conditional_edges:
                router, targets = self.conditional_edges[current]
                route = router(state)
                if route not in targets:
                    raise RuntimeError(f"Unknown route '{route}' from node '{current}'")
                current = targets[route]
                continue

            current = self.edges.get(current, END)

        return state


def _normalize_query(text: str) -> str:
    return " ".join(text.split()).strip()


def _append_unique_query(queries: list[str], text: str) -> None:
    query = _normalize_query(text)
    if query and query not in queries:
        queries.append(query)


def _doc_key(doc: Document) -> tuple[str, str]:
    source = str(doc.metadata.get("source", ""))
    chunk_index = str(doc.metadata.get("chunk_index", ""))
    return source, chunk_index


def _search_queries(queries: list[str], top_k: int) -> list[tuple[Document, float]]:
    merged: dict[tuple[str, str], tuple[Document, float]] = {}

    for query in queries:
        for doc, score in retrieve_context_with_scores(query, top_k=top_k):
            key = _doc_key(doc)
            normalized_score = float(score or 0.0)
            current = merged.get(key)
            if current is None or normalized_score > current[1]:
                merged[key] = (doc, normalized_score)

    return sorted(merged.values(), key=lambda item: item[1], reverse=True)


def _merge_doc_results(
    primary: list[tuple[Document, float]],
    extra: list[tuple[Document, float]],
) -> list[tuple[Document, float]]:
    merged = {_doc_key(doc): (doc, score) for doc, score in primary}
    for doc, score in extra:
        key = _doc_key(doc)
        current = merged.get(key)
        if current is None or score > current[1]:
            merged[key] = (doc, score)
    return sorted(merged.values(), key=lambda item: item[1], reverse=True)


def _prepare_history(state: RAGGraphState) -> RAGGraphState:
    history_messages = []
    for msg in state.chat_history[-MAX_HISTORY_MESSAGES:]:
        role = msg.get("role")
        content = msg.get("content", "").strip()
        if role in {"user", "assistant"} and content:
            history_messages.append({"role": role, "content": content})
    state.history_messages = history_messages
    return state


def _build_fallback_queries(state: RAGGraphState) -> list[str]:
    queries: list[str] = []
    lower_message = state.user_message.lower()

    stage_hint = STAGE_QUERY_HINTS.get(state.current_stage)
    if stage_hint:
        _append_unique_query(queries, stage_hint)

    if state.scheduling_context or state.current_stage in {"agendamento", "confirmacao_consulta"}:
        _append_unique_query(queries, "agendamento consulta horário comercial Dr. Filipe disponibilidade")

    if state.current_stage in {"tratamento_objecao", "oferta_consulta"}:
        _append_unique_query(queries, "objeções consulta reajuste medo de cancelar plano de saúde")

    if any(term in lower_message for term in ["cancel", "pens", "espos", "marido", "mulher"]):
        _append_unique_query(queries, "tratamento de objeções cancelamento consulta segurança do contrato")

    _append_unique_query(queries, "manual de atendimento reajuste plano de saúde")
    return queries[:4]


def _plan_queries(state: RAGGraphState) -> RAGGraphState:
    queries: list[str] = []
    _append_unique_query(queries, state.user_message)
    _append_unique_query(queries, f"{state.current_stage.replace('_', ' ')} {state.user_message}")

    if state.collected_data and state.collected_data != "Nenhum dado coletado ainda":
        _append_unique_query(queries, f"{state.user_message} {state.collected_data}")

    if state.scheduling_context:
        _append_unique_query(queries, f"{state.user_message} {state.scheduling_context}")

    state.search_queries = queries[:4]
    state.fallback_queries = _build_fallback_queries(state)
    return state


def _retrieve_primary_context(state: RAGGraphState) -> RAGGraphState:
    state.retrieved_docs = _search_queries(state.search_queries, top_k=4)[:MAX_RETRIEVED_DOCS]
    return state


def _route_after_primary_retrieval(state: RAGGraphState) -> str:
    if not state.retrieved_docs:
        return "fallback"

    best_score = state.retrieved_docs[0][1]
    if len(state.retrieved_docs) < 2 or best_score < RELEVANCE_THRESHOLD:
        return "fallback"

    return "build_context"


def _retrieve_fallback_context(state: RAGGraphState) -> RAGGraphState:
    if not state.fallback_queries:
        return state

    fallback_docs = _search_queries(state.fallback_queries, top_k=3)
    state.retrieved_docs = _merge_doc_results(state.retrieved_docs, fallback_docs)[:MAX_RETRIEVED_DOCS]
    return state


def _build_context(state: RAGGraphState) -> RAGGraphState:
    docs = [doc for doc, _score in state.retrieved_docs[:MAX_RETRIEVED_DOCS]]
    if docs:
        state.context = format_context(docs)
    else:
        state.context = (
            "Nenhum trecho específico foi recuperado da base. "
            "Use as regras do sistema e o histórico para responder com segurança."
        )
    return state


def _build_system_prompt(state: RAGGraphState) -> str:
    return SYSTEM_PROMPT.format(
        context=state.context,
        user_name=state.user_name,
        user_phone=state.user_phone,
        current_stage=state.current_stage,
        collected_data=state.collected_data,
        current_datetime=state.now.strftime("%d/%m/%Y %H:%M"),
        current_weekday=WEEKDAYS_PT[state.now.weekday()],
        current_year=str(state.now.year),
        scheduling_context=state.scheduling_context,
        conversation_guidance=state.conversation_guidance,
    )


def _extract_openrouter_text(payload: dict) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()

    return str(content).strip()


async def _call_openrouter(messages: list[dict[str, str]]) -> str:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://andrade-lemos.com.br",
        "X-Title": "Andrade & Lemos WhatsApp Agent",
    }
    payload = {
        "model": settings.openrouter_model,
        "temperature": 0.4,
        "max_tokens": 500,
        "messages": messages,
    }

    timeout = httpx.Timeout(settings.response_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            if exc.response.status_code == 401:
                raise RuntimeError(
                    "OpenRouter authentication failed. Check OPENROUTER_API_KEY and "
                    "restart the API to reload .env values."
                ) from exc
            raise RuntimeError(
                f"OpenRouter request failed with status {exc.response.status_code}: {detail}"
            ) from exc
        data = response.json()

    text = _extract_openrouter_text(data)
    if not text:
        raise RuntimeError("OpenRouter returned an empty response")
    return text


async def _call_openai_with_model(messages: list[dict[str, str]], model: str) -> str:
    """Chama OpenAI com modelo especifico."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY nao configurada")
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 500,
        "messages": messages,
    }
    timeout = httpx.Timeout(settings.response_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            raise RuntimeError(
                f"OpenAI({model}) request failed {exc.response.status_code}: {detail[:300]}"
            ) from exc
        data = response.json()
    text = _extract_openrouter_text(data)
    if not text:
        raise RuntimeError(f"OpenAI({model}) retornou resposta vazia")
    return text


async def _call_openai(messages: list[dict[str, str]]) -> str:
    """Wrapper retrocompatibilidade — usa modelo primario."""
    return await _call_openai_with_model(messages, get_settings().openai_model)


async def _call_openai_fallback(messages: list[dict[str, str]]) -> str:
    return await _call_openai_with_model(messages, get_settings().openai_model_fallback)


async def _call_llm_with_fallback(messages: list[dict[str, str]]) -> str:
    """Chama provedor primary; se falhar, tenta fallback automaticamente."""
    import logging
    log = logging.getLogger(__name__)
    settings = get_settings()
    providers = {
        "openrouter": _call_openrouter,
        "openai": _call_openai,
        "openai_fallback": _call_openai_fallback,
    }

    primary = providers.get(settings.llm_primary, _call_openrouter)
    fallback = providers.get(settings.llm_fallback)

    try:
        return await primary(messages)
    except Exception as primary_err:
        log.warning(
            "LLM primary (%s) falhou: %s -- tentando fallback (%s)",
            settings.llm_primary, str(primary_err)[:200], settings.llm_fallback,
        )
        if fallback and fallback is not primary:
            try:
                return await fallback(messages)
            except Exception as fb_err:
                log.error("LLM fallback (%s) tambem falhou: %s", settings.llm_fallback, str(fb_err)[:200])
                raise RuntimeError(
                    f"Ambos LLMs falharam. Primary({settings.llm_primary}): {str(primary_err)[:120]}. "
                    f"Fallback({settings.llm_fallback}): {str(fb_err)[:120]}"
                ) from fb_err
        raise


async def _generate_llm_response(state: RAGGraphState) -> RAGGraphState:
    messages = [{"role": "system", "content": _build_system_prompt(state)}]
    messages.extend(state.history_messages)
    messages.append({"role": "user", "content": state.user_message})
    state.response = await _call_llm_with_fallback(messages)
    return state


def _build_rag_graph() -> StateGraph:
    graph = StateGraph(start_node="prepare_history")
    graph.add_node("prepare_history", _prepare_history)
    graph.add_node("plan_queries", _plan_queries)
    graph.add_node("retrieve_primary_context", _retrieve_primary_context)
    graph.add_node("retrieve_fallback_context", _retrieve_fallback_context)
    graph.add_node("build_context", _build_context)
    graph.add_node("generate_response", _generate_llm_response)

    graph.add_edge("prepare_history", "plan_queries")
    graph.add_edge("plan_queries", "retrieve_primary_context")
    graph.add_conditional_edges(
        "retrieve_primary_context",
        _route_after_primary_retrieval,
        {
            "fallback": "retrieve_fallback_context",
            "build_context": "build_context",
        },
    )
    graph.add_edge("retrieve_fallback_context", "build_context")
    graph.add_edge("build_context", "generate_response")
    graph.add_edge("generate_response", END)
    return graph


RAG_GRAPH = _build_rag_graph()


async def generate_response(
    user_message: str,
    user_name: str,
    user_phone: str,
    current_stage: str,
    collected_data: str,
    chat_history: list[dict],
    scheduling_context: str = "",
    conversation_guidance: str = "",
) -> str:
    """Generate a response using a graph-based RAG workflow."""
    state = RAGGraphState(
        user_message=user_message,
        user_name=user_name,
        user_phone=user_phone,
        current_stage=current_stage,
        collected_data=collected_data,
        chat_history=chat_history,
        scheduling_context=scheduling_context,
        conversation_guidance=conversation_guidance,
    )
    final_state = await RAG_GRAPH.ainvoke(state)
    return final_state.response


async def generate_outbound_message(
    contact_name: str,
    cadence_label: str,
    followup_day: int,
    notes: str = "",
) -> str:
    """Generate Natasha's outbound opener/follow-up for list-based outreach."""
    note_context = f"\nContexto extra: {notes}" if notes else ""
    system_prompt = f"""Você é Natasha, assistente jurídica do escritório Andrade & Lemos.

Seu papel aqui é iniciar ou retomar uma conversa outbound de forma humana, feminina, carismática e profissional.
Objetivo desta mensagem: abrir a conversa para começar o diagnóstico do caso do plano de saúde.

REGRAS:
- Não invente intimidade.
- Não fale em horário, agenda, link ou agendamento nesta etapa.
- Não tente fechar nada nesta mensagem.
- Convide a pessoa a responder para que Natasha faça perguntas rápidas e entenda o caso.
- Mensagem curta, natural e com no máximo 3 blocos curtos.
- Use o nome da pessoa se ele existir.
- Soe acolhedora e confiante, com leve charme e delicadeza, sem exagero.
- Não mencione prompt, estratégia, funil ou bastidor.
- Não repita texto padronizado; escreva de forma natural.

CADÊNCIA ATUAL: {cadence_label}
DIA DE FOLLOW-UP: {followup_day}{note_context}
"""
    user_prompt = (
        f"Escreva a mensagem outbound da Natasha para {contact_name or 'o contato'} "
        "abrir ou retomar a conversa e incentivar uma resposta."
    )
    return await _call_llm_with_fallback(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
