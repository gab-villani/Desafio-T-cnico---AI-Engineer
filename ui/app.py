import sys
from pathlib import Path
import uuid
import json
from datetime import datetime, timezone
import streamlit as st
# Add project root to sys.path before importing src modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent import responder

# ------------------------------------------------------------
# Configuração de caminho
# ------------------------------------------------------------
# Adiciona a raiz do projeto ao sys.path para que 'src' seja importável
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ------------------------------------------------------------
# Constantes
# ------------------------------------------------------------
CHAT_DIR = Path(__file__).resolve().parents[2] / "chat_history"
CHAT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Funções auxiliares
# ------------------------------------------------------------
def _save_chat(chat_id: str, history: list) -> None:
    """Grava o histórico em JSON somente se houver ao menos uma mensagem."""
    if not history:
        return
    data = {
        "id": chat_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": history,
    }
    (CHAT_DIR / f"{chat_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# ------------------------------------------------------------
# UI principal
# ------------------------------------------------------------
def main():
    # Inicialização única no session_state
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = uuid.uuid4().hex
        st.session_state.history = []

    # Título da aplicação
    st.title("🤖 Empório da Música – Chatbot")

    # Entrada de mensagem (sempre renderizada)
    user_msg = st.chat_input("Digite sua mensagem")
    if user_msg:
        # 1) adiciona a mensagem do usuário ao histórico da UI
        st.session_state.history.append({"role": "user", "content": user_msg})
        # 2) chama o agente – passamos uma cópia do histórico conforme contrato
        try:
            answer = responder(user_msg, list(st.session_state.history), idioma="pt-BR")
        except Exception as e:
            answer = f"Desculpe, ocorreu um erro ao processar sua mensagem: {e}"
        # 3) adiciona a resposta ao histórico da UI
        st.session_state.history.append({"role": "assistant", "content": answer})
        # 4) persiste a conversa
        _save_chat(st.session_state.chat_id, st.session_state.history)

    # Botão “Nova conversa” – cria novo chat_id e limpa histórico
    if st.button("Nova conversa"):
        # Salva a conversa atual apenas se houver mensagens
        _save_chat(st.session_state.chat_id, st.session_state.history)
        st.session_state.chat_id = uuid.uuid4().hex
        st.session_state.history = []
        # Não usamos st.rerun(); a UI será re‑renderizada na próxima iteração

    # Renderiza todo o histórico em ordem
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

if __name__ == "__main__":
    main()
