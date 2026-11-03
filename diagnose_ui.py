import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

# Path to the UI script
script_path = (Path(__file__).resolve().parent / "ui" / "app.py").as_posix()

app = AppTest.from_file(script_path).run()

# Check for chat_input and button
elements = app.get("chat_input")
print("chat_input elements:", len(elements))
if elements:
    print("chat_input found:", elements[0])

elements = app.get("button")
print("button elements:", len(elements))
for b in elements:
    print("button:", b.label if hasattr(b, 'label') else b)

# Count script executions - we can track via a counter in session_state
if 'exec_count' not in app.session_state:
    app.session_state['exec_count'] = 0
app.session_state['exec_count'] += 1
print("execution count:", app.session_state['exec_count'])

# Check chat_history files
chat_dir = Path(__file__).resolve().parent / "chat_history"
files_before = list(chat_dir.glob("*.json")) if chat_dir.exists() else []
print("files in chat_history before:", len(files_before))

# Simulate 3 messages
msgs = ["Oi", "Quanto custa o Takamine GD20?", "Qual o status do pedido 5?"]
for m in msgs:
    app.chat_input.set_value(m)
    app.chat_input.post()
    app.run()

# After messages, count files again
files_after = list(chat_dir.glob("*.json")) if chat_dir.exists() else []
print("files in chat_history after:", len(files_after))
print("history length:", len(app.session_state.get('history', [])))