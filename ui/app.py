import sys
import os
from pathlib import Path
# Define chat directory (environment‑overrideable)
CHAT_DIR = Path(os.getenv("CHAT_HISTORY_DIR", str(Path(__file__).resolve().parent.parent / "chat_history")))
# Add project root to sys.path so that 'src' can be imported when running from ui/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import streamlit as st
from src.agent import responder
import json
import uuid
from datetime import datetime, timezone

def _save_chat(chat_id: str, history: list) -> None:
    """Save the current chat history to a JSON file.
    Does nothing if `history` is empty. Uses atomic write and validates the path.
    """
    if not history:
        return
    # Validate chat_id (hexadecimal)
    if not all(c in "0123456789abcdef" for c in chat_id.lower()):
        raise ValueError("Invalid chat_id format")
    chat_dir = CHAT_DIR
    chat_dir.mkdir(parents=True, exist_ok=True)
    file_path = chat_dir / f"{chat_id}.json"
    # Preserve created_at if file exists, else use current UTC time
    if file_path.exists():
        existing = json.loads(file_path.read_text(encoding="utf-8"))
        created_at = existing.get("created_at", datetime.now(timezone.utc).isoformat())
    else:
        created_at = datetime.now(timezone.utc).isoformat()
    data = {"id": chat_id, "created_at": created_at, "messages": history}
    # Atomic write
    tmp_path = chat_dir / f".{chat_id}.tmp"
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_path, file_path)

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

    # After processing possible new message, build and render the history selector
    history_selector_placeholder = st.sidebar.empty()
    # Gather saved chats
    chat_dir = CHAT_DIR
    saved_chats = []
    if chat_dir.exists():
        for file in chat_dir.iterdir():
            if file.suffix == ".json":
                try:
                    data = json.loads(file.read_text(encoding="utf-8"))
                    first_user = next((m["content"] for m in data["messages"] if m["role"] == "user"), "")
                    first_user = " ".join(first_user.split())
                    title = first_user[:30] + ("..." if len(first_user) > 30 else "")
                    saved_chats.append((title, data["id"], data["created_at"]))
                except Exception:
                    continue
    # Ensure created_at for current chat is stored
    if "created_at" not in st.session_state:
        st.session_state.created_at = datetime.now(timezone.utc).isoformat()
    # Current chat title
    def _title_from_hist(hist):
        if not hist:
            return labels["new_chat"]
        first = next((m["content"] for m in hist if m["role"] == "user"), "")
        first = " ".join(first.split())
        if not first:
            return labels["new_chat"]
        return (first[:40] + "…") if len(first) > 40 else first
    # Current chat title
    def _title_from_hist(hist):
        if not hist:
            return labels["new_chat"]
        first = next((m["content"] for m in hist if m["role"] == "user"), "")
        first = " ".join(first.split())
        if not first:
            return labels["new_chat"]
        return (first[:40] + "…") if len(first) > 40 else first
    current_title = _title_from_hist(st.session_state.history)
    current_option = f"{current_title} ({st.session_state.created_at[:10]})"
    # Build mapping of chat ids to display labels
    id_to_label = {st.session_state.chat_id: current_option}
    for title, cid, dt in sorted(saved_chats, key=lambda x: x[2], reverse=True):
        if cid != st.session_state.chat_id:
            id_to_label[cid] = f"{title} ({dt[:10]})"
    # Options are the chat ids, with current chat first
    options = [st.session_state.chat_id] + [cid for cid in id_to_label.keys() if cid != st.session_state.chat_id]
    selected = history_selector_placeholder.selectbox(
        labels["load_chat"], options, index=0, format_func=lambda i: id_to_label[i]
    )
    if selected != st.session_state.chat_id:
        # Load selected chat
        sel_file = chat_dir / f"{selected}.json"
        if sel_file.exists():
            data = json.loads(sel_file.read_text(encoding="utf-8"))
            st.session_state.history = data["messages"]
            st.session_state.chat_id = selected
            st.session_state.created_at = data.get("created_at", datetime.now(timezone.utc).isoformat())
            if "identidade_verificada" in st.session_state:
                del st.session_state["identidade_verificada"]
    

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


    # Input field
    user_msg = st.chat_input(labels["placeholder"])
    if user_msg:
        # Append user message to history (will be rendered in the history loop)
        st.session_state.history.append({"role": "user", "content": user_msg})
        # Get assistant response (copy of history passed)
        try:
            answer = responder(user_msg, list(st.session_state.history), idioma=idioma)
        except Exception as e:
            answer = f"Desculpe, ocorreu um erro ao processar sua mensagem: {e}"
        # Append assistant response to history
        st.session_state.history.append({"role": "assistant", "content": answer})
        # Persist chat
        _save_chat(st.session_state.chat_id, st.session_state.history)

if __name__ == "__main__":
    main()
