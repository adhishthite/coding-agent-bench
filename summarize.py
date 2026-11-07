#!/usr/bin/env python3
"""Summarize one task run: tests, model, calls, tool calls, tokens, cost, time.

Data sources (no third-party packages):
  - events.jsonl written by hook.py (session, tools, model, transcript path, cwd)
  - Antigravity transcript.jsonl (per-step input / cache read / output tokens)
  - Claude Code session .jsonl (per-message usage; deduplicated by message id)
Cost uses public list prices per 1M tokens (global endpoint, checked 5 Nov 2026).
"""
import argparse, datetime, json, os, re, subprocess, sys

# (input, cached input, cache write 5m, cache write 1h, output) USD per 1M tokens.
PRICES = {
    "gemini-4-argon": (4.00, 0.20, 0.0, 0.0, 20.00),     # standard price (promo ends 30 Nov 2026)
    "gemini-3.8-flash": (1.50, 0.15, 0.0, 0.0, 7.50),    # standard price (intro price is half until 31 Dec 2026)
    "claude-opus-5-5": (4.00, 0.20, 5.00, 8.00, 20.00),
}
LABELS = {
    "s1": "Antigravity CLI + Gemini 4 Argon",
    "s2": "Antigravity CLI + Claude Opus 5.5",
    "s3": "VS Code Antigravity ext + Gemini 4 Argon",
    "s4": "Claude Code CLI + Claude Opus 5.5",
    "s5": "Antigravity CLI + Gemini 3.8 Flash",
    "s6": "VS Code Claude Code ext + Claude Opus 5.5",
}
# Fallback price key per setup, used when the reported model name is not in PRICES
# (some agy builds report an alias instead of the public model name).
SETUP_MODEL = {"s1": "gemini-4-argon", "s3": "gemini-4-argon", "s5": "gemini-3.8-flash",
               "s2": "claude-opus-5-5", "s4": "claude-opus-5-5", "s6": "claude-opus-5-5"}
BASE = os.path.dirname(os.path.abspath(__file__))
HIDDEN = os.path.expanduser("~/.bench-hidden")


def ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def norm(m):
    # "Gemini 4 Argon (Medium)" and "gemini-4-argon-medium" -> same key form
    return re.sub(r"[^a-z0-9]+", "-", (m or "").lower()).strip("-")


def price_for(model):
    for k, v in PRICES.items():
        if model and norm(model).startswith(norm(k)):
            return v
    return None


def run_tests(task, d):
    # Test command per task. Default: python3 -m unittest. Add your own tasks here if they differ.
    cmd = ["python3", "test_calc.py"] if task == "T1" else ["python3", "-m", "unittest", "-q"]
    ok = subprocess.run(cmd, cwd=d, capture_output=True).returncode == 0
    hidden = None
    if os.path.isdir(os.path.join(HIDDEN, task)):  # optional hidden tests: ~/.bench-hidden/<task>
        h = os.path.join(HIDDEN, task)
        hidden = subprocess.run(["python3", "-m", "unittest", "discover", "-s", h, "-t", h, "-q"],
                                cwd=d, capture_output=True).returncode == 0
    return ok, hidden


def agy_usage(path):
    calls, inp, cr, out, first_cr, t = 0, 0, 0, 0, None, []
    for line in open(path):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("created_at"):
            t.append(ts(row["created_at"]))
        m = re.search(r'"input_tokens":(\d+)', line)
        if not m:
            continue
        calls += 1
        inp += int(m.group(1))
        c = re.search(r'"cache_read_tokens":(\d+)', line)
        o = re.search(r'"output_tokens":(\d+)', line)
        crv = int(c.group(1)) if c else 0
        cr += crv
        out += int(o.group(1)) if o else 0
        first_cr = crv if first_cr is None else first_cr
    secs = (max(t) - min(t)).total_seconds() if len(t) > 1 else None
    return dict(calls=calls, input=inp, cache_read=cr, cache_write=0, cw1h=0, output=out, first_cr=first_cr, secs=secs)


