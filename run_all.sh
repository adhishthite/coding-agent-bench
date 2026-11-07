#!/usr/bin/env bash
# Run T1, T2, T3 on the CLI setups. Before each task, wait until Claude Code has been idle 6 min (cold cache).
set -u
BASE=$(cd "$(dirname "$0")" && pwd); cd "$BASE"
for T in ${TASKS:-T1 T2 T3}; do
  wait=$(python3 - <<'P'
import glob, os, time
f = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
last = max((os.path.getmtime(x) for x in f), default=0)
print(max(0, int(last + 360 - time.time())))
P
)
  if [ "$wait" -gt 0 ]; then echo "### $T: waiting ${wait}s so Claude Code starts cold"; sleep "$wait"; else echo "### $T: starting now"; fi
  TASK=$T bash ./run_check.sh
done
echo "### All done. See $BASE/results/"
