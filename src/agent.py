"""Orquestra o Gemini e as ferramentas determinísticas da Empório da Música."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from google import genai

from src.data_loader import load_data
from src.prompts import build_system_prompt
from src.tools import TOOL_SCHEMAS, StoreTools

load_dotenv()
MAX_TOOL_ITERATIONS = 6
MAX_API_ATTEMPTS = 2
BACKOFF_SECONDS = 1.0
SDK_RETRY_ATTEMPTS = 1


class AgentError(RuntimeError):
    """Erro recuperável ao comunicar com o provedor do modelo."""


def _is_rate_limit_or_unavailable(error: Exception) -> bool:
    """Detecta rate limit (429) ou indisponibilidade temporária (503)."""
    status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
    error_str = str(error).lower()
    return status_code in {429, 503} or "429" in error_str or "503" in error_str or "rate limit" in error_str or "service_unavailable" in error_str or "high demand" in error_str


def _call_with_retry(call: Callable[[], Any]) -> Any:
    """Executa chamada à API com no máximo duas tentativas para indisponibilidade temporária."""
    for attempt in range(1, MAX_API_ATTEMPTS + 1):
        try:
            return call()
        except Exception as error:
            if not _is_rate_limit_or_unavailable(error) or attempt == MAX_API_ATTEMPTS:
                raise AgentError("Não foi possível consultar o assistente agora. Tente novamente em instantes.") from error
            time.sleep(BACKOFF_SECONDS * (2 ** (attempt - 1)))
    raise AssertionError("Fluxo de retry inesperado.")


def _history_context(historico: list[dict[str, str]]) -> str:
    """Converte somente mensagens textuais anteriores em contexto para a nova interação."""
    if not historico:
        return ""
    lines = []
    for item in historico[-12:]:
        role = "Cliente" if item.get("role") == "user" else "Atendente"
        content = item.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n\nContexto anterior da conversa:\n" + "\n".join(lines) if lines else ""


def _execute_tool(tools: StoreTools, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Executa somente funções declaradas; converte erros de argumentos em retorno ao modelo."""
    function = getattr(tools, name, None)
    if not callable(function) or name.startswith("_"):
        return {"ok": False, "error": "Ferramenta solicitada não está disponível."}
    try:
        return function(**arguments)
    except (TypeError, ValueError) as error:
        return {"ok": False, "error": f"Não foi possível executar a consulta: {error}"}


def responder(mensagem: str, historico: list[dict[str, str]] | None = None) -> str:
    """Responde uma mensagem usando Gemini e tools; atualiza o histórico em memória recebido.

    Args:
        mensagem: Texto atual do cliente.
        historico: Lista mutável de mensagens no formato
            ``[{"role": "user"|"assistant", "content": "..."}]``. Pode ser reutilizada entre turnos.

    Returns:
        Texto final pronto para ser exibido ao cliente.
    """
    if not mensagem or not mensagem.strip():
        return "Me conta como posso te ajudar com instrumentos, pedidos ou políticas da loja?"
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL")
    if not api_key or not model:
        raise AgentError("Configure GEMINI_API_KEY e GEMINI_MODEL no arquivo .env antes de iniciar o agente.")

    conversation = historico if historico is not None else []
    tools = StoreTools(load_data())
    client = genai.Client(
        api_key=api_key,
        http_options={"retry_options": {"attempts": SDK_RETRY_ATTEMPTS}},
    )
    tool_definitions = [{"type": "function", **schema} for schema in TOOL_SCHEMAS]
    user_input = f"{mensagem.strip()}{_history_context(conversation)}"
    interaction = _call_with_retry(
        lambda: client.interactions.create(
            model=model,
            input=user_input,
            system_instruction=build_system_prompt(),
            tools=tool_definitions,
            timeout=30,
        )
    )

    for _ in range(MAX_TOOL_ITERATIONS):
        function_calls = [step for step in interaction.steps if step.type == "function_call"]
        if not function_calls:
            answer = (interaction.output_text or "Não consegui gerar uma resposta agora. Tente novamente.").strip()
            conversation.extend([{"role": "user", "content": mensagem.strip()}, {"role": "assistant", "content": answer}])
            return answer

        function_results = []
        for call in function_calls:
            result = _execute_tool(tools, call.name, dict(call.arguments or {}))
            function_results.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}],
            })
        interaction = _call_with_retry(
            lambda: client.interactions.create(
                model=model,
                input=function_results,
                previous_interaction_id=interaction.id,
                tools=tool_definitions,
                timeout=30,
            )
        )

    fallback = "Tive uma dificuldade para concluir a consulta. Pode reformular sua pergunta ou tentar novamente?"
    conversation.extend([{"role": "user", "content": mensagem.strip()}, {"role": "assistant", "content": fallback}])
    return fallback
