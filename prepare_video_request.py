#!/usr/bin/env python3
"""Prepare an offline AI-video request. Does not upload, submit or generate video."""
from pathlib import Path
import argparse
import json
import uuid
from video_adapter import VideoRequest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider', required=True, help='Adapter alias, e.g. gpt, douyin_ai_creation, doubao')
    p.add_argument('--collage', required=True)
    p.add_argument('--prompt-file', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--seconds', type=float, default=5)
    p.add_argument('--split', type=float, default=.52)
    p.add_argument('--request-id', help='Reuse the saved ID only when recovering the same request')
    a = p.parse_args()
    req = VideoRequest(a.request_id or str(uuid.uuid4()), a.provider,
                       str(Path(a.collage).resolve()),
                       Path(a.prompt_file).read_text(encoding='utf-8'), a.seconds, a.split)
    payload = {'status': 'prepared_not_submitted', 'request': req.to_dict()}
    output = Path(a.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f'Prepared only; nothing uploaded or submitted: {output}')

if __name__ == '__main__':
    main()
