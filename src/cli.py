"""Command-line interface for the Empório da Música agent."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from src.agent import AgentError, responder

PROJECT_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_DIR / "examples"
SESSION_FILE = PROJECT_DIR / ".session_history.json"


def _load_session() -> list[dict[str, str]]:
    """Load history from last session, if it exists."""
    if SESSION_FILE.exists():
        try:
            with SESSION_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def _save_session(history: list[dict[str, str]]) -> None:
    """Persist the current session history."""
    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _save_conversation(history: list[dict[str, str]]) -> None:
    """Export current conversation to examples/ with timestamp."""
    EXAMPLES_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = EXAMPLES_DIR / f"conversa_{timestamp}.md"
    
    with filename.open("w", encoding="utf-8") as f:
        f.write("# Conversa com o Agente Empório da Música\n\n")
        f.write(f"**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        for entry in history:
            role = "🧑 Cliente" if entry["role"] == "user" else "🤖 Atendente"
            f.write(f"## {role}\n\n{entry['content']}\n\n")
    
    print(f"\n✓ Conversa salva em: {filename.relative_to(PROJECT_DIR)}")


def main() -> None:
    """Main CLI loop."""
    print("=" * 70)
    print("🎵 Empório da Música — Assistente de Atendimento")
    print("=" * 70)
    print("\nComandos disponíveis:")
    print("  /sair    - Encerra o atendimento")
    print("  /salvar  - Salva a conversa em examples/")
    print("\nDigite sua mensagem e pressione Enter para conversar.\n")
    
    history = _load_session()
    if history:
        print(f"[Sessão anterior carregada com {len(history)} mensagens]\n")
    
    try:
        while True:
            try:
                user_input = input("Você: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nEncerrando...")
                break
            
            if not user_input:
                continue
            
            if user_input.lower() == "/sair":
                print("\nObrigado por usar o Empório da Música. Até logo! 🎵")
                break
            
            if user_input.lower() == "/salvar":
                if history:
                    _save_conversation(history)
                else:
                    print("\nNão há conversa para salvar ainda.")
                continue
            
            try:
                response = responder(user_input, history)
                print(f"\nAtendente: {response}\n")
            except AgentError as error:
                print(f"\n⚠️  {error}\n")
            except Exception as error:
                print(f"\n❌ Erro inesperado: {error}")
                print("Por favor, tente novamente.\n")
    
    finally:
        if history:
            _save_session(history)


if __name__ == "__main__":
    main()
