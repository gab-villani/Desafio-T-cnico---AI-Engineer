import sys
from pathlib import Path
# Add project root to sys.path so that 'src' can be imported when running from ui/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from src.agent import responder
import json
import uuid
from datetime import datetime, timezone

def _save_chat(chat_id, history):
    """Save the current chat history to a JSON file in chat_history/."""
    chat_dir = Path(__file__).resolve().parents[2] / "chat_history"
    chat_dir.mkdir(exist_ok=True)
    data = {
        "id": chat_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": history,
    }
    (chat_dir / f"{chat_id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    # Language dictionary for UI labels
    LANG = {
        "pt-BR": {
            "title": "🤖 Empório da Música – Chatbot",
            "placeholder": "Digite sua mensagem",
            "new_chat": "Nova conversa",
            "typing": "*digitando...*",
            "load_chat": "Carregar conversa",
            "save_success": "Conversa salva.",
        },
        "en": {
            "title": "🤖 Empório da Music – Chatbot",
            "placeholder": "Type your message",
            "new_chat": "New conversation",
            "typing": "*typing...*",
            "load_chat": "Load conversation",
            "save_success": "Conversation saved.",
        },
    }

    # Initialize language selection in session state
    if "idioma" not in st.session_state:
        st.session_state.idioma = "pt-BR"
    # Sidebar selector for language
    st.sidebar.selectbox(
        "Idioma / Language",
        options=["pt-BR", "en"],
        index=0 if st.session_state.idioma == "pt-BR" else 1,
        key="idioma_selector",
        on_change=lambda: setattr(st.session_state, "idioma", st.session_state.idioma_selector),
    )
    # Apply selected language
    idioma = st.session_state.idioma
    labels = LANG[idioma]

    st.title(labels["title"])

    # Initialize chat ID and history in session state
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = str(uuid.uuid4())
    if "history" not in st.session_state:
        st.session_state.history = []

    # Sidebar: list saved chats
    chat_dir = Path(__file__).resolve().parents[2] / "chat_history"
    saved_chats = []
    if chat_dir.exists():
        for file in chat_dir.iterdir():
            if file.suffix == ".json":
                try:
                    data = json.loads(file.read_text(encoding="utf-8"))
                    first_user = next((m["content"] for m in data["messages"] if m["role"] == "user"), "")
                    title = first_user[:30] + ("..." if len(first_user) > 30 else "")
                    saved_chats.append((title, data["id"], data["created_at"]))
                except Exception:
                    continue
    if saved_chats:
        options = [f"{t} ({dt[:10]})" for t, _, dt in saved_chats]
        selected = st.sidebar.selectbox(labels["load_chat"], options)
        idx = options.index(selected)
        _, sel_id, _ = saved_chats[idx]
        sel_file = chat_dir / f"{sel_id}.json"
        if sel_file.exists():
            data = json.loads(sel_file.read_text(encoding="utf-8"))
            st.session_state.history = data["messages"]
            st.session_state.chat_id = sel_id
            if "identidade_verificada" in st.session_state:
                del st.session_state["identidade_verificada"]
                        st.rerun()

    # Render existing history (all messages)
    for msg in st.session_state.history:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.write(msg["content"])

    # New conversation button
    if st.button(labels["new_chat"]):
        if st.session_state.history:
            _save_chat(st.session_state.chat_id, st.session_state.history)
            st.success(labels["save_success"])
        st.session_state.history = []
        st.session_state.chat_id = str(uuid.uuid4())
                    st.rerun()

    # Input field
    user_msg = st.chat_input(labels["placeholder"])
    if user_msg:
        # Append user message to history (will be rendered in the history loop)
        st.session_state.history.append({"role": "user", "content": user_msg})
        # Show typing placeholder and get answer
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.write(labels["typing"])
            try:
                answer = responder(user_msg, st.session_state.history, idioma=idioma)
                st.session_state.history.append({"role": "assistant", "content": answer})
                placeholder.write(answer)
                _save_chat(st.session_state.chat_id, st.session_state.history)
            except Exception as e:
                err = f"Desculpe, ocorreu um erro ao processar sua mensagem: {e}".replace("\n", " ")
                placeholder.write(err)

if __name__ == "__main__":
    main()
