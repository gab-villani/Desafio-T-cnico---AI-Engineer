import pathlib, tempfile, shutil, subprocess, sys, json

# Read original ui/app.py
orig = pathlib.Path('ui/app.py').read_text(encoding='utf-8')
# Remove deduplication part: replace _list_saved_chats with version without dedupe
old_func_start = 'def _list_saved_chats():'
old_func_end = '    return chats'
# We'll just replace whole function with simple one that does not dedupe.
new_func = '''def _list_saved_chats():
    """Return list of dicts with id, title, created_at (localized string)."""
    chats = []
    for file in CHAT_DIR.glob("*.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            first_user = next(
                (m["content"] for m in data["messages"] if m["role"] == "user"), ""
            )
            title = first_user[:40] + ("..." if len(first_user) > 40 else "")
            created = data.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                local_dt = dt.astimezone(ZoneInfo("America/Cuiaba"))
                date_str = local_dt.strftime("%d/%m/%Y")
            except Exception:
                date_str = ""
            chats.append({"id": data["id"], "title": title, "date": date_str})
        except Exception:
            continue
    chats.sort(key=lambda c: c["date"], reverse=True)
    return chats
'''
# Find the function boundaries
lines = orig.splitlines()
new_lines = []
i = 0
while i < len(lines):
    if lines[i].startswith('def _list_saved_chats'):
        new_lines.append(new_func)
        # skip until return chats line
        while i < len(lines) and not (lines[i].strip().startswith('return chats') and lines[i-1].strip() != ''):
            i += 1
        # skip the return line
        i += 1
        # continue loop
        continue
    new_lines.append(lines[i])
    i += 1
new_content = '\n'.join(new_lines)
# Write to temp file
tmp_dir = pathlib.Path(tempfile.mkdtemp())
tmp_app = tmp_dir / 'app.py'
tmp_app.write_text(new_content, encoding='utf-8')
print('Temp app at', tmp_app)

# Ensure duplicate files exist in chat_history
CHAT_DIR = pathlib.Path('chat_history')
CHAT_DIR.mkdir(exist_ok=True)
duplicate_id = 'dup-id-1234'
common_msg = 'Mensagem teste'
common_date = '2026-11-02T12:00:00+00:00'
for j in range(2):
    data = {'id': duplicate_id, 'created_at': common_date, 'messages': [{'role': 'user', 'content': common_msg}]}
    (CHAT_DIR / f'dup_{j}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# Run AppTest on temp file using subprocess to capture exception
cmd = [sys.executable, '-c', f'''
import sys, traceback
from streamlit.testing.v1 import AppTest
from streamlit.errors import StreamlitDuplicateElementId
script_path = r"{tmp_app}"
try:
    AppTest.from_file(script_path).run()
except StreamlitDuplicateElementId as e:
    print("EXCEPTION_TYPE:", type(e).__name__)
    print("EXCEPTION_MSG:", e)
    traceback.print_exc()
except Exception as e:
    print("OTHER_EXCEPTION_TYPE:", type(e).__name__)
    print("OTHER_EXCEPTION_MSG:", e)
    traceback.print_exc()
''']
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
print('STDOUT:')
print(result.stdout)
print('STDERR:')
print(result.stderr)
print('Return code:', result.returncode)
# Cleanup
shutil.rmtree(tmp_dir)