#!/usr/bin/env python3
"""Exportiert Claude-Code-Transkripte nach Markdown.

Nur die eigenen Eingaben (Standard) oder das komplette Gespraech (--full).
Die Transkripte liegen als JSONL unter ~/.claude/projects/<slug>/<session-id>.jsonl
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECTS = Path.home() / ".claude" / "projects"
LOCAL = ZoneInfo("Europe/Berlin")


def sessions():
    # Alle Transkriptdateien, neueste zuerst
    files = [p for p in PROJECTS.rglob("*.jsonl") if "subagents" not in p.parts]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def records(path):
    for line in path.open(encoding="utf-8"):
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def text_of(message):
    # Der Inhalt ist entweder ein String oder eine Liste typisierter Bloecke
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    parts = [b.get("text", "") for b in content
             if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(p for p in parts if p.strip())


def when(rec):
    ts = rec.get("timestamp")
    if not ts:
        return ""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(LOCAL).strftime("%Y-%m-%d %H:%M")


def export(path, full=False):
    out = [f"# Chatprotokoll — Sitzung {path.stem}", ""]
    n = 0
    for rec in records(path):
        kind = rec.get("type")
        if kind == "user":
            # Auch Tool-Ergebnisse haben den Typ "user" -- nur echte Eingaben behalten.
            if rec.get("origin", {}).get("kind") != "human":
                continue
            body = text_of(rec.get("message", {})).strip()
            if not body:
                continue
            n += 1
            out += [f"## Eingabe {n} — {when(rec)}", "", body, ""]
        elif kind == "assistant" and full:
            body = text_of(rec.get("message", {})).strip()
            if body:
                out += ["**Antwort (Claude):**", "", body, ""]
    return "\n".join(out), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="Antworten von Claude mit aufnehmen")
    ap.add_argument("--all", action="store_true", help="alle Sitzungen, nicht nur die letzte")
    ap.add_argument("--out", type=Path, help="Ausgabedatei statt stdout")
    args = ap.parse_args()

    targets = sessions() if args.all else sessions()[:1]
    if not targets:
        raise SystemExit(f"no transcripts found under {PROJECTS}")

    chunks, total = [], 0
    for path in targets:
        text, n = export(path, args.full)
        if n:
            chunks.append(text)
            total += n

    result = "\n\n---\n\n".join(chunks)
    if args.out:
        args.out.write_text(result, encoding="utf-8")
        print(f"{total} Eingaben aus {len(chunks)} Sitzung(en) -> {args.out}")
    else:
        print(result)


if __name__ == "__main__":
    main()