def claude_usage(path):
    msgs, t, effort, model = {}, [], set(), None
    for line in open(path):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("timestamp"):
            t.append(ts(row["timestamp"]))
        effort.update(re.findall(r'"effort":"([a-z]+)"', line))
        if row.get("type") == "assistant":
            msg = row.get("message", {})
            model = msg.get("model") or model
            msgs[msg.get("id")] = msg.get("usage", {})  # one line per content block: keep last per id
    u = list(msgs.values())
    g = lambda k: sum(x.get(k) or 0 for x in u)
    cw1h = sum((x.get("cache_creation") or {}).get("ephemeral_1h_input_tokens") or 0 for x in u)
    secs = (max(t) - min(t)).total_seconds() if len(t) > 1 else None
    return dict(calls=len(u), input=g("input_tokens"), cache_read=g("cache_read_input_tokens"),
                cache_write=g("cache_creation_input_tokens") - cw1h, cw1h=cw1h, output=g("output_tokens"),
                first_cr=(u[0].get("cache_read_input_tokens") if u else None), secs=secs,
                model=f"{model} ({','.join(sorted(effort)) or 'effort ?'})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--setups", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    events = [json.loads(l) for l in open(os.path.join(BASE, "events.jsonl")) if l.strip()] \
        if os.path.exists(os.path.join(BASE, "events.jsonl")) else []
    rows = []
    for s in a.setups.split(","):
        d = os.path.join(BASE, s)
        mine = [e for e in events if e.get("cwd") and os.path.basename(os.path.normpath(e["cwd"])) == s]
        r = dict(setup=s, label=LABELS.get(s, s))
        r["tests"], r["hidden"] = run_tests(a.task, d) if os.path.isdir(d) else (None, None)
        if not mine:
            r["note"] = "no hook events (did hooks run in this folder?)"
            rows.append(r)
            continue
        sess = mine[-1]["session"]
        ev = [e for e in mine if e["session"] == sess]
        tools = {}
        for e in ev:
            if e["event"] == "PostToolUse":
                tools[e["tool"]] = tools.get(e["tool"], 0) + 1
        r["tools"] = sum(tools.values())
        r["tool_mix"] = ", ".join(f"{k}={v}" for k, v in sorted(tools.items()))
        tr = next((e["transcript"] for e in ev if e.get("transcript")), None)
        if ev[0]["harness"] == "agy":
            r["model"] = next((e["model"] for e in ev if e.get("model")), "?")
            u = agy_usage(tr) if tr and os.path.exists(tr) else {}
            sj = os.path.join(BASE, f"{s}.json")  # CLI self-report adds thinking tokens
            if os.path.exists(sj):
                try:
                    r["thinking"] = json.load(open(sj)).get("usage", {}).get("thinking_tokens")
                except ValueError:
                    pass
        else:
            u = claude_usage(tr) if tr and os.path.exists(tr) else {}
            r["model"] = u.pop("model", "?")
        r.update(u)
        p = price_for(r.get("model", "")) or price_for(SETUP_MODEL.get(s))
        if p and u:
            r["cost"] = round((r["input"] * p[0] + r["cache_read"] * p[1] + r["cache_write"] * p[2]
                               + r["cw1h"] * p[3] + r["output"] * p[4]) / 1e6, 4)
        rows.append(r)

    yn = lambda v: "-" if v is None else ("PASS" if v else "FAIL")
    hdr = ["Setup", "Model (level)", "Tests", "Hidden", "Time s", "Model calls", "Tool calls", "Input", "Cache read",
           "Cache write", "Output", "1st-call cache read", "Cost USD", "Tool mix"]
    lines = [f"## {a.task}", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in [
            f"{r['setup']} {r['label']}", r.get("model", "-"), yn(r["tests"]), yn(r["hidden"]),
            round(r["secs"]) if r.get("secs") else "-", r.get("calls", "-"), r.get("tools", "-"),
            r.get("input", "-"), r.get("cache_read", "-"), (r.get("cache_write", 0) + r.get("cw1h", 0)) if "input" in r else "-",
            r.get("output", "-"), r.get("first_cr", "-"), r.get("cost", "-"), r.get("tool_mix", r.get("note", "-"))]) + " |")
    lines += ["", "Cost = tokens x public list price (global). Antigravity output includes thinking. "
              "Cache write for Claude via Antigravity is not reported. 1st-call cache read 0 = cold start."]
    text = "\n".join(lines)
    print(text)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        open(os.path.join(a.out, "summary.md"), "w").write(text + "\n")
        json.dump(rows, open(os.path.join(a.out, "summary.json"), "w"), indent=2, default=str)


if __name__ == "__main__":
    sys.exit(main())
