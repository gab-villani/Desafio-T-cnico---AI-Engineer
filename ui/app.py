import sys
from pathlib import Path
# Add project root to sys.path so that 'src' can be imported when running from ui/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from src.agent import responder

def main():
    st.title("🤖 Empório da Música – Chatbot")
    # Inicializar histórico na sessão
    if "history" not in st.session_state:
        st.session_state.history = []

    # Botão para iniciar nova conversa
    if st.button("Nova conversa"):
        st.session_state.history = []
        st.rerun()

    # Campo de entrada (chat_input) – disponível a partir do Streamlit 1.30
    user_msg = st.chat_input("Digite sua mensagem")
    if user_msg:
        # Adiciona mensagem do usuário ao histórico
        st.session_state.history.append({"role": "user", "content": user_msg})
        # Exibe a mensagem do usuário
        with st.chat_message("user"):
            st.write(user_msg)
        # Indicador de "digitando..."
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.write("*digitando...*")
            try:
                answer = responder(user_msg, st.session_state.history)
                # Atualiza histórico com a resposta
                st.session_state.history.append({"role": "assistant", "content": answer})
                message_placeholder.write(answer)
            except Exception as e:
                error_msg = f"Desculpe, ocorreu um erro ao processar sua mensagem: {e}".replace("\n", " ")
                message_placeholder.write(error_msg)

    # Renderiza todo o histórico (exceto a última mensagem já exibida acima)
    for msg in st.session_state.history[:-1]:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.write(msg["content"])

if __name__ == "__main__":
    main()
