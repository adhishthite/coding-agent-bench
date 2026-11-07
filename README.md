# Coding agent bench kit

Compare coding agents on the same tasks. For each run, the kit records tests passed,
model and thinking level, model calls, tool calls, tokens, list-price cost and time.

| Setup | Agent | Model | How it runs |
|---|---|---|---|
| s1 | Antigravity CLI | Gemini 4 Argon (Medium) | `run_check.sh` |
| s2 | Antigravity CLI | Claude Opus 5.5 (Medium) | `run_check.sh` |
| s3 | VS Code + Antigravity extension | Gemini 4 Argon (Medium) | by hand, `manual.sh` |
| s4 | Claude Code CLI | Claude Opus 5.5 (effort Medium) | `run_check.sh` |
| s5 | Antigravity CLI | Gemini 3.8 Flash (Medium) | `run_check.sh` |
| s6 | VS Code + Claude Code extension | Claude Opus 5.5 (effort Medium) | by hand, `manual.sh` |

## Setup (once)

```bash
bash setup.sh
```

Needs `python3`, `git`, `agy` (Antigravity CLI) and `claude` (Claude Code). No other packages.

## Run the CLI setups

```bash
TASK=T2 bash run_check.sh      # one task on s1 s2 s4 s5, in throwaway repos with auto-approve
bash run_all.sh                # T1, T2, T3; waits until Claude Code is idle 6 min before each task
ONLY="s1 s4" TASK=T3 bash run_check.sh
```

## Run the VS Code setups

```bash
bash manual.sh prep T2         # fresh s3 and s6, prints the prompt
# Open s3 in VS Code: Antigravity panel, Gemini 4 Argon (Medium), paste the prompt.
# Open s6 in VS Code: Claude Code panel, Opus, effort Medium, paste the prompt.
bash manual.sh collect T2
```

Results go to `results/<time>-<task>/summary.md`.

## Tasks

| Task | What the agent must do | Graded by |
|---|---|---|
| T1 | Fix 2 one-line bugs | `python3 test_calc.py` |
| T2 | Find and fix 3 bugs across 3 files in a small `portfolio` package | 10 unit tests (5 fail at start) |
| T3 | Implement `realized_pnl_report()` from `SPEC.md` | 2 visible tests + 4 hidden tests in `~/.bench-hidden/T3` |

To add your own task: create `tasks/T4/` with the code, tests and a `PROMPT.txt`. The default test command is `python3 -m unittest`; if yours differs, add it in `run_tests()` in `summarize.py`. Optional hidden tests go in `~/.bench-hidden/T4`.

## How the data is collected

- Hooks (`hookcfg/`, made by `setup.sh`) log each tool call, the model name, the session and the transcript path to `events.jsonl`.
- Model calls, tokens and time come from the session files. Each run saves `sN.diff` (including new files) in the results folder.
- Tokens come from each tool's own session files: the Antigravity `transcript.jsonl`, and the Claude Code session `.jsonl`.
- Cost = tokens x public list price per 1M tokens (see `PRICES` in `summarize.py`).
- Claude Code uses a 5-minute prompt cache in this folder (`.claude/settings.json`: `"promptCacheTtl": "5m"`).
- "1st-call cache read" = 0 means the run started with a cold cache.

## Fair-test rules

- Use the same thinking level in every setup. The summary shows the level that each run actually used.
- Run each task 3 times and compare medians. Single runs vary a lot.
- Antigravity does not report cache-write tokens for Claude models, so that cost is slightly low.
