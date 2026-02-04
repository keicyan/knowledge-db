import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:80] if s else "untitled"


def now_jst_date() -> str:
    # JST固定（Asia/Tokyo）
    # ActionsはUTCなので、簡易的に +9h
    dt = datetime.now(timezone.utc).timestamp() + 9 * 3600
    jst = datetime.fromtimestamp(dt)
    return jst.strftime("%Y-%m-%d")


def main():
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not found")

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    issue = event.get("issue")
    if not issue:
        raise RuntimeError("No issue in event payload")

    number = issue["number"]
    title = issue["title"].replace("[Inbox]", "").strip() or f"Inbox-{number}"
    body = issue.get("body") or ""

    # domain はテンプレのdropdownが本文に含まれることが多いので、雑に抽出（なければ other）
    domain = "other"
    m = re.search(r"Domain\s*\n\s*(management|finance|strategy|marketing|sales|org|product|ma|other)", body, re.I)
    if m:
        domain = m.group(1).lower()

    # memo抽出（テンプレ本文情報だが、なければ全文）
    memo = body
    m2 = re.search(r"Memo \(raw\)\s*\n([\s\S]*?)(\n\n|$)", body, re.I)
    if m2:
        memo = m2.group(1).strip()

    # tags抽出
    tags = []
    mt = re.search(r"Tags \(comma separated\)\s*\n([^\n]*)", body, re.I)
    if mt:
        tags = [t.strip() for t in mt.group(1).split(",") if t.strip()]

    created = now_jst_date()
    kid = f"K-{created.replace('-', '')}-{number:03d}"
    filename = f"{kid}_{slugify(title)}.md"

    out_dir = Path("knowledge/00_inbox")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename

    fm_tags = "[" + ", ".join(tags) + "]" if tags else "[]"

    content = f"""---
id: {kid}
title: {title}
domain: {domain}
type: note
tags: {fm_tags}
created: {created}
updated: {created}
status: draft
related: []
source: [github_issue#{number}]
---

## 原文メモ（Inbox）
{memo}

## 次に整形するときの方針（任意）
- typeを concept/playbook/decision/project のどれにするか
- 何が「判断をどう変えるか」を書く
"""

    out_path.write_text(content, encoding="utf-8")
    print(f"Wrote: {out_path}")

if __name__ == "__main__":
    main()
