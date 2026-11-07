#!/usr/bin/env python3
"""Hook logger for Antigravity and Claude Code. Usage: hook.py <harness> <event>.

Reads the hook payload (JSON) on stdin and appends one line to events.jsonl
next to this script. Always prints {} so the agent continues.
"""
import datetime, json, os, sys

harness, event = sys.argv[1], sys.argv[2]
try:
    p = json.loads(sys.stdin.read() or "{}")
except Exception:
    p = {}
tool = p.get("toolName") or p.get("tool_name") or (p.get("toolCall") or {}).get("name")
cwd = p.get("cwd") or (p.get("workspacePaths") or [None])[0]
row = {
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds"),
    "harness": harness,
    "event": event,
    "session": p.get("conversationId") or p.get("session_id"),
    "tool": tool,
    "model": p.get("modelName"),
    "effort": p.get("effort"),
    "transcript": p.get("transcriptPath") or p.get("transcript_path"),
    "cwd": cwd,
    "prompt": str(p.get("lastUserInput") or p.get("prompt") or "")[:60],
}
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "events.jsonl"), "a") as f:
    f.write(json.dumps(row) + "\n")
print("{}")
