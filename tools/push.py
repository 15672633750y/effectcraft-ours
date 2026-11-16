#!/usr/bin/env python3
"""Push files to the GitHub repo and optionally start the build."""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

TOKEN = Path('/data/user/0/com.deepseek.harness/files/.ec_token').read_text().strip()
REPO = '15672633750y/effectcraft-ours'
BASE = f'https://api.github.com/repos/{REPO}'


def api(path: str, data=None, method: str | None = None):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        BASE + path,
        data=body,
        method=method or ('POST' if body else 'GET'),
        headers={
            'User-Agent': 'dsh',
            'Authorization': f'Bearer {TOKEN}',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
        },
    )
    return json.load(urllib.request.urlopen(req, timeout=60))


def push(files: dict[str, Path], message: str) -> str:
    sha = api('/git/ref/heads/main')['object']['sha']
    tree = api(f'/git/commits/{sha}')['tree']['sha']
    entries = []
    for remote, local in files.items():
        blob = api('/git/blobs', {
            'content': base64.b64encode(Path(local).read_bytes()).decode(),
            'encoding': 'base64',
        })
        entries.append({'path': remote, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    new_tree = api('/git/trees', {'base_tree': tree, 'tree': entries})
    commit = api('/git/commits', {'message': message, 'tree': new_tree['sha'], 'parents': [sha]})
    api('/git/refs/heads/main', {'sha': commit['sha']}, method='PATCH')
    return commit['sha']


def dispatch() -> int:
    req = urllib.request.Request(
        f'{BASE}/actions/workflows/414083221/dispatches',
        data=json.dumps({'ref': 'main', 'inputs': {'tag': 'v0.24.1'}}).encode(),
        method='POST',
        headers={
            'User-Agent': 'dsh',
            'Authorization': f'Bearer {TOKEN}',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
        },
    )
    return urllib.request.urlopen(req, timeout=60).status


def latest_run():
    runs = api('/actions/runs?per_page=1')['workflow_runs']
    return runs[0]['run_number'], runs[0]['status'], runs[0].get('conclusion')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        print(*latest_run())
    else:
        message = sys.argv[1] if len(sys.argv) > 1 else 'update'
        files = json.loads(sys.argv[2])
        print('pushed', push(files, message)[:10])
        time.sleep(3)
        print('dispatch', dispatch())
