#!/usr/bin/env bash
# One-time setup. Run from the kit folder:  bash setup.sh
set -eu
BASE=$(cd "$(dirname "$0")" && pwd)
echo "Kit folder: $BASE"
for t in python3 git agy claude; do
  if command -v "$t" >/dev/null; then echo "  ok   $t"; else echo "  MISSING $t"; fi
done
H="python3 $BASE/hook.py"
mkdir -p "$BASE/hookcfg/.agents" "$BASE/hookcfg/.claude"
cat > "$BASE/hookcfg/.agents/hooks.json" <<J
{ "bench-metrics": {
    "PostToolUse": [ { "matcher": ".*", "hooks": [ { "type": "command", "command": "$H agy PostToolUse", "timeout": 10 } ] } ],
    "PostInvocation": [ { "type": "command", "command": "$H agy PostInvocation", "timeout": 10 } ],
    "Stop": [ { "type": "command", "command": "$H agy Stop", "timeout": 10 } ]
} }
J
cat > "$BASE/hookcfg/.claude/settings.json" <<J
{ "promptCacheTtl": "5m",
  "autoMemoryEnabled": false,
  "hooks": {
    "UserPromptSubmit": [ { "hooks": [ { "type": "command", "command": "$H claude UserPromptSubmit" } ] } ],
    "PostToolUse": [ { "matcher": ".*", "hooks": [ { "type": "command", "command": "$H claude PostToolUse" } ] } ],
    "Stop": [ { "hooks": [ { "type": "command", "command": "$H claude Stop" } ] } ]
} }
J
# Hidden tests live outside the kit so agents cannot read them.
mkdir -p "$HOME/.bench-hidden/T3" && cp "$BASE/hidden/T3/"*.py "$HOME/.bench-hidden/T3/"
chmod +x "$BASE"/*.sh "$BASE"/*.py
echo "Setup done. Hooks: $BASE/hookcfg. Hidden tests: ~/.bench-hidden/T3"
