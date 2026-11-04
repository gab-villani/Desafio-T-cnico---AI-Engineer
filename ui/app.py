import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent import responder

CHAT_DIR = Path(
    os.getenv(
        "CHAT_HISTORY_DIR",
        str(Path(__file__).resolve().parent.parent / "chat_history"),
    )
)
CHAT_ID_RE = r"^[A-Za-z0-9_-]{1,64}$"


def _save_chat(chat_id: str, history: list) -> None:
    if not history:
        return
    if not re.fullmatch(CHAT_ID_RE, chat_id):
        raise ValueError("Invalid chat_id format")

    CHAT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = CHAT_DIR / f"{chat_id}.json"
    if file_path.exists():
        existing = json.loads(file_path.read_text(encoding="utf-8"))
        created_at = existing.get(
            "created_at", datetime.now(timezone.utc).isoformat()
        )
    else:
        created_at = datetime.now(timezone.utc).isoformat()

    data = {"id": chat_id, "created_at": created_at, "messages": history}
    tmp_path = CHAT_DIR / f".{chat_id}.tmp"
    tmp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    os.replace(tmp_path, file_path)


def _title_from_history(history: list, new_chat_label: str) -> str:
    first_user_message = next(
        (message["content"] for message in history if message["role"] == "user"),
        "",
    )
    first_user_message = " ".join(first_user_message.split())
    if not first_user_message:
        return new_chat_label
    return (
        first_user_message[:40] + "…"
        if len(first_user_message) > 40
        else first_user_message
    )


def main():
    labels_by_language = {
        "pt-BR": {
            "title": "🤖 Empório da Música – Chatbot",
            "placeholder": "Digite sua mensagem",
            "new_chat": "Nova conversa",
            "typing": "*digitando...*",
            "load_chat": "Carregar conversa",
        },
        "en": {
            "title": "🤖 Empório da Music – Chatbot",
            "placeholder": "Type your message",
            "new_chat": "New conversation",
            "typing": "*typing...*",
            "load_chat": "Load conversation",
        },
    }

    if "idioma" not in st.session_state:
        st.session_state.idioma = "pt-BR"
    st.sidebar.selectbox(
        "Idioma / Language",
        options=["pt-BR", "en"],
        index=0 if st.session_state.idioma == "pt-BR" else 1,
        key="idioma_selector",
        on_change=lambda: setattr(
            st.session_state, "idioma", st.session_state.idioma_selector
        ),
    )
    idioma = st.session_state.idioma
    labels = labels_by_language[idioma]
    st.title(labels["title"])

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = uuid.uuid4().hex
    if "history" not in st.session_state:
        st.session_state.history = []
    if "created_at" not in st.session_state:
        st.session_state.created_at = datetime.now(timezone.utc).isoformat()

    chat_dir = CHAT_DIR
    saved_chats = []
    if chat_dir.exists():
        for file in chat_dir.iterdir():
            if file.suffix != ".json":
                continue
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                chat_id = file.stem
                if not re.fullmatch(CHAT_ID_RE, chat_id):
                    continue
                title = _title_from_history(data["messages"], labels["new_chat"])
                saved_chats.append((title, chat_id, data["created_at"]))
            except (OSError, ValueError, KeyError, TypeError):
                continue

    current_title = _title_from_history(
        st.session_state.history, labels["new_chat"]
    )
    current_option = (
        f"{current_title} ({st.session_state.created_at[:10]})"
    )
    id_to_label = {st.session_state.chat_id: current_option}
    for title, chat_id, created_at in sorted(
        saved_chats, key=lambda chat: chat[2], reverse=True
    ):
        if chat_id != st.session_state.chat_id:
            id_to_label[chat_id] = f"{title} ({created_at[:10]})"

    label_counts = {}
    for label in id_to_label.values():
        label_counts[label] = label_counts.get(label, 0) + 1
    for chat_id, label in list(id_to_label.items()):
        if label_counts[label] > 1:
            id_to_label[chat_id] = f"{label} [{chat_id}]"

    chat_options = list(id_to_label)
    selected_chat_id = st.sidebar.selectbox(
        labels["load_chat"],
        chat_options,
        index=0,
        format_func=lambda chat_id: id_to_label[chat_id],
    )
    if selected_chat_id != st.session_state.chat_id:
        selected_file = chat_dir / f"{selected_chat_id}.json"
        if selected_file.exists():
            data = json.loads(selected_file.read_text(encoding="utf-8"))
            st.session_state.history = data["messages"]
            st.session_state.chat_id = selected_chat_id
            st.session_state.created_at = data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            )
            st.session_state.pop("identidade_verificada", None)

    for message in st.session_state.history:
        role = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(role):
            st.write(message["content"])

    if st.button(labels["new_chat"]):
        _save_chat(st.session_state.chat_id, st.session_state.history)
        st.session_state.history = []
        st.session_state.chat_id = uuid.uuid4().hex
        st.session_state.created_at = datetime.now(timezone.utc).isoformat()
        st.session_state.pop("identidade_verificada", None)

    user_message = st.chat_input(labels["placeholder"])
    if user_message:
        st.session_state.history.append(
            {"role": "user", "content": user_message}
        )
        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.write(labels["typing"])
            try:
                answer = responder(
                    user_message, list(st.session_state.history), idioma=idioma
                )
            except Exception as error:
                answer = (
                    "Desculpe, ocorreu um erro ao processar sua mensagem: "
                    f"{error}"
                )
            st.session_state.history.append(
                {"role": "assistant", "content": answer}
            )
            placeholder.write(answer)
        _save_chat(st.session_state.chat_id, st.session_state.history)


if __name__ == "__main__":
    main()
