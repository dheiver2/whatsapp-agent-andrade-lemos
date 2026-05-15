"""Classificação dos 5 cenários conforme jornada prescritiva.

Cenarios:
- "falso_coletivo": empresarial + mesma família + operadora privada → VIÁVEL
- "multifamiliar":  empresarial + famílias DIFERENTES → VIÁVEL menos
- "coletivo_adesao": coletivo por adesão → fluxo extra
- "individual": individual/familiar puro → 1/2 viável
- "inviavel": autogestão/estatal/cancelado
- "indefinido": dados insuficientes
"""
from __future__ import annotations


AUTOGESTAO_OPERADORAS = (
    "geap", "cassi", "postal", "saude petrobras", "vale saude", "petrobras",
    "fundacao", "fundação",
)


def classify_cenario(profile: dict) -> str:
    tipo = (profile.get("tipo_plano") or "").lower()
    operadora = (profile.get("operadora") or "").lower()
    benef_fam = (profile.get("beneficiarios_familia") or "").lower()

    # 5. inviável (autogestão)
    if any(t in operadora for t in AUTOGESTAO_OPERADORAS):
        return "inviavel"

    # 3. coletivo por adesão
    if "ades" in tipo:
        return "coletivo_adesao"

    # 1 e 2. empresarial → depende de família
    if "empresarial" in tipo or "coletivo empresarial" in tipo:
        if benef_fam == "sim":
            return "falso_coletivo"
        if benef_fam == "não" or benef_fam == "nao":
            return "multifamiliar"
        return "indefinido"  # falta info sobre família

    # 4. individual/familiar puro
    if "individual" in tipo or "familiar" in tipo:
        return "individual"

    return "indefinido"


def diagnostic_message(cenario: str, name: str = "", profile: dict | None = None) -> str:
    """Retorna mensagem diagnóstica conforme jornada do documento."""
    prefix = f"{name}, " if name else ""
    p = profile or {}

    if cenario == "falso_coletivo":
        # REGRA CRÍTICA do documento: mencionar OS DOIS benefícios
        return (
            f"{prefix}seu plano é de fato um falso coletivo. É possível "
            "reduzir a mensalidade em até 50% e restituir o que pagou a "
            "mais nos últimos 3 anos.\n\n"
            "Se for muito antigo (mais de 10 anos), dá até para reduzir mais. "
            "Se for muito recente (1 ou 2 anos), é possível limitar os "
            "abusos e diminuir o valor da mensalidade."
        )

    if cenario == "multifamiliar":
        return (
            f"{prefix}seu caso tem particularidades porque os beneficiários "
            "não são todos da mesma família. É uma tese menos viável, mas "
            "ainda possível dependendo do contexto — especialmente se o "
            "valor do plano for elevado."
        )

    if cenario == "coletivo_adesao":
        return (
            f"{prefix}seu plano é coletivo por adesão. Pra te orientar "
            "melhor, preciso saber:\n\n"
            "1) Sabe qual a entidade contratante? (normalmente está no "
            "cartão do plano ou no contrato)\n"
            "2) Você tem vínculo efetivo com essa entidade/associação/"
            "sindicato?"
        )

    if cenario == "individual":
        return (
            f"{prefix}planos individuais têm reajuste regulado pela ANS. "
            "Vamos verificar se houve cobrança indevida. Pra adiantar:\n\n"
            "- De quanto foi o aumento?\n"
            "- Foi reajuste por idade ou anual?"
        )

    if cenario == "inviavel":
        return (
            f"{prefix}nesse tipo de plano (autogestão), os critérios são "
            "diferentes. Preciso de mais detalhes:\n\n"
            "- Valor atual do plano\n"
            "- Idade dos beneficiários\n"
            "- Se for Cassi: é Família I ou Família II? Data de adesão?"
        )

    return ""


def is_viable(cenario: str) -> bool:
    """Cenários que avançam pra proposta de reunião automaticamente."""
    return cenario in ("falso_coletivo", "multifamiliar")
