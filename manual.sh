#!/usr/bin/env bash
# VS Code runs (by hand): s3 = Antigravity extension + Gemini 4 Argon (Medium), s6 = Claude Code extension + Opus (Medium).
#   bash manual.sh prep T2      -> fresh s3 and s6 repos for the task, prints the prompt
#   bash manual.sh collect T2   -> summary for s3 and s6
set -u
BASE=$(cd "$(dirname "$0")" && pwd); cd "$BASE"
CMD=${1:-}; TASK=${2:-T2}
case $CMD in
  prep)
    for r in s3 s6; do
      rm -rf "$r"; cp -R "tasks/$TASK" "$r"; rm -f "$r/PROMPT.txt"; cp -R hookcfg/.agents hookcfg/.claude "$r/"
      (cd "$r" && git init -q && git add -A && git -c user.email=b@b -c user.name=bench commit -qm init)
    done
    : > events.jsonl
    echo "Open $BASE/s3 (Antigravity panel, Gemini 4 Argon Medium) and $BASE/s6 (Claude Code panel, Opus, effort Medium)."
    echo "Paste this prompt in each:"; echo; cat "tasks/$TASK/PROMPT.txt"; echo ;;
  collect)
    OUT="$BASE/results/$(date +%Y%m%d-%H%M)-$TASK-vscode"; mkdir -p "$OUT"
    python3 summarize.py --task "$TASK" --setups s3,s6 --out "$OUT"
    for r in s3 s6; do (cd "$r" && git add -A && git diff --cached > "$OUT/$r.diff"); done; cp events.jsonl "$OUT/"
    echo "Saved: $OUT" ;;
  *) echo "Usage: bash manual.sh prep|collect T1|T2|T3" ;;
esac
