import os, json, uuid
from pathlib import Path
chat_dir = Path('chat_history')
chat_dir.mkdir(exist_ok=True)
for i in range(3):
    cid = uuid.uuid4().hex
    data = {
        'id': cid,
        'created_at': '2026-01-01T00:00:00+00:00',
        'messages': [{'role':'user','content':f'Hello {i}'}, {'role':'assistant','content':'Hi'}]
    }
    (chat_dir/f'{cid}.json').write_text(json.dumps(data), encoding='utf-8')