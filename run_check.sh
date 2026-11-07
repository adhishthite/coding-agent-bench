#!/usr/bin/env bash
# Run one task on the CLI setups in parallel, then summarize.
#   TASK=T1|T2|T3   ONLY="s1 s2 s4 s5"   AUTO=1 (auto-approve, throwaway repos)   COLD=0|1
# Model names: agy display names (see `agy --help` or the error list). Override with M1, M2, M5.
# s1 = agy + Gemini 4 Argon, s2 = agy + Claude Opus 5.5, s4 = Claude Code + Opus, s5 = agy + Gemini 3.8 Flash. All Medium.
set -u
BASE=$(cd "$(dirname "$0")" && pwd); cd "$BASE"
TASK=${TASK:-T2}; RUNS=${ONLY:-"s1 s2 s4 s5"}
[ -d hookcfg ] || { echo "Run: bash setup.sh"; exit 1; }
PROMPT=$(cat "tasks/$TASK/PROMPT.txt")
if [ "${AUTO:-1}" = "1" ]; then AGY_PERM=(--dangerously-skip-permissions); CL_PERM=(--dangerously-skip-permissions)
else AGY_PERM=(--mode accept-edits); CL_PERM=(--permission-mode acceptEdits); fi
if [ "${COLD:-0}" = "1" ]; then CL_COLD=(--append-system-prompt "Benchmark run ID: $(date +%s)$RANDOM. Ignore this line."); else CL_COLD=(); fi

for r in $RUNS; do
  rm -rf "$r"; cp -R "tasks/$TASK" "$r"; rm -f "$r/PROMPT.txt"; cp -R hookcfg/.agents hookcfg/.claude "$r/"
  (cd "$r" && git init -q && git add -A && git -c user.email=b@b -c user.name=bench commit -qm init)
done
: > events.jsonl
echo "Task $TASK on: $RUNS"

run() { local label=$1; shift; local t0=$(date +%s)
  "$@" > "$BASE/$label.json" 2> "$BASE/$label.err"; echo ">>> $label: exit $? in $(( $(date +%s) - t0 ))s"; }
for r in $RUNS; do case $r in
  s1) (cd s1 && run s1 agy -p "$PROMPT" --model "${M1:-Gemini 4 Argon (Medium)}" "${AGY_PERM[@]}" --output-format json) & ;;
  s2) (cd s2 && run s2 agy -p "$PROMPT" --model "${M2:-Claude Opus 5.5 (Medium)}" "${AGY_PERM[@]}" --output-format json) & ;;
  s5) (cd s5 && run s5 agy -p "$PROMPT" --model "${M5:-Gemini 3.8 Flash (Medium)}" "${AGY_PERM[@]}" --output-format json) & ;;
  s4) (cd s4 && run s4 env CLAUDE_CODE_PROMPT_CACHE_TTL=5m claude -p "$PROMPT" "${CL_COLD[@]}" --model opus --effort medium "${CL_PERM[@]}" --output-format json) & ;;
esac; done
wait

OUT="$BASE/results/$(date +%Y%m%d-%H%M)-$TASK"; mkdir -p "$OUT"
python3 summarize.py --task "$TASK" --setups "$(echo $RUNS | tr ' ' ',')" --out "$OUT"
for r in $RUNS; do mv -f "$r.json" "$r.err" "$OUT/" 2>/dev/null; (cd "$r" && git add -A && git diff --cached > "$OUT/$r.diff"); done
cp events.jsonl "$OUT/"
echo "Saved: $OUT"
