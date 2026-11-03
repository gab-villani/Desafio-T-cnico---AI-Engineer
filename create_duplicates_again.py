import json
from pathlib import Path

CHAT_DIR = Path('chat_history')
CHAT_DIR.mkdir(exist_ok=True)

duplicate_id = 'dup-id-1234'
common_msg = 'Mensagem teste'
common_date = '2026-11-02T12:00:00+00:00'

for i in range(2):
    data = {
        'id': duplicate_id,
        'created_at': common_date,
        'messages': [
            {'role': 'user', 'content': common_msg}
        ]
    }
    (CHAT_DIR / f'dup_{i}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('created duplicates again')