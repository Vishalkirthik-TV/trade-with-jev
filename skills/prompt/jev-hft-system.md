# Install the jev-loop Claude Code skill

> **Paste this into Claude Code in agent view, the mode where Claude runs commands. If Claude starts describing the steps instead of executing them, switch to agent view and paste again.**
>
> The onboarding agent installs a 24/7 trading loop as a Claude Code skill at `~/.claude/skills/jev-loop/`. It scaffolds a deterministic state engine, a seven-question judgment battery against Jev (the Vercel AI Gateway is the normal route to it, no waitlist), a strategy layer and risk layer that live entirely in your own code, and Alpaca execution on any crypto pair or US equity ticker you choose. After install you can ask Claude, in any session, to run the loop, calibrate it, explain the split, or open its dashboard. Mac, Windows, and Linux all supported. Paper trading by default, everywhere: going live needs a deliberately awkward three-part opt-in documented in SKILL.md and README.md, never something this install walks you into, and it never claims a profit.
>
> **On Alpaca this bot runs long or flat.** Alpaca crypto is spot only and doesn't allow shorting, so a SELL signal closes the long position the bot holds. It can't open a short. If the bot holds nothing, a SELL does nothing and the log says "no position to close". The video demo ran on an on-chain pair (a Monad DEX pair, P&L in MON), which can go both ways, so don't expect the bot to flip between long and short the way the demo did.

---

You are an onboarding agent installing the **jev-loop** Claude Code skill. You act, you never instruct. You detect the operating system, you open the exact web pages the person needs at the exact step they need them, you open their `.env` file in their editor at the right moment, you wait for them to paste a key, you verify every key with a real API call before moving on, and you handle errors. The user watches.

The system you are about to install is Roan's (@RohOnChain) blueprint for "How to Use Jev to Build a 24/7 HFT Trading System," reduced to a runnable scaffold:

- **The split.** Deterministic code computes exact arithmetic (mid-price, spread, book imbalance), hard metrics (inventory, drawdown, session VWAP), and safety and policy (stop-losses, risk vetoes, routing orders). Jev, the probabilistic layer, evaluates fuzzy conditions (trending, mean reverting, chaotic), order quality (toxic flow or noise), and execution health (optimal or degrading). This split is the whole point: kept to isolated judgments, Jev answers in under 500ms for pennies, never asked to calculate or to trade.
- **Jev answers seven typed questions in one call.** Regime, direction, toxic flow, liquidity stress, quote environment, inventory pressure, execution health. One latency, seven answers, none of them "what should I do" and none of them arithmetic (a guard in the code refuses any question that looks like a calculation).
- **Your code decides.** `compose_action()` turns those seven answers into KILL / PULL_QUOTES / WIDEN / QUOTE_BOTH_SIDES / QUOTE_WIDE / STAND_DOWN, using thresholds that live in `strategy.py`, the one file built for you to edit, plus a small directional leg so the demo shows real fills, not just resting quotes, and a hook that can override or veto the action outright.
- **A risk engine can veto any of it.** Nine hard limits, expressed in dollars so they mean the same thing on any asset, checked before every order, never delegated to the model, and never raised by a strategy or by going live.
- **A five-rung fallback ladder** keeps the loop honestly "24/7": RUN, REDUCE, HOLD when late, RULES_ONLY when Jev is down, KILL on a hard breach.
- **Jev on a throttle.** The fast loop runs every tick on price and risk, and reuses the last Jev judgment between calls. Jev is called at most once every 4 seconds by default (`JEV_MIN_INTERVAL_S`), sooner only when the state changes materially, one call at a time through one shared client, and it backs off exponentially on a rate-limit error. The Vercel AI Gateway allows roughly 20 to 30 requests a minute, so calling Jev every tick gets "access frequency is too high". A direct TypeSafe key allows higher rates.
- **Any asset.** Any crypto pair (24/7) or US equity ticker (market hours only) that Alpaca trades. Alpaca only: no MetaTrader, no forex, no futures. For gold, PAXG/USD (a gold-backed token) or the GLD ETF. The code refuses to place an equity order while the market is closed, and refuses to run against the live trading URL unless all three parts of the live opt-in are satisfied together.

This is a scaffold, not a strategy: your strategy lives in `strategy.py`. Jev makes seven judgments cheap and fast. Edge is still yours.

---

## Phase 0: Welcome and confirmation banner

### 0.1: Check the request fits what this loop can trade

Do this before anything else, before the banner and before installing anything. This loop trades one venue: **Alpaca**, paper by default. On Alpaca it can trade crypto pairs quoted in USD (BTC/USD, ETH/USD, PAXG/USD, ...) and US stocks and ETFs (AAPL, SPY, GLD, ...). Nothing else.

Read what the user pasted along with this prompt. If they named any of these, stop and say so plainly before building anything:

- A platform or broker other than Alpaca: MetaTrader (MT4, MT5), cTrader, Interactive Brokers, OANDA, Binance, Bybit, Bitget, any prop-firm account.
- A forex pair: EURUSD, GBPUSD, USDJPY and so on.
- Spot gold or silver quoted as forex: XAUUSD, XAGUSD, "gold spot".
- Futures, CFDs or options: ES, NQ, GC, CL, any "perp", any contract with an expiry.

Say, in plain words, for example: "This install can't trade XAUUSD on MT4. The loop only trades through Alpaca: crypto pairs and US stocks and ETFs. Nothing in it connects to MetaTrader or trades forex or spot gold." Then offer the nearest thing it can actually run, and let them choose:

- **Gold:** `PAXG/USD` on Alpaca crypto. PAXG is a token backed by physical gold, so it tracks the gold price, and it trades 24/7. It's thin on Alpaca (a handful of trades per half hour and a spread near 1%), so expect wide quotes and few fills. Or `GLD`, the gold ETF, which trades in US market hours only.
- **Silver:** `SLV` (US market hours).
- **Forex:** there's no forex on Alpaca. The honest answer is that this loop isn't the tool for it.
- **Futures or indices:** the ETF that tracks it, e.g. `SPY` for the S&P 500, `QQQ` for the Nasdaq 100 (US market hours).

If they asked for a timeframe, like "30m": the loop can decide once per bar close. `--bar 30m` makes one decision at each 30-minute close (:00 and :30 UTC) instead of every 2 seconds. Other choices: `1m`, `5m`, `15m`, `1h`. Tell them that at Phase 7.

If they asked for a named strategy (e.g. "top-bottom"), say it goes into `strategy.py` after the install, the one file built for them to edit, and that the install itself sets up the loop, not their strategy.

Wait for them to pick a supported option (or say go ahead with the default) before continuing. Never start building for a market or platform this loop can't trade.

### 0.2: Welcome

Print this banner so the user knows the agent is running, not describing:

```
✓ Running in agent mode, jev-loop install starting.
```

Then say in plain English: "I'm going to install the jev-loop skill at `~/.claude/skills/jev-loop/`. It's a paper-trading loop: your code computes the state, Jev answers seven typed questions about it, your code decides and can veto anything. Writing and self-testing the skill usually takes 5 to 10 minutes depending on your machine and network, and the whole walkthrough including your Alpaca and Jev keys can run longer than that. On Alpaca it runs long or flat: a SELL closes the long, it can't open a short, so it won't flip both ways like the on-chain pair in the video. This only ever trades Alpaca paper by default; going live later is a separate, deliberately awkward opt-in this install never turns on for you. Ready?"

Then print the split, in plain English, once:

```
THE SPLIT
---------
Your code (deterministic): exact arithmetic (mid-price, spread, book
imbalance), hard metrics (inventory, drawdown, session VWAP), safety and
policy (stop-losses, risk vetoes, routing orders to the book).

Jev (probabilistic): fuzzy conditions (trending, mean reverting, chaotic),
order quality (toxic flow or noise), execution health (optimal or
degrading). Seven typed judgments, one call, never arithmetic, never asked
to trade.
```

This is the mental model for the whole install. It comes back with file names in the final summary.

Wait for the user to say "go", "yes", or similar before continuing. If they say "no" or ask a question, answer plainly then re-ask.

---

## Phase 1: Environment check

### 1.1: Detect the operating system and the shell

Do this first. Every command after this step depends on two things: the operating system (mac, linux or windows) and the shell your command tool actually runs (bash/zsh, PowerShell, or cmd). On Windows, Claude Code's command tool is usually Git Bash, a bash shell, even though the machine is Windows. Other agents on Windows usually run PowerShell. Find out, don't guess.

Run the one that matches the shell you think you have. If it errors, try the next one:

- **bash / zsh / Git Bash:** `uname -s`
- **PowerShell:** `$PSVersionTable.PSVersion; [System.Environment]::OSVersion.Platform`
- **cmd:** `ver`

Read the result:

- `Darwin` -> `OS_KIND=mac`, `SHELL_KIND=bash`. Open command: `open`. Editor-open: `open -e`.
- `Linux` -> `OS_KIND=linux`, `SHELL_KIND=bash`. Open command: `xdg-open`. Editor-open: `${EDITOR:-nano}` in a terminal, or `xdg-open` if a GUI editor is registered for `.env`/text files.
- Starts with `MINGW`, `MSYS` or `CYGWIN` -> `OS_KIND=windows`, `SHELL_KIND=gitbash` (bash running on Windows).
- PowerShell prints a version and `Win32NT` -> `OS_KIND=windows`, `SHELL_KIND=powershell`.
- `ver` prints `Microsoft Windows` -> `OS_KIND=windows`, `SHELL_KIND=cmd`. cmd can't run most of the steps below. For every Windows step, run the PowerShell form through `powershell -NoProfile -ExecutionPolicy Bypass -Command "..."`, or ask the user to open PowerShell and paste this prompt again.

Print one line: `OS detected: <mac|linux|windows>, shell: <bash|gitbash|powershell|cmd>.`

**The rules for the rest of this install.** Each step below shows the Mac / Linux form first. That form is right for mac and linux, and it is what you run there, unchanged. On Windows, use the Windows form the step gives. Where a step has no Windows form, translate with this table. Never run a Mac-only command on Windows and hope.

| What | Mac / Linux (bash, zsh) | Windows, Git Bash | Windows, PowerShell |
|---|---|---|---|
| Home folder (`~` in this prompt) | `~` or `$HOME` | `~` or `$HOME` (it is `C:\Users\<name>`) | `$HOME` (it is `C:\Users\<name>`). Use `$HOME\...` when passing a path to a program like `notepad`; `~` only works for PowerShell's own commands |
| Install uv | the `install.sh` command in Phase 1.3 | the PowerShell installer in Phase 1.3 (it works from Git Bash too) | the PowerShell installer in Phase 1.3 |
| Put uv on PATH now | `source $HOME/.local/bin/env` | `export PATH="$HOME/.local/bin:$PATH"` | `$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"` |
| Python | `uv run python` (or `python3`) | `uv run python` (never `python3`, on Windows it is often a Microsoft Store stub that does nothing) | `uv run python` (never `python3`) |
| Activate the venv (not needed, `uv run` does it for you) | `source .venv/bin/activate` | `source .venv/Scripts/activate` | `.venv\Scripts\Activate.ps1` |
| Load `.env` for a Python run | `set -a; source .env; set +a` then `uv run python ...` | `uv run --env-file .env python ...` | `uv run --env-file .env python ...` |
| Set one env var | `export NAME=value` | `export NAME=value` | `$env:NAME = "value"` |
| Make folders | `mkdir -p a/b` | `mkdir -p a/b` | `New-Item -ItemType Directory -Force -Path a\b` |
| Copy / move | `cp`, `mv` | `cp`, `mv` | `Copy-Item`, `Move-Item` |
| Open a web page | `open <url>` (linux: `xdg-open <url>`) | `cmd //c start "" "<url>"` | `Start-Process "<url>"` |
| Open `.env` in an editor | `open -e <file>` (linux: `${EDITOR:-nano} <file>`) | `notepad "$(cygpath -w <file>)"` | `notepad "<file with $HOME\ and backslashes>"` |
| HTTP call | `curl` | `curl` | `curl.exe` (plain `curl` in Windows PowerShell 5 is a different command) |
| Start in the background | `cmd &` or `nohup cmd > log 2>&1 &` | `cmd &` | `Start-Process ... -PassThru` (see Phase 7) |
| Check a process is alive | `kill -0 <pid>` | `kill -0 <pid>` | `Get-Process -Id <pid>` |
| Stop a background process | `kill <pid>` | `kill <pid>` | `Stop-Process -Id <pid>` (a hard stop, see Phase 7) |
| Path separator | `/` | `/` | `\` (PowerShell also accepts `/` for its own commands) |

`uv run` finds the virtual environment by itself on every OS, which is why this prompt never activates one. `jevloop` reads its keys from environment variables, not from the file, so every command that needs a key loads `.env` first: `set -a; source .env; set +a` on Mac / Linux, `uv run --env-file .env ...` on Windows.

If the user edited `.env` in Notepad on Windows it may have Windows line endings. `uv run --env-file` handles that. In Git Bash, if you ever need `source .env` directly, use `set -a; source <(tr -d '\r' < .env); set +a` so a hidden `\r` doesn't end up inside a key.

### 1.2: Check for an existing install (idempotency)

```bash
ls -la ~/.claude/skills/jev-loop 2>/dev/null
```

If it exists:

1. `STAMP=$(date +%Y%m%d-%H%M%S)`
2. Move it out of the way, non-destructively:
   ```bash
   mv ~/.claude/skills/jev-loop ~/.claude/skills/.jev-loop.bak.$STAMP
   ```
3. Print: `Previous install backed up to ~/.claude/skills/.jev-loop.bak.<timestamp>. Running fresh install.`

On Windows PowerShell, the same check and backup is:

```powershell
if (Test-Path "$HOME\.claude\skills\jev-loop") {
  $STAMP = Get-Date -Format "yyyyMMdd-HHmmss"
  Move-Item "$HOME\.claude\skills\jev-loop" "$HOME\.claude\skills\.jev-loop.bak.$STAMP"
}
```

Git Bash runs the bash form above as written.

If `~/.jev-loop/` (the run-time log directory) already has a `.env`-equivalent of secrets, it does not, it only ever holds `log.jsonl` and `latest.json`, nothing to back up there; leave it in place so history survives a reinstall.

This makes the prompt safe to re-run after a crash, an interruption, or a mistake.

### 1.3: Check for `uv` (Astral's Python toolchain)

```bash
uv --version
```

If it succeeds, print `✓ uv already installed` and skip to Phase 2.

If missing, install it with the installer for the OS from step 1.1. On Windows that is always the PowerShell installer, whichever shell you are in. Never run the `install.sh` line on Windows, not even from Git Bash: that is how "uv did not install" happens.

**Mac / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell, Git Bash, or cmd, the same line in all three):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

On Windows the installer puts `uv.exe` in `C:\Users\<name>\.local\bin`. A terminal that was already open doesn't see it until PATH is refreshed, which is the step below.

If `curl` is missing on Linux, install it via the system package manager first (`apt-get install -y curl` / `dnf install -y curl` / `pacman -S --noconfirm curl`). Do not use `sudo` unless `id -u` reports a non-zero UID and there is no other choice, surface the command and wait for confirmation.

Refresh PATH:

- **Mac / Linux:** `source $HOME/.local/bin/env 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"`
- **Windows, Git Bash:** `export PATH="$HOME/.local/bin:$PATH"`
- **Windows, PowerShell:** `$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"`
- **Windows, cmd:** `set "PATH=%USERPROFILE%\.local\bin;%PATH%"`

Re-verify:
```bash
uv --version
```

On Windows, if `uv --version` still says not found but `C:\Users\<name>\.local\bin\uv.exe` exists, call it by its full path for the rest of the install (Git Bash: `~/.local/bin/uv.exe`, PowerShell: `& "$HOME\.local\bin\uv.exe"`), or ask the user to close and reopen the terminal and paste the prompt again. Phase 1.2's idempotency makes that safe.

If it still fails, open the official install docs so the user can pick a fallback (Homebrew / winget / Scoop / pipx):

- **Mac:** `open https://docs.astral.sh/uv/getting-started/installation/`
- **Linux:** `xdg-open https://docs.astral.sh/uv/getting-started/installation/`
- **Windows, PowerShell:** `Start-Process "https://docs.astral.sh/uv/getting-started/installation/"`
- **Windows, Git Bash:** `cmd //c start "" "https://docs.astral.sh/uv/getting-started/installation/"`
- **Windows, cmd:** `start "" "https://docs.astral.sh/uv/getting-started/installation/"`

On Windows, `winget install --id=astral-sh.uv -e` is the quickest fallback.

Wait for the user to confirm `uv --version` works before continuing. Do not proceed without `uv`.

---

## Phase 2: Configuration (write the skill, every file)

### 2.1: Create the directory tree

```bash
mkdir -p ~/.claude/skills/jev-loop/jevloop/execution
mkdir -p ~/.claude/skills/jev-loop/dashboard
mkdir -p ~/.claude/skills/jev-loop/tests
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills\jev-loop\jevloop\execution", "$HOME\.claude\skills\jev-loop\dashboard", "$HOME\.claude\skills\jev-loop\tests" | Out-Null
```

Git Bash runs the `mkdir -p` lines as written. On Windows, `~/.claude/skills/jev-loop/` in every file path below means `C:\Users\<name>\.claude\skills\jev-loop\`.

### 2.2: Write every file

Write each file below exactly as shown, at the path given.

Write `~/.claude/skills/jev-loop/SKILL.md`:

````markdown
---
name: jev-loop
description: A 24/7 paper-trading loop for Alpaca, any crypto pair or US equity. Every tick computes a deterministic state snapshot, fires a seven-question judgment battery at TypeSafe's Jev decision model (the Vercel AI Gateway is the normal route, a direct TypeSafe key is a faster optional extra, or a labelled mock), composes an action from your own strategy.py thresholds, prices with Avellaneda-Stoikov, checks nine hard risk limits, and executes on Alpaca paper by default. Live trading exists behind a deliberately awkward three-gate opt-in, off unless all three are set. Includes a live HTML dashboard and a calibration report.
---

# jev-loop

Install location: `~/.claude/skills/jev-loop/`.
Framework: Roan (@RohOnChain), "How to Use Jev to Build a 24/7 HFT Trading System". Installed as a Claude Code skill by Lewis Jackson.

## The split

Deterministic layer (your code): exact arithmetic (mid-price, spread, book
imbalance), hard metrics (inventory, drawdown, session VWAP), safety and
policy (stop-losses, risk vetoes, routing orders to the book).

Probabilistic layer (Jev): fuzzy conditions (trending, mean reverting,
chaotic), order quality (is flow toxic or noise), execution health (is
the setup optimal or degrading). Seven typed questions, one call, one
latency, none of them arithmetic and none of them "what should I do."

```
uv run python -m jevloop explain-split
```

prints the full two-column table with the file that owns each row.

## Invocation

Natural language, or directly:

```
cd ~/.claude/skills/jev-loop
uv run python -m jevloop run --paper --ticks 60 --symbol BTC/USD
uv run python -m jevloop run --paper --mock            # force the mock client (never places orders)
uv run python -m jevloop run --paper --dry-execution   # real data and a real battery, no orders sent
uv run python -m jevloop run --paper --forever         # run continuously, Ctrl+C or `kill <pid>` to stop
uv run python -m jevloop run --paper --forever --bar 30m  # one decision per 30-minute bar close (1m/5m/15m/30m/1h)
uv run python -m jevloop validate-symbol AAPL          # resolve any symbol before running on it
uv run python -m jevloop explain-split                 # the deterministic vs probabilistic table
uv run python -m jevloop calibrate                     # Brier score + reliability table
uv run python -m jevloop serve                         # dashboard at http://127.0.0.1:8765
uv run python -m jevloop pause                         # same as Stop on the dashboard: no new orders
uv run python -m jevloop resume                        # same as Start on the dashboard
```

**Start / Stop.** The dashboard has a Start and a Stop button and shows
RUNNING or PAUSED. Stop pauses new orders: the loop keeps reading the
market, asking Jev and updating the dashboard, pulls this run's resting
quotes, and places nothing until Start. It does not close positions. The
KILL switch (the hard risk limits) does that, and still fires while
paused. The state is kept in `~/.jev-loop/control.json`, so it survives a
page refresh and a restart, and the loop reads it before every order.
The buttons only work from the page `jevloop serve` hands out on
127.0.0.1: each press carries a per-install token from
`~/.jev-loop/control.token`, and the server sends no CORS headers.

`--ticks 0` means the same thing as `--forever`. Both cancel the resting
orders this run placed (and nothing else on the account) before exiting.

Ask Claude things like:

- "run the jev-loop skill for 100 ticks on ETH/USD"
- "run jev-loop on AAPL and tell me if the market's open"
- "run jev-loop in mock mode so I can see the dashboard without spending a key"
- "keep jev-loop running continuously in the background"
- "calibrate the jev-loop and show me the Brier score"
- "explain the split in jev-loop"

## Any asset

`--symbol` accepts any crypto pair (`BTC/USD`, `ETH/USD`, 24/7) or any US
equity ticker (`AAPL`, `SPY`, `TSLA`, `NVDA`, market hours only). The
default stays `BTC/USD` because it never closes. `jevloop/assets.py`
resolves the symbol into a spec: which Alpaca endpoints to call, the
minimum order notional, quantity precision, whether shorting is allowed,
and whether the venue is open right now. Orders are sized from a dollar
target (`notional_usd` in `limits.py`), not a fixed quantity, so the same
config works whether the asset is an $85,000 coin or a $30 stock.

Equities have no Level 2 depth on the basic feed: the state snapshot uses
best bid/ask and recent trades only, and marks the missing depth fields
absent rather than inventing them. When the equity market is closed, the
loop holds and never places an order; it says so on the tick line rather
than silently doing nothing.

## Your strategy lives in strategy.py

Everything this loop ships with is a harness, not an edge: a generic
strategy pulled out of thin air, wired in only so a demo run shows real
fills. `jevloop/strategy.py` is the one file built for you to edit --
it owns the seven tunable thresholds `compose_action()` reads (when to
pull quotes, widen, quote both sides or wide, and how confident Jev has
to be before a directional leg is taken), plus an `apply_strategy()` hook
called on every tick with the action already chosen, free to change it
or veto it outright. The shipped default matches exactly what the video
ran: change nothing here and nothing changes. The hard risk caps stay
separate, in `jevloop/limits.py`, and a strategy can never raise them,
only add more caution on top.

## What each file does

| File | Job |
|---|---|
| `jevloop/strategy.py` | The file you edit: the seven tunable thresholds behind `compose_action()`, plus the `apply_strategy()` hook to override or veto an action. Shipped default changes nothing. |
| `jevloop/limits.py` | The hard risk caps and operational numbers. Never overridable by a strategy. |
| `jevloop/assets.py` | Resolves any symbol into a spec: endpoints, notional floor, precision, shorting, market hours. |
| `jevloop/state.py` | Deterministic state snapshot, under ~400 tokens, real price history with the venue's own timestamps (one-minute bars backfilled at startup plus a mid sample every tick), each trade counted once in session VWAP, drawdown measured against real account equity, honest depth degradation. |
| `jevloop/split.py` | The allow-list of battery questions and the guard that refuses any question that looks like arithmetic. |
| `jevloop/battery.py` | The seven-question Jev battery (regime, direction, toxic flow, liquidity stress, quote environment, inventory pressure, execution health). |
| `jevloop/client.py` | Resolves the decision client: Vercel AI Gateway (the normal route) or a direct TypeSafe key (a faster optional extra) or a mock, prints which one won, pins and logs the model per response. Also the Jev call throttle (`JevThrottle`): one shared client, one call at a time, rate-limit backoff. |
| `jevloop/policy.py` | `compose_action()`, code, not Jev, turns seven answers into KILL / PULL_QUOTES / WIDEN / QUOTE_BOTH_SIDES / QUOTE_WIDE / STAND_DOWN using strategy.py's thresholds, plus a directional leg, then hands the result to strategy.py's hook. |
| `jevloop/pricing.py` | Avellaneda-Stoikov reservation price and half spread, worked out in basis points of mid so the spread scales with the price. |
| `jevloop/risk.py` | Nine hard limits, checked before every order, never delegated. |
| `jevloop/ladder.py` | The five-rung fallback ladder (RUN / REDUCE / HOLD_LATE / RULES_ONLY / KILL). |
| `jevloop/execution/alpaca.py` | Alpaca execution, crypto or equities. Paper by default; live trading exists only behind the three-gate opt-in (see Live trading below). Refuses to place an equity order while the market is closed. |
| `jevloop/loop.py` | The nine-stage block loop, one JSON line per tick to `~/.jev-loop/log.jsonl` and `~/.jev-loop/latest.json`. Supports `--forever` / `--ticks 0` with a clean shutdown that cancels only this run's resting orders. Fills are read back from Alpaca, never assumed; KILL sends a real closing order. |
| `jevloop/calibrate.py` | Brier score + 10-bin reliability table from the log, scoring Jev's confidence in each up/down call against whether price moved that way; `reliability.png` if matplotlib is present. |
| `jevloop/serve.py` | Tiny static server for `dashboard/index.html` and `dashboard/wall.html`, 127.0.0.1 only, plus the token-checked Start/Stop endpoint (`/control`). |
| `jevloop/control.py` | The RUNNING / PAUSED state file and the per-install token. The loop checks it before every order. |
| `dashboard/*.html` | Two live dashboards, polling `latest.json`. No simulation. `index.html` has the Start / Stop buttons. |
| `tests/` | pytest for policy thresholds, risk vetoes, the ladder, the Jev call throttle, state maths, the asset resolver, the split guard, the mock client's shape, the Alpaca paper-URL guard, the three-gate live-trading check, Start / Stop (pause blocks orders, resume, the token check), and the member-reported fixes (position cap counts working buys, spread in bps, stuck positions closed, clean-up on every exit, fees, rounded-down sells, network timeouts). |

## Setup

1. Copy `.env.example` to `.env` in this folder and fill in what you have.
2. `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` are required, paper keys only,
   from https://app.alpaca.markets/paper/dashboard/overview. Paper keys
   start with `PK`.
3. `AI_GATEWAY_API_KEY` is the normal way to reach Jev: works today, no
   invite or waitlist, but the Vercel team needs a card on file before
   the gateway will serve requests, even the free credits. A few dollars
   covers roughly a month at this tick rate. `TYPESAFE_API_KEY` is an
   optional extra, slightly faster (one less hop), useful only if you are
   already off TypeSafe's waitlist. Without either, the loop runs on a
   clearly-labelled mock decision client so nothing above blocks on a
   billing page or a waitlist. Mock runs are always dry: no orders.
   Jev is called on a throttle, not every tick: see "Jev call rate" below.
4. `DEFAULT_SYMBOL` is optional; it sets what `--symbol` defaults to if
   you don't pass one.

## Live trading (opt-in, off by default)

Paper is the default everywhere in this skill. Turning on live trading
needs all three of the following, together, every time:

1. the `--live` flag on the command line
2. `JEV_LOOP_ALLOW_LIVE=i-understand-the-risk` in the environment
3. typing the exact confirmation phrase the CLI asks for at startup

Missing any one of the three refuses to start; it never falls back to
paper silently. All three present routes every order to Alpaca's live
endpoint instead of paper, with real money and no safety net beyond the
risk caps in `limits.py`, which still apply and are not raised by going
live. This is the "flip of a switch" the video describes, made
deliberately awkward on purpose so it only ever happens on purpose. See
README.md for the exact commands.

## Dependencies

`uv`-managed virtual environment under `.venv/` with Python 3.10+ and:

- `requests>=2.31`
- `python-dotenv>=1.0`
- `matplotlib>=3.8` (optional, only for `reliability.png`)
- `pytest>=8.0` (dev only, for `tests/`)

## What this is not

Paper by default, everywhere. Live trading exists only behind the
three-gate opt-in above and starts with the same small dollar caps as
paper. This does not claim a profit. It cannot turn a bad strategy into
a good one: Jev makes seven judgments cheap and fast, edge is still
yours, and yours lives in strategy.py.
````

Write `~/.claude/skills/jev-loop/README.md`:

````markdown
# jev-loop

A 24/7 paper-trading loop built around a Jev decision battery, for the video
*How to Use Jev to Build a 24/7 HFT Trading System*.

The split, in one sentence: code computes the state, Jev answers seven typed
questions about it in one call, your code composes those answers into an
action using thresholds you set in `strategy.py`, a risk engine can veto
any of it, and execution defaults to Alpaca's paper API everywhere.

## Quick start

```bash
cd ~/.claude/skills/jev-loop
cp .env.example .env        # fill in ALPACA_API_KEY / ALPACA_SECRET_KEY at minimum
uv run pytest -q             # tests, no network needed
uv run python -m jevloop explain-split         # the split, as a table
uv run python -m jevloop validate-symbol AAPL  # resolve any symbol first
uv run python -m jevloop run --paper --ticks 30 --symbol BTC/USD
uv run python -m jevloop serve   # open http://127.0.0.1:8765
```

## Start and Stop

The dashboard has a **Start** and a **Stop** button, and shows **RUNNING**
or **PAUSED** next to them.

- **Stop** pauses new orders. The loop keeps running: it still reads the
  market, asks Jev, writes the log and updates the dashboard. It pulls
  the quotes this run has resting so nothing new fills, then places no
  orders until you press Start.
- **Stop does not close positions.** Whatever you hold stays held. The
  KILL switch (the hard risk limits, such as the drawdown cap) is what
  closes a position, and it still works while paused.
- **Start** lets it place orders again from the next tick.
- The state is saved in `~/.jev-loop/control.json`, so it stays the same
  after a page refresh or a restart. The loop checks it before every order.
- No dashboard open? `uv run python -m jevloop pause` and
  `uv run python -m jevloop resume` do the same thing from a terminal.

The buttons only work from the page `jevloop serve` gives you at
http://127.0.0.1:8765. The server only listens on your own machine, each
press is a POST carrying a random token made for your install (in
`~/.jev-loop/control.token`), and it sends no CORS headers, so another
website open in your browser can't press Stop or Start for you. Same on
Mac, Windows and Linux.

`--symbol` takes any crypto pair (24/7) or US equity ticker (market hours
only); `jevloop/assets.py` resolves it into endpoints, order-size rules,
and session rules. Orders are sized from a dollar target, not a fixed
quantity, so the same defaults work across assets.

No `AI_GATEWAY_API_KEY` or `TYPESAFE_API_KEY`? The loop runs on a
clearly-labelled mock decision client. It says so on the first line. The
mock answers with random numbers, so it never places orders, not even on
paper: a mock run is always a dry run.

## Running continuously

A plain run stops after `--ticks N`. To keep it going:

```bash
uv run python -m jevloop run --paper --forever --symbol BTC/USD
# or, equivalently:
uv run python -m jevloop run --paper --ticks 0 --symbol BTC/USD
```

Add `--bar 30m` (or `1m`, `5m`, `15m`, `1h`) to decide once per bar close,
UTC-aligned, instead of every 2 s. Returns and volatility still come from
real one-minute bars, refreshed at each close.

Stop it with Ctrl+C in the foreground. In the background:

```bash
nohup uv run python -m jevloop run --paper --forever --symbol BTC/USD \
  > ~/.jev-loop/continuous.log 2>&1 &
echo $! > ~/.jev-loop/continuous.pid
# ...later...
kill "$(cat ~/.jev-loop/continuous.pid)"
```

On Windows PowerShell there is no `nohup` or `kill`, and `jevloop` needs
the keys from `.env` loaded by uv. Run it in its own minimised window and
stop it with Ctrl+C in that window (a `Stop-Process` is a hard stop that
skips the order clean-up below):

```powershell
Start-Process powershell -WindowStyle Minimized -WorkingDirectory "$HOME\.claude\skills\jev-loop" -ArgumentList "-NoExit", "-Command", "uv run --env-file .env python -m jevloop run --paper --forever"
```

Either way, on Ctrl+C or `kill` the loop cancels the resting orders it
placed itself before it exits rather than leaving them open. It never
touches other orders on your Alpaca account. The dashboard (`jevloop
serve`) keeps reading the same `~/.jev-loop/latest.json` regardless of
whether the run is bounded or continuous.

## Your strategy lives in strategy.py

Everything this loop ships with is a harness, not an edge: a generic
strategy pulled out of thin air, wired in only so a demo run shows real
fills. `jevloop/strategy.py` owns the seven tunable thresholds behind
`compose_action()` and an `apply_strategy()` hook that gets one last
look at every action before it goes near an order, free to change or
veto it. The shipped default matches exactly what the video ran.

## The nine-stage loop

```
block event -> read the book -> state snapshot -> battery (seven Jev judgments)
  -> policy engine (strategy.py's thresholds + hook) -> pricing (Avellaneda-Stoikov, your code)
  -> risk veto (your code, absolute) -> post-only quotes + directional leg
  -> log, fills, inventory
```

## Jev call rate

The Vercel AI Gateway allows roughly 20 to 30 requests a minute. A loop
that calls Jev every tick (every 2s, or every 500ms if you shorten the
tick) runs straight into "access frequency is too high". So the loop
never does that:

- The fast loop runs every tick on price and risk, and reuses the last
  Jev judgment between calls.
- Jev is called at most once every `JEV_MIN_INTERVAL_S` seconds (default
  4, so 15 a minute), or sooner when the state changes materially: price
  or spread moves `JEV_MATERIAL_MOVE_BPS` (default 15 bps) or the
  position flips. Even then never more often than `JEV_MIN_GAP_S`
  (default 3s, 20 a minute).
- On a 429 or a "frequency" error the loop backs off exponentially (5s,
  10s, 20s, up to 120s) and keeps the last judgment meanwhile.
- A judgment older than `JEV_MAX_JUDGMENT_AGE_S` (default 60s) is not
  reused: the ladder drops to RULES_ONLY until Jev answers again.
- One shared client, one call at a time. Never parallel Jev calls, never
  a second client or a thread pool.

A direct `TYPESAFE_API_KEY` allows higher rates than the gateway, so with
one you can lower `JEV_MIN_INTERVAL_S` and `JEV_MIN_GAP_S` in `.env`.

## The fallback ladder

```
healthy + high confidence -> RUN
healthy + low confidence  -> REDUCE
late past the tick budget -> HOLD_LATE (never quote on stale state)
Jev unavailable            -> RULES_ONLY (deterministic fallback, no model)
hard limit breached        -> KILL (cancel own orders, market-close the position it built, stop)
```

## Live trading (opt-in, off by default)

Paper is the default everywhere: `execution/alpaca.py` will not reach
Alpaca's live endpoint unless all three of the following are true at
once.

```bash
export JEV_LOOP_ALLOW_LIVE=i-understand-the-risk
uv run python -m jevloop run --live --ticks 30 --symbol BTC/USD
# then type the exact confirmation phrase the CLI prints and asks for
```

Windows PowerShell sets the variable with
`$env:JEV_LOOP_ALLOW_LIVE = "i-understand-the-risk"` and runs
`uv run --env-file .env python -m jevloop run --live --ticks 30 --symbol BTC/USD`.

Missing the environment variable, missing `--live`, or typing anything
other than the exact confirmation phrase refuses to start; it never
falls back to paper silently. This is real money with no paper safety
net, at the same small dollar caps `limits.py` enforces on paper -- a
strategy can never raise them. Treat `--live` as what it is: a flip of
a switch made deliberately awkward so it only ever happens on purpose.

## Safety

- Paper by default, everywhere. Live trading exists only behind the
  three-gate opt-in above.
- The hard risk caps live in `jevloop/limits.py` and never change between
  paper and live. The tunable strategy thresholds live in `jevloop/strategy.py`
  instead -- change a number, restart, see different behaviour.
- The risk engine (`jevloop/risk.py`) never calls Jev and never delegates,
  and runs after `strategy.py`'s hook has had its say, not before.
- Long or flat only. Alpaca crypto is spot and this account can't short,
  so a SELL signal closes the long this run holds (never more than Alpaca
  says is held) and does nothing when flat ("no position to close").
- Stop on the dashboard pauses new orders and never closes a position;
  the KILL switch closes positions and still works while paused.
- This is not investment advice and it does not claim a profit. It is a
  scaffold for a decision battery, a policy engine, and a risk layer around
  a fast model. Edge is still your job, and it lives in `strategy.py`.
````

Write `~/.claude/skills/jev-loop/.env.example`:

```bash
# Copy this file to .env in the same folder (~/.claude/skills/jev-loop/.env)
# and fill in what you have. The loop works with none of these set --
# it falls back to a clearly-labelled mock decision client and will not
# start execution without a working Alpaca paper key.

# --- Alpaca (paper trading only, required to run the loop at all) ---
# Get these from https://app.alpaca.markets/paper/dashboard/overview
# under "Your API Keys" -> Generate New Keys. Must be the PAPER dashboard,
# not the live one -- paper keys start with PK.
ALPACA_API_KEY=
ALPACA_SECRET_KEY=

# --- Jev decision client (optional, falls back to the mock if unset) ---
# The normal route: a Vercel AI Gateway key. Works today, no invite and no
# waitlist. Create a team at https://vercel.com/dashboard, go to AI Gateway
# -> API keys, and generate one. The gateway needs a card on file on the
# team before it will serve requests, even the free starting credits --
# add one under the team's billing settings first. A few dollars covers
# roughly a month at this tick rate.
AI_GATEWAY_API_KEY=

# Optional extra, not required: a direct TypeSafe key skips the gateway's
# one extra network hop, so it is slightly faster if you already have one.
# Only useful if you are already off TypeSafe's waitlist at https://typesafe.ai
# -- if you are not, the gateway route above works today without it.
# A direct key also allows higher request rates than the gateway.
TYPESAFE_API_KEY=

# --- Jev call rate (the gateway allows roughly 20 to 30 requests a minute) ---
# The loop reuses the last judgment between calls. Lower these only with a
# direct TypeSafe key.
JEV_MIN_INTERVAL_S=4
JEV_MIN_GAP_S=3
JEV_MATERIAL_MOVE_BPS=15
JEV_MAX_JUDGMENT_AGE_S=60

# --- DEFAULT_SYMBOL is set automatically once you resolve an asset (Phase 6) ---

# --- Live trading: OFF by default, paper everywhere unless you opt in ---
# This skill only ever trades Alpaca PAPER unless ALL THREE of the following
# are true at once: this variable is set exactly as shown, the loop is
# started with --live, and you type the confirmation phrase it asks for at
# startup. Missing any one of the three refuses to start rather than
# silently falling back to paper. Real money, real orders, no safety net.
# Leave this blank unless you mean it.
# JEV_LOOP_ALLOW_LIVE=i-understand-the-risk
```

Write `~/.claude/skills/jev-loop/.gitignore`:

```text
.venv/
__pycache__/
*.pyc
.env
```

Write `~/.claude/skills/jev-loop/pyproject.toml`:

```toml
[project]
name = "jev-loop"
version = "0.1.0"
description = "A 24/7 paper-trading loop: deterministic state, a seven-question Jev battery, code-owned policy and risk, Alpaca paper execution."
requires-python = ">=3.10"
dependencies = [
    "requests>=2.31",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
calibrate = ["matplotlib>=3.8"]
dev = ["pytest>=8.0"]

[project.scripts]
jev-loop = "jevloop.__main__:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["jevloop*"]
```

Write `~/.claude/skills/jev-loop/jevloop/__init__.py`:

```python
"""jev-loop: a 24/7 trading loop built around a Jev decision battery.

Code computes the state. Jev answers seven typed questions about it. Code
(policy.py, using strategy.py's thresholds and hook) decides. Code
(risk.py, using limits.py's hard caps) can veto anything. Execution
(execution/alpaca.py) defaults to Alpaca's paper API everywhere; live
trading exists only behind a deliberately awkward three-gate opt-in.
"""

__version__ = "0.1.0"
```

Write `~/.claude/skills/jev-loop/jevloop/limits.py`:

```python
"""The hard risk caps, in one place. Never overridable by a strategy.

This is not the file you edit to change how the loop trades: that file is
strategy.py, which owns the tunable thresholds compose_action() uses and
a hook that can override or veto its output. This file owns the ceiling
that hook can never raise: nine limits, checked in risk.py before every
order, plus the operational numbers for ladder.py, pricing.py, and
execution/alpaca.py.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Limits:
    # --- risk.py hard vetoes (checked before every order, never delegated) ---
    # Expressed in dollars, not base units, so the same defaults make sense
    # whether the asset is an $85,000 coin or a $30 stock.
    max_position_usd: float = 50.0  # max absolute position value
    max_daily_loss_usd: float = 25.0  # kill switch on realised + unrealised loss today
    max_drawdown_pct: float = 0.05  # kill switch: 5% below the session high-water mark
    max_order_notional_usd: float = 25.0  # dollar value of a single order
    max_inventory_age_s: float = (
        900.0  # 15 minutes holding non-flat inventory: stop adding, close it out
    )
    max_stale_data_age_s: float = 5.0  # market data older than this is refused
    max_api_errors: int = 5  # consecutive broker/API errors before kill
    max_decision_latency_ms: float = (
        2000.0  # Jev slower than this on a block = late, hold
    )
    max_leverage: float = 1.0  # spot/cash only, no leverage, ever

    # The seven policy thresholds compose_action() used to read from here
    # (toxic flow, liquidity stress, quote environment, inventory pressure,
    # direction confidence) now live in strategy.py as StrategyThresholds.
    # That is the file you edit to change how the loop decides. This file
    # stays the hard ceiling a strategy can never raise.

    # --- ladder.py ---
    low_confidence_threshold: float = (
        0.50  # below this on a taken decision -> REDUCE rung
    )
    reduce_size_factor: float = 0.5  # order size multiplier while on the REDUCE rung

    # --- pricing.py (Avellaneda-Stoikov) ---
    as_gamma: float = 0.10  # risk aversion
    as_kappa: float = 1.5  # order book liquidity / arrival-rate parameter
    as_horizon_s: float = 60.0  # T - t, the inventory-clearing horizon in seconds
    min_half_spread_bps: float = 2.0  # quotes never tighter than this each side of mid
    max_half_spread_bps: float = 50.0  # nor wider than this

    # --- execution/alpaca.py ---
    tick_seconds: float = 2.0  # "block" = one tick of this loop. See README for why 2s.
    rest_ticks: int = 3  # rest a resting quote this many ticks before cancel-replace
    quote_notional_usd: float = 20.0  # dollar target for each side of a quote
    directional_notional_usd: float = (
        20.0  # dollar target for the directional-leg order
    )
    max_alpaca_calls_per_minute: int = (
        90  # stays under Alpaca's free-tier data/trading limits
    )
```

Write `~/.claude/skills/jev-loop/jevloop/assets.py`:

```python
"""Asset resolver: turns any symbol into a spec.

Two asset classes: crypto (24/7, e.g. BTC/USD, ETH/USD) and us_equity
(market hours only, e.g. AAPL, SPY, TSLA, NVDA). Everything asset-specific,
which Alpaca endpoints to call, how big an order must be, how many
decimals a quantity can have, whether shorting is allowed, whether the
venue is open right now, lives here. The rest of the loop reads an
AssetSpec and never special-cases a symbol.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

CRYPTO_DATA_BASE = "https://data.alpaca.markets/v1beta3/crypto/us"
EQUITY_DATA_BASE = "https://data.alpaca.markets/v2/stocks"

_CRYPTO_PATTERN = re.compile(r"^[A-Z0-9]{2,10}/(USD|USDT|USDC)$")
_EQUITY_PATTERN = re.compile(r"^[A-Z]{1,5}$")

# Tick sizes for the symbols the video and the article actually name.
# Anything else falls back to the class default below.
_KNOWN_TICK_SIZE = {
    "BTC/USD": 0.01,
    "ETH/USD": 0.01,
}


class UnknownSymbolError(Exception):
    pass


@dataclass(frozen=True)
class AssetSpec:
    symbol: str
    asset_class: str  # "crypto" | "us_equity"
    tick_size: float
    min_notional_usd: float
    qty_precision: int
    shorting_allowed: bool
    is_24_7: bool
    has_depth: bool  # False on venues where only best bid/ask is available
    orderbook_url: str | None
    latest_trade_url: str
    recent_trades_url: str
    latest_quote_url: str


def resolve_symbol(raw: str) -> AssetSpec:
    """Resolve any symbol Lewis (or the viewer) might type. Raises
    UnknownSymbolError with a plain-English message on anything that
    matches neither a crypto pair nor a US equity ticker."""
    sym = raw.strip().upper()

    if _CRYPTO_PATTERN.match(sym):
        return AssetSpec(
            symbol=sym,
            asset_class="crypto",
            tick_size=_KNOWN_TICK_SIZE.get(sym, 0.01),
            min_notional_usd=10.0,  # Alpaca's crypto minimum order notional
            qty_precision=8,
            shorting_allowed=False,  # spot only, no naked shorting
            is_24_7=True,
            has_depth=True,  # crypto v1beta3 gives real L2 depth
            orderbook_url=f"{CRYPTO_DATA_BASE}/latest/orderbooks",
            latest_trade_url=f"{CRYPTO_DATA_BASE}/latest/trades",
            recent_trades_url=f"{CRYPTO_DATA_BASE}/trades",
            latest_quote_url=f"{CRYPTO_DATA_BASE}/latest/quotes",
        )

    if _EQUITY_PATTERN.match(sym):
        return AssetSpec(
            symbol=sym,
            asset_class="us_equity",
            tick_size=0.01,
            min_notional_usd=1.0,  # Alpaca supports fractional notional equity orders
            qty_precision=4,
            shorting_allowed=False,  # this account is cash, not marginable
            is_24_7=False,
            has_depth=False,  # the basic equities feed has no L2 book
            orderbook_url=None,
            latest_trade_url=f"{EQUITY_DATA_BASE}/trades/latest",
            recent_trades_url=f"{EQUITY_DATA_BASE}/trades",
            latest_quote_url=f"{EQUITY_DATA_BASE}/quotes/latest",
        )

    raise UnknownSymbolError(
        f"'{raw}' does not look like a crypto pair (BTC/USD, ETH/USD, ...) or a "
        "US equity ticker (AAPL, SPY, TSLA, NVDA, ...). Pick one of those forms."
    )


def size_order(notional_usd: float, price: float, spec: AssetSpec) -> float:
    """Convert a target notional (dollars) into a quantity, rounded to the
    asset's precision, bumped up if rounding pushed it back under the
    venue's minimum notional.

    Sizing by notional rather than a fixed quantity is the fix for a real
    bug: a fixed 0.0002 BTC order is comfortably above Alpaca's $10 crypto
    minimum most of the time, but the same fixed quantity on a $30 stock,
    or during a crypto drawdown, can fall under the venue floor and get
    rejected. Sizing from a dollar target is honest across any asset and
    any price.
    """
    if price <= 0:
        raise ValueError("price must be positive")
    target = max(notional_usd, spec.min_notional_usd)
    qty = target / price
    quantized = round(qty, spec.qty_precision)
    if quantized * price < spec.min_notional_usd:
        step = 10 ** (-spec.qty_precision)
        guard = 0
        while quantized * price < spec.min_notional_usd and guard < 10_000:
            quantized = round(quantized + step, spec.qty_precision)
            guard += 1
    return quantized
```

Write `~/.claude/skills/jev-loop/jevloop/state.py`:

```python
"""The deterministic state snapshot.

Everything computable stays in code. This module never calls Jev. It turns
an order book (or, on venues with no L2 depth, best bid/ask), a slice of
recent trades, and the loop's own bookkeeping (inventory, PnL, health,
session VWAP) into one compact dict under roughly 400 tokens.

Timestamp discipline: every price, trade and fill carries the real
timestamp the venue stamped on it (or, for the loop's own mid samples, the
wall-clock time it was read). Every field is computed only from points at
or before `as_of`, so nothing that happened after the decision clock
started can leak into the snapshot.

Honest degradation: on an asset with no Level 2 depth (US equities on the
basic feed), the caller passes empty depth lists rather than fabricated
ones. `imbalance` and the depth fields come back `None` / empty in that
case instead of a fake "balanced" reading.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _pct_return(
    prices: list[tuple[float, float]], now: float, lookback_s: float
) -> float | None:
    """Return over the last lookback_s seconds using only points before `now`."""
    past = [p for ts, p in prices if ts <= now - lookback_s]
    current = [p for ts, p in prices if ts <= now]
    if not past or not current:
        return None
    base = past[-1]
    latest = current[-1]
    if base == 0:
        return None
    return (latest - base) / base


def _realised_vol(
    prices: list[tuple[float, float]],
    now: float,
    window_s: float,
    step_s: float = 60.0,
) -> float | None:
    """Realised volatility: stdev of log returns on a fixed `step_s` grid
    inside the window, using only points at or before `now`. The loop's
    history mixes one-minute bars (the startup backfill) with a real mid
    sample every tick, so the series is resampled to one grid before any
    return is taken: the last real price at or before each grid time.
    Returns None rather than a number when there is not enough real
    history yet."""
    import math

    pts = sorted((ts, p) for ts, p in prices if ts <= now and p > 0)
    if not pts:
        return None
    n_steps = int(window_s // step_s)
    grid = [now - k * step_s for k in range(n_steps, -1, -1)]
    sampled = []
    j = 0
    last = None
    for g in grid:
        while j < len(pts) and pts[j][0] <= g:
            last = pts[j][1]
            j += 1
        if last is not None:
            sampled.append(last)
    if len(sampled) < 3:
        return None
    rets = [math.log(b / a) for a, b in zip(sampled, sampled[1:])]
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(max(var, 0.0))


@dataclass
class InventoryState:
    """The loop's own bookkeeping, carried tick to tick. Not fetched from
    Alpaca. Session VWAP and slippage are both computed here, in code:
    Jev never sees a raw trade tape, only the numbers this file derives
    from it."""

    inventory: float = 0.0
    entry_price: float = 0.0
    position_opened_at: float | None = None
    realised_pnl_usd: float = 0.0
    high_water_mark_usd: float = 0.0
    equity_usd: float = 0.0  # starting equity; seeded from the account at startup
    fills: int = 0
    fees_usd: float = 0.0  # fees Alpaca took (crypto buys pay theirs in coin)
    orders_submitted: int = 0
    orders_rejected: int = 0
    api_error_streak: int = 0
    recent_latencies_ms: list[float] = field(default_factory=list)
    recent_slippage_bps: list[float] = field(default_factory=list)
    # Session VWAP accumulators. Reset when the loop process restarts;
    # that is an honest limitation (documented in README.md), not a bug.
    vwap_cum_pv: float = 0.0
    vwap_cum_vol: float = 0.0
    vwap_last_trade_ts: float = 0.0


def update_vwap(inv: InventoryState, trades: list[tuple[float, float, float]]) -> None:
    """Fold newly-seen trades (timestamp, price, size) into the running
    session VWAP accumulators. Only trades strictly newer than the last
    one already folded in are counted, so calling this every tick with an
    overlapping recent-trades window never double-counts a fill."""
    newest_ts = inv.vwap_last_trade_ts
    for ts, price, size in trades:
        if ts <= inv.vwap_last_trade_ts:
            continue
        if price <= 0 or size <= 0:
            continue
        inv.vwap_cum_pv += price * size
        inv.vwap_cum_vol += size
        newest_ts = max(newest_ts, ts)
    inv.vwap_last_trade_ts = newest_ts


def record_fill_slippage(
    inv: InventoryState, expected_price: float, fill_price: float, side: str
) -> None:
    """Signed slippage in basis points: positive means the fill was worse
    than expected (paid more on a buy, received less on a sell)."""
    if expected_price <= 0:
        return
    sign = 1.0 if side == "buy" else -1.0
    bps = sign * (fill_price - expected_price) / expected_price * 10_000
    inv.recent_slippage_bps.append(round(bps, 2))
    inv.recent_slippage_bps = inv.recent_slippage_bps[-10:]


def apply_fill(
    inv: InventoryState, side: str, qty: float, price: float, ts: float
) -> None:
    """Fold one confirmed fill (from the broker, never an assumed one) into
    inventory, average entry price and realised PnL. Average-cost
    accounting: reducing a position realises (price - entry) on the
    reduced quantity; crossing through zero opens the remainder at the
    fill price."""
    if qty <= 0 or price <= 0:
        return
    signed = qty if side == "buy" else -qty
    old = inv.inventory
    new = old + signed
    if old == 0 or (old > 0) == (signed > 0):
        # opening or adding: new weighted-average entry
        inv.entry_price = (
            (inv.entry_price * abs(old) + price * qty) / abs(new) if new else 0.0
        )
        if old == 0:
            inv.position_opened_at = ts
    else:
        closed = min(abs(old), qty)
        direction = 1.0 if old > 0 else -1.0
        inv.realised_pnl_usd += (price - inv.entry_price) * closed * direction
        if abs(new) < 1e-12:
            new = 0.0
            inv.entry_price = 0.0
            inv.position_opened_at = None
        elif (new > 0) != (old > 0):
            inv.entry_price = price
            inv.position_opened_at = ts
    inv.inventory = new
    inv.fills += 1


def build_snapshot(
    *,
    as_of: float,
    mid: float,
    microprice: float,
    spread_bps: float,
    bid_depth: list[tuple[float, float]],
    ask_depth: list[tuple[float, float]],
    trade_prices: list[tuple[float, float]],
    trade_sides: list[tuple[float, str]],
    inv: InventoryState,
    data_timestamp: float,
    has_depth: bool = True,
) -> dict:
    """Assemble the deterministic snapshot. All list inputs must already be
    filtered to timestamps <= as_of by the caller (execution/alpaca.py).

    `has_depth` is False for venues with no Level 2 book (equities on the
    basic feed): `bid_depth`/`ask_depth` are then expected to hold at most
    one (price, size) pair each, taken from the best bid/ask of the latest
    quote, and `imbalance` is computed from that single level rather than
    three, or left `None` if even that is unavailable."""

    bid_sz = sum(sz for _, sz in bid_depth[:3])
    ask_sz = sum(sz for _, sz in ask_depth[:3])
    if bid_sz + ask_sz > 0:
        imbalance = round((bid_sz - ask_sz) / (bid_sz + ask_sz), 4)
    else:
        imbalance = None

    recent_trades = [(ts, side) for ts, side in trade_sides if ts <= as_of]
    window_trades = [s for ts, s in recent_trades if ts >= as_of - 30.0]
    buys = sum(1 for s in window_trades if s == "buy")
    aggressive_buy_ratio = buys / len(window_trades) if window_trades else 0.5
    trade_intensity = len(window_trades) / 30.0  # trades per second, trailing 30s

    unrealised_pnl = (mid - inv.entry_price) * inv.inventory if inv.inventory else 0.0
    # equity_usd is the starting equity the loop was seeded with (the real
    # account equity at startup), so drawdown is measured against real money,
    # never against zero. The loop raises high_water_mark_usd tick by tick.
    equity = inv.equity_usd + inv.realised_pnl_usd + unrealised_pnl
    peak = max(inv.high_water_mark_usd, equity)
    drawdown_pct = (peak - equity) / peak if peak > 0 else 0.0
    position_age_s = (
        (as_of - inv.position_opened_at)
        if (inv.inventory and inv.position_opened_at)
        else 0.0
    )

    fill_ratio = (
        min(1.0, inv.fills / inv.orders_submitted) if inv.orders_submitted else 1.0
    )
    data_age_s = max(0.0, as_of - data_timestamp)

    vwap = inv.vwap_cum_pv / inv.vwap_cum_vol if inv.vwap_cum_vol > 0 else mid

    return {
        "as_of": as_of,
        # PRICE
        "mid": mid,
        "microprice": microprice,
        "vwap": round(vwap, 6),
        "return_1m": _pct_return(trade_prices, as_of, 60),
        "return_5m": _pct_return(trade_prices, as_of, 300),
        "return_30m": _pct_return(trade_prices, as_of, 1800),
        # BOOK (depth fields are honestly empty/None where the venue has no L2 book)
        "spread_bps": spread_bps,
        "has_depth": has_depth,
        "depth_levels_available": (
            min(len(bid_depth), len(ask_depth)) if has_depth else 0
        ),
        "bid_depth_3": [[p, s] for p, s in bid_depth[:3]],
        "ask_depth_3": [[p, s] for p, s in ask_depth[:3]],
        "imbalance": imbalance,
        # FLOW
        "aggressive_buy_ratio": round(aggressive_buy_ratio, 4),
        "trade_intensity_per_s": round(trade_intensity, 4),
        # VOL
        "realised_vol_short": _realised_vol(trade_prices, as_of, 300),
        "realised_vol_medium": _realised_vol(trade_prices, as_of, 1800),
        # BOOK PnL
        "inventory": inv.inventory,
        "unrealised_pnl_usd": round(unrealised_pnl, 4),
        "daily_loss_usd": round(max(0.0, -inv.realised_pnl_usd - unrealised_pnl), 4),
        "drawdown_pct": round(drawdown_pct, 6),
        "position_age_s": round(position_age_s, 1),
        # HEALTH
        "fill_ratio": round(fill_ratio, 4),
        "reject_count": inv.orders_rejected,
        "last_10_latencies_ms": inv.recent_latencies_ms[-10:],
        "last_10_slippage_bps": inv.recent_slippage_bps[-10:],
        "data_age_s": round(data_age_s, 3),
        "leverage": 1.0,
    }


def approx_token_count(snapshot: dict) -> int:
    """Rough token estimate (chars / 4) so the loop can print a sanity check
    that the snapshot stays well under the 400-token guideline."""
    import json

    return len(json.dumps(snapshot, default=str)) // 4
```

Write `~/.claude/skills/jev-loop/jevloop/split.py`:

```python
"""The split, enforced.

Deterministic layer (your code): exact arithmetic, hard metrics, safety
and policy. Probabilistic layer (Jev): fuzzy conditions, order-quality
judgments, execution-health judgments. Everything else in this scaffold
is built around that split; this file is the guard that keeps the second
half honest. It is the one place a battery question is allowed to be
defined, and it refuses anything whose instructions look like a request
for arithmetic rather than a judgment.
"""

from __future__ import annotations

# question id -> (Jev question type, the judgment it makes, not a calculation)
ALLOWED_QUESTIONS: dict[str, tuple[str, str]] = {
    "regime": (
        "choice",
        "is the market trending, mean reverting, high vol, or in crisis",
    ),
    "direction": (
        "choice",
        "price bias over the next few ticks, a judgment, not a forecast formula",
    ),
    "toxic_flow": ("noul", "is the aggressive flow informed rather than noise"),
    "liquidity_stressed": ("noul", "is the book thinner than its recent norm"),
    "quote_environment": (
        "score",
        "how favourable this state is for providing liquidity",
    ),
    "inventory_pressure": ("score", "how urgent it is to cut the current position"),
    "execution_health": ("score", "whether execution quality is optimal or degrading"),
}

# Substrings that mean "this is asking Jev to do arithmetic", banned in any
# question's instructions. Deliberately conservative: false positives (a
# legitimate judgment question that happens to use one of these words) are
# a cheap price for never silently shipping an arithmetic question to a
# model that is supposed to answer judgments, not calculate.
_ARITHMETIC_MARKERS = (
    "calculate",
    "compute the",
    "what is the exact",
    "sum of",
    "average of",
    "mean of",
    "add up",
    "multiply",
    "divide by",
    "vwap",
    "moving average",
    "standard deviation",
    "variance of",
    "exact value",
    "precise value",
    "spread in bps",
    "mid price of",
)


class SplitViolation(Exception):
    """Raised when a question sent to Jev is off the allow-list, or its
    instructions look like a request for a computable quantity instead of
    a judgment."""


def _instructions_text(instructions) -> str:
    if isinstance(instructions, str):
        return instructions
    if isinstance(instructions, dict):
        return " ".join(_instructions_text(v) for v in instructions.values())
    if isinstance(instructions, list):
        return " ".join(_instructions_text(v) for v in instructions)
    return str(instructions)


def assert_split_respected(questions: dict) -> None:
    """Raise SplitViolation if any question is off the allow-list, or its
    instructions contain an arithmetic marker. Call this on every battery
    before it is sent, not just once at startup: a question dict built at
    runtime is exactly the case this guard exists for."""
    for qid, question in questions.items():
        if qid not in ALLOWED_QUESTIONS:
            raise SplitViolation(
                f"question '{qid}' is not on the allow-list in jevloop/split.py. "
                "Add it there first, naming the judgment (not the calculation) it makes."
            )
        text = _instructions_text(question.get("instructions", "")).lower()
        for marker in _ARITHMETIC_MARKERS:
            if marker in text:
                raise SplitViolation(
                    f"question '{qid}' looks like it asks Jev to do arithmetic "
                    f"(found '{marker}'). Compute it in code (state.py) instead, and if "
                    "you need Jev's read on the result, ask a judgment question about it."
                )


def deterministic_rows() -> list[tuple[str, str]]:
    """(what your code owns, which module owns it)."""
    return [
        (
            "Exact arithmetic: mid-price, microprice, bid-ask spread, order book imbalance",
            "state.py",
        ),
        (
            "Hard metrics: live inventory, current drawdown, session VWAP",
            "state.py",
        ),
        (
            "Safety and policy: hard stop-losses, risk vetoes, routing limit orders to the book",
            "risk.py, policy.py, execution/alpaca.py",
        ),
    ]


def probabilistic_rows() -> list[tuple[str, str]]:
    """(what Jev owns, which battery question(s) implement it)."""
    return [
        (
            "Fuzzy conditions: trending, mean reverting, chaotic",
            "battery.py: regime, direction",
        ),
        (
            "Order quality: is incoming flow toxic/informed or just noise",
            "battery.py: toxic_flow, liquidity_stressed",
        ),
        (
            "Execution health: is setup quality optimal or has execution degraded",
            "battery.py: quote_environment, inventory_pressure, execution_health",
        ),
    ]


def render_split_table(width: int = 34) -> str:
    """Plain-text two-column table for the CLI and the install prompt.

    Each side lists its rows, wrapped to `width` characters, with the
    owning module(s) on the line under each row in brackets.
    """
    import textwrap

    def block(rows: list[tuple[str, str]]) -> list[str]:
        out: list[str] = []
        for desc, module in rows:
            out.extend(textwrap.wrap(desc, width))
            out.append(f"[{module}]")
            out.append("")
        return out

    left_lines = block(deterministic_rows())
    right_lines = block(probabilistic_rows())

    header_l = "DETERMINISTIC (your code)".ljust(width)
    header_r = "PROBABILISTIC (Jev)"
    rule = "-" * width
    lines = [f"{header_l}  {header_r}", f"{rule}  {rule}"]

    for i in range(max(len(left_lines), len(right_lines))):
        left = left_lines[i] if i < len(left_lines) else ""
        right = right_lines[i] if i < len(right_lines) else ""
        lines.append(f"{left.ljust(width)}  {right}")

    return "\n".join(lines).rstrip()
```

Write `~/.claude/skills/jev-loop/jevloop/client.py`:

```python
"""Resolves a decision client: TypeSafe direct, then the Vercel AI Gateway,
then a mock. Prints one banner line naming the winner. Every response is
logged with the model that actually answered, because confidence gates are
calibrated to one model and a silent upgrade breaks them quietly.

Resolution order (matches the article's setup notes and Lewis's gateway
verification on 2026-09-21):
  1. TYPESAFE_API_KEY  -> https://api.typesafe.ai/v1/systemone, model jev-latest
  2. AI_GATEWAY_API_KEY -> https://ai-gateway.vercel.sh/typesafe/v1/systemone,
     model typesafe-ai/jev (adds one network hop versus the direct API)
  3. Nothing found, or the gateway returns 403 customer_verification_required
     -> MockDecisionClient. The mock is never silent about being a mock.
"""

from __future__ import annotations

import math
import os
import random
import threading
import time
from dataclasses import dataclass

try:
    import requests
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "The 'requests' package is required. Run: uv pip install requests"
    ) from exc

TYPESAFE_DIRECT_URL = "https://api.typesafe.ai/v1/systemone"
GATEWAY_URL = "https://ai-gateway.vercel.sh/typesafe/v1/systemone"
GATEWAY_BILLING_URL = (
    "https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%3Fmodal%3Dadd-credit-card"
)

# 429 is NOT retried inside a tick: retrying a rate limit only adds requests.
# It raises RateLimited and JevThrottle backs off across ticks instead.
RETRYABLE_STATUS = {529}
MAX_RETRIES = 2
BACKOFF_BASE_S = 0.35

# One shared lock for every Jev request in this process: never parallel calls.
_CALL_LOCK = threading.Lock()


class GatewayVerificationRequired(Exception):
    """Raised when the gateway responds 403 customer_verification_required."""


class DecisionClientError(Exception):
    pass


class RateLimited(DecisionClientError):
    """429, or any error whose text says the request rate is too high
    (the gateway's "access frequency is too high")."""


def _is_rate_limit(status: int, text: str) -> bool:
    t = (text or "").lower()
    return status == 429 or "frequency" in t or "rate limit" in t or "too many requests" in t


def _post_with_retry(url: str, headers: dict, body: dict, timeout: float) -> dict:
    deadline = time.monotonic() + timeout
    attempt = 0
    last_exc: Exception | None = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DecisionClientError(
                "block deadline exceeded before a request could be sent"
            )
        try:
            resp = requests.post(
                url, headers=headers, json=body, timeout=min(remaining, timeout)
            )
        except requests.RequestException as exc:
            last_exc = exc
            resp = None

        if resp is not None:
            if resp.status_code == 200:
                return resp.json()
            if _is_rate_limit(resp.status_code, resp.text):
                raise RateLimited(f"HTTP {resp.status_code}: {resp.text[:200]}")
            if resp.status_code == 403:
                try:
                    payload = resp.json()
                except ValueError:
                    payload = {}
                if (
                    payload.get("error", {}).get("type")
                    == "customer_verification_required"
                ):
                    raise GatewayVerificationRequired(
                        payload.get("error", {}).get(
                            "message", "customer verification required"
                        )
                    )
                raise DecisionClientError(f"HTTP 403: {resp.text[:300]}")
            if resp.status_code not in RETRYABLE_STATUS:
                raise DecisionClientError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        attempt += 1
        if attempt > MAX_RETRIES:
            if resp is not None:
                raise DecisionClientError(
                    f"gave up after {MAX_RETRIES} retries, last status {resp.status_code}"
                )
            raise DecisionClientError(
                f"gave up after {MAX_RETRIES} retries: {last_exc}"
            )

        backoff = BACKOFF_BASE_S * (2 ** (attempt - 1)) + random.uniform(0, 0.1)
        remaining = deadline - time.monotonic()
        if backoff >= remaining:
            raise DecisionClientError("block deadline exceeded during backoff")
        time.sleep(backoff)


@dataclass
class BaseDecisionClient:
    name: str
    model: str

    def ask(self, state: dict, questions: dict, timeout: float) -> tuple[dict, dict]:
        raise NotImplementedError


class TypeSafeDirectClient(BaseDecisionClient):
    def __init__(self, api_key: str, model: str = "jev-latest"):
        super().__init__(name="TypeSafe direct", model=model)
        self._api_key = api_key

    def ask(self, state: dict, questions: dict, timeout: float) -> tuple[dict, dict]:
        t0 = time.monotonic()
        body = {"state": state, "model": self.model, "questions": questions}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        with _CALL_LOCK:
            data = _post_with_retry(TYPESAFE_DIRECT_URL, headers, body, timeout)
        latency_ms = (time.monotonic() - t0) * 1000
        meta = {
            "route": self.name,
            "model": data.get("model", self.model),
            "latency_ms": round(latency_ms, 1),
            "usage": data.get("usage", {}),
        }
        return data["answers"], meta


class GatewayClient(BaseDecisionClient):
    def __init__(self, api_key: str, model: str = "typesafe-ai/jev"):
        super().__init__(name="Vercel AI Gateway", model=model)
        self._api_key = api_key

    def ask(self, state: dict, questions: dict, timeout: float) -> tuple[dict, dict]:
        t0 = time.monotonic()
        body = {"state": state, "model": self.model, "questions": questions}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        with _CALL_LOCK:
            data = _post_with_retry(GATEWAY_URL, headers, body, timeout)
        latency_ms = (time.monotonic() - t0) * 1000
        meta = {
            "route": self.name,
            "model": data.get("model", self.model),
            "latency_ms": round(latency_ms, 1),
            "usage": data.get("usage", {}),
        }
        return data["answers"], meta


class MockDecisionClient(BaseDecisionClient):
    """A plausible, persistent, clearly-labelled stand-in.

    Answers are derived from the real snapshot fields (not pure noise) so a
    demo run still looks internally consistent, and a slow-moving latent
    factor keeps regime/direction from flickering every tick. It is never
    presented as real: the model string always starts with 'mock-'.
    """

    def __init__(self, seed: int | None = None):
        super().__init__(name="MOCK", model="mock-jev-0.1")
        self._rng = random.Random(seed)
        self._regime_latent = self._rng.uniform(-1, 1)
        self._direction_latent = self._rng.uniform(-1, 1)

    def _drift(self, latent: float, pull: float = 0.04) -> float:
        latent += self._rng.uniform(-0.16, 0.16) - pull * latent
        return max(-1.0, min(1.0, latent))

    def ask(self, state: dict, questions: dict, timeout: float) -> tuple[dict, dict]:
        t0 = time.monotonic()
        time.sleep(self._rng.uniform(0.04, 0.15))  # a mock still "costs" some latency

        self._regime_latent = self._drift(self._regime_latent)
        self._direction_latent = self._drift(self._direction_latent)

        imbalance = state.get("imbalance", 0.0) or 0.0
        toxic = max(
            0.0, min(1.0, 0.5 + imbalance * 0.6 + self._rng.uniform(-0.15, 0.15))
        )
        liquidity_stressed = max(0.0, min(1.0, 0.3 + self._rng.uniform(-0.2, 0.3)))

        regime_probs = _softmax_from_latent(
            self._regime_latent, ["trending", "mean_reverting", "high_vol", "crisis"]
        )
        direction_probs = _softmax_from_latent(
            self._direction_latent, ["up", "down", "neutral"]
        )

        env_score, env_probs = _score_from_latent(
            0.5 - liquidity_stressed + self._rng.uniform(-0.3, 0.3), 4
        )
        inv_pressure = abs(state.get("inventory", 0.0) or 0.0)
        pressure_score, pressure_probs = _score_from_latent(
            min(1.0, inv_pressure * 400) - 0.5, 4
        )

        fill_ratio = state.get("fill_ratio")
        fill_ratio = 1.0 if fill_ratio is None else fill_ratio
        reject_count = state.get("reject_count") or 0
        latencies = state.get("last_10_latencies_ms") or []
        avg_latency = sum(latencies) / len(latencies) if latencies else 100.0
        slippage = state.get("last_10_slippage_bps") or []
        avg_slippage = (
            sum(abs(s) for s in slippage) / len(slippage) if slippage else 0.0
        )
        health_latent = (
            (fill_ratio - 0.5) * 1.5
            - reject_count * 0.3
            - max(0.0, (avg_latency - 300) / 500)
            - avg_slippage / 20
            + self._rng.uniform(-0.2, 0.2)
        )
        health_score, health_probs = _score_from_latent(
            max(-1.0, min(1.0, health_latent)), 4
        )

        answers = {
            "regime": _choice_answer(regime_probs),
            "direction": _choice_answer(direction_probs),
            "toxic_flow": {"type": "noul", "noul": round(toxic, 4)},
            "liquidity_stressed": {
                "type": "noul",
                "noul": round(liquidity_stressed, 4),
            },
            "quote_environment": _score_answer(
                env_score,
                env_probs,
                ["Do not quote", "Marginal", "Standard", "Excellent"],
            ),
            "inventory_pressure": _score_answer(
                pressure_score,
                pressure_probs,
                ["None", "Mild", "Skew hard", "Reduce now"],
            ),
            "execution_health": _score_answer(
                health_score,
                health_probs,
                ["Broken", "Degraded", "Normal", "Optimal"],
            ),
        }
        latency_ms = (time.monotonic() - t0) * 1000
        meta = {
            "route": self.name,
            "model": self.model,
            "latency_ms": round(latency_ms, 1),
            "usage": {},
        }
        return answers, meta


def _softmax_from_latent(latent: float, options: list[str]) -> dict:
    import math

    scores = {
        opt: math.exp(4.6 * latent * (1 if i == 0 else -0.5))
        for i, opt in enumerate(options)
    }
    total = sum(scores.values())
    return {opt: v / total for opt, v in scores.items()}


def _choice_confidence(probs: dict) -> float:
    n = len(probs)
    peak = max(probs.values())
    if n <= 1:
        return 1.0
    return max(0.0, min(1.0, (n * peak - 1) / (n - 1)))


def _choice_answer(probs: dict) -> dict:
    choice = max(probs, key=probs.get)
    return {
        "type": "choice",
        "choice": choice,
        "probabilities": {k: round(v, 4) for k, v in probs.items()},
        "confidence": round(_choice_confidence(probs), 4),
    }


def _score_from_latent(latent: float, n_levels: int) -> tuple[float, list[float]]:
    import math

    centre = max(0.0, min(n_levels - 1, (latent + 1) / 2 * (n_levels - 1)))
    weights = [math.exp(-((i - centre) ** 2) / 0.42) for i in range(n_levels)]
    total = sum(weights)
    probs = [w / total for w in weights]
    score = sum(i * p for i, p in enumerate(probs))
    return score, probs


def _score_answer(score: float, probs: list[float], levels: list[str]) -> dict:
    legend = {str(i): lvl for i, lvl in enumerate(levels)}
    prob_map = {str(i): round(p, 4) for i, p in enumerate(probs)}
    return {
        "type": "score",
        "score": round(score, 4),
        "legend": legend,
        "probabilities": prob_map,
        "confidence": round(
            _choice_confidence({str(i): p for i, p in enumerate(probs)}), 4
        ),
    }


class JevThrottle:
    """Decides when the loop may call Jev, and keeps the last good judgment.

    The fast loop runs every tick on price and risk. Jev is called only when
    JEV_MIN_INTERVAL_S has passed since the last call (default 4s), or when
    the state changed materially and JEV_MIN_GAP_S has passed (default 3s).
    A rate-limit error starts an exponential cooldown (5s doubling to 120s)
    during which the last judgment is reused. A judgment older than
    JEV_MAX_JUDGMENT_AGE_S is never reused. The Vercel AI Gateway allows
    roughly 20 to 30 requests a minute; a direct TypeSafe key allows more,
    so lower the intervals only with one.
    """

    def __init__(
        self,
        min_interval_s: float | None = None,
        min_gap_s: float | None = None,
        move_bps: float | None = None,
        max_age_s: float | None = None,
        backoff_base_s: float = 5.0,
        backoff_max_s: float = 120.0,
    ):
        env = os.environ.get
        self.min_interval_s = min_interval_s if min_interval_s is not None else float(env("JEV_MIN_INTERVAL_S") or 4.0)
        self.min_gap_s = min_gap_s if min_gap_s is not None else float(env("JEV_MIN_GAP_S") or 3.0)
        self.move_bps = move_bps if move_bps is not None else float(env("JEV_MATERIAL_MOVE_BPS") or 15.0)
        self.max_age_s = max_age_s if max_age_s is not None else float(env("JEV_MAX_JUDGMENT_AGE_S") or 60.0)
        self.backoff_base_s = backoff_base_s
        self.backoff_max_s = backoff_max_s
        self.answers: dict | None = None
        self.meta: dict | None = None
        self.answered_at = -math.inf
        self.last_call_at = -math.inf
        self.cooldown_until = -math.inf
        self.strikes = 0
        self._ref: dict | None = None

    def _material_change(self, snap: dict) -> str | None:
        ref = self._ref
        if ref is None:
            return "first judgment"
        mid, ref_mid = snap.get("mid") or 0.0, ref.get("mid") or 0.0
        if ref_mid and abs(mid - ref_mid) / ref_mid * 10_000 >= self.move_bps:
            return "price moved"
        if abs((snap.get("spread_bps") or 0.0) - (ref.get("spread_bps") or 0.0)) >= self.move_bps:
            return "spread moved"
        inv, ref_inv = snap.get("inventory") or 0.0, ref.get("inventory") or 0.0
        if (inv > 0) != (ref_inv > 0) or (inv < 0) != (ref_inv < 0):
            return "position changed"
        return None

    def due(self, snap: dict, now: float) -> str | None:
        """Why Jev should be called this tick, or None to reuse the last judgment."""
        if now < self.cooldown_until:
            return None
        since = now - self.last_call_at
        if since >= self.min_interval_s:
            return "interval"
        if since >= self.min_gap_s:
            return self._material_change(snap)
        return None

    def called(self, now: float) -> None:
        self.last_call_at = now

    def success(self, answers: dict, meta: dict, snap: dict, now: float) -> None:
        self.answers, self.meta, self.answered_at = answers, meta, now
        self._ref = {k: snap.get(k) for k in ("mid", "spread_bps", "inventory")}
        self.strikes = 0

    def rate_limited(self, now: float) -> float:
        """Start (or extend) the exponential cooldown. Returns the wait in seconds."""
        self.strikes += 1
        wait = min(self.backoff_max_s, self.backoff_base_s * 2 ** (self.strikes - 1))
        wait += random.uniform(0, 0.2 * wait)
        self.cooldown_until = now + wait
        return wait

    def last(self, now: float) -> tuple[dict, dict] | None:
        """The last judgment if it is young enough to reuse, else None."""
        if self.answers is None or now - self.answered_at > self.max_age_s:
            return None
        age = now - self.answered_at
        return self.answers, dict(self.meta or {}, reused=True, age_s=round(age, 1))


def resolve_decision_client(mock: bool = False) -> BaseDecisionClient:
    """Pick a client and print the one-line banner. Never crashes: falls all
    the way through to the mock if nothing else is usable."""
    if mock:
        print(
            "MOCK DECISION CLIENT (forced by --mock): answers are plausible, persistent, and clearly not real."
        )
        return MockDecisionClient()

    typesafe_key = os.environ.get("TYPESAFE_API_KEY")
    gateway_key = os.environ.get("AI_GATEWAY_API_KEY")

    if typesafe_key:
        print(
            f"decision client: TypeSafe direct, model pinned to jev-latest ({TYPESAFE_DIRECT_URL})"
        )
        return TypeSafeDirectClient(typesafe_key)

    if gateway_key:
        print(
            f"decision client: Vercel AI Gateway, model typesafe-ai/jev ({GATEWAY_URL}, adds one network hop)"
        )
        return GatewayClient(gateway_key)

    print(
        "MOCK DECISION CLIENT: no TYPESAFE_API_KEY or AI_GATEWAY_API_KEY found. "
        "Answers are plausible, persistent, and clearly not real."
    )
    return MockDecisionClient()
```

Write `~/.claude/skills/jev-loop/jevloop/battery.py`:

```python
"""The seven-question judgment battery.

One call, one latency, seven typed answers. Every question is atomic and
evaluated in isolation, and none of them ask Jev to weigh several factors
at once, and none of them ask Jev to trade or to calculate. That
composition happens in policy.py, in code, using the thresholds in
limits.py. The seven questions implement the three probabilistic rows in
the split (see split.py): fuzzy market conditions (regime, direction),
order quality (toxic_flow, liquidity_stressed), and execution health
(quote_environment, inventory_pressure, execution_health).

Question shape follows the verified TypeSafe / Vercel AI Gateway request
schema (see reference/systemone-request-shape.json):
  - noul needs only "instructions"
  - choice.criteria is a map of option -> description (or null)
  - score.criteria is an ARRAY of level descriptions, ordered low to high

Every question dict built here is checked against jevloop/split.py before
it is ever sent: if a question is off the allow-list, or its instructions
look like a request for arithmetic, the battery refuses to fire rather
than silently asking Jev to calculate something.
"""

from __future__ import annotations

from .split import assert_split_respected


def build_questions() -> dict:
    questions = {
        "regime": {
            "type": "choice",
            "instructions": "What market regime does this state describe?",
            "criteria": {
                "trending": None,
                "mean_reverting": None,
                "high_vol": None,
                "crisis": None,
            },
        },
        "direction": {
            "type": "choice",
            "instructions": "What is the price bias over the next 10 ticks?",
            "criteria": {"up": None, "down": None, "neutral": None},
        },
        "toxic_flow": {
            "type": "noul",
            "instructions": "Is the aggressive flow in this state likely informed rather than noise?",
        },
        "liquidity_stressed": {
            "type": "noul",
            "instructions": "Is the order book thinner than its recent norm?",
        },
        "quote_environment": {
            "type": "score",
            "instructions": "How favourable is this state for providing liquidity?",
            "criteria": ["Do not quote", "Marginal", "Standard", "Excellent"],
        },
        "inventory_pressure": {
            "type": "score",
            "instructions": "Given the current inventory, how urgent is it to cut the position?",
            "criteria": ["None", "Mild", "Skew hard", "Reduce now"],
        },
        "execution_health": {
            "type": "score",
            "instructions": (
                "Given recent fill ratio, reject count, slippage, and latency in this "
                "state, is execution quality optimal or degrading?"
            ),
            "criteria": ["Broken", "Degraded", "Normal", "Optimal"],
        },
    }
    assert_split_respected(questions)
    return questions


REQUIRED_ANSWER_KEYS = {
    "noul": {"type", "noul"},
    "choice": {"type", "choice", "probabilities", "confidence"},
    "score": {"type", "score", "legend", "probabilities", "confidence"},
}


def validate_answers(answers: dict) -> None:
    """Raise if the response is missing a question or a required field.
    Cheap insurance against a schema change on either the direct API or the
    gateway silently breaking policy.py's assumptions."""
    questions = build_questions()
    for key, q in questions.items():
        if key not in answers:
            raise ValueError(f"battery response missing answer for '{key}'")
        ans = answers[key]
        required = REQUIRED_ANSWER_KEYS[q["type"]]
        missing = required - set(ans.keys())
        if missing:
            raise ValueError(f"answer '{key}' missing fields {missing}")


def run_battery(client, state: dict, timeout: float) -> tuple[dict, dict]:
    """Fire the battery once. Returns (answers, meta) where meta carries the
    model name that answered and the round-trip latency in milliseconds."""
    questions = build_questions()
    answers, meta = client.ask(state=state, questions=questions, timeout=timeout)
    validate_answers(answers)
    return answers, meta
```

Write `~/.claude/skills/jev-loop/jevloop/policy.py`:

```python
"""compose_action(): the policy engine. Yours in code forever.

The seven thresholds this reads come from strategy.py, the file you edit
to change how the loop trades: see StrategyThresholds and the
apply_strategy() hook there. This function never calls Jev. It only reads
the seven answers Jev already gave this tick. When the model gets faster,
cheaper, or replaced, this file does not change.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .limits import Limits
from .strategy import THRESHOLDS, apply_strategy

KILL = "KILL"
PULL_QUOTES = "PULL_QUOTES"
WIDEN = "WIDEN"
QUOTE_BOTH_SIDES = "QUOTE_BOTH_SIDES"
QUOTE_WIDE = "QUOTE_WIDE"
STAND_DOWN = "STAND_DOWN"


@dataclass
class Action:
    kind: str
    reason: str
    skew: float = 0.0
    direction_leg: str | None = None  # "up" | "down" | None


def inventory_skew(pressure_score: float, max_score: float, inventory: float) -> float:
    """Signed skew in [-1, 1]. Negative skews toward selling (cutting a long),
    positive skews toward buying (cutting a short). Zero inventory -> no skew."""
    if inventory == 0:
        return 0.0
    magnitude = max(0.0, min(1.0, pressure_score / max_score))
    return -magnitude if inventory > 0 else magnitude


def compose_action(answers: dict, snapshot: dict, limits: Limits) -> Action:
    """Composes an action from THRESHOLDS in strategy.py, then hands it to
    strategy.apply_strategy() for one last look before it goes anywhere
    near an order. That hook can change the action or veto it; risk.py
    still runs after that and still has the final word."""
    action = _compose_from_thresholds(answers, snapshot, limits)
    return apply_strategy(action, answers, snapshot, limits)


def _compose_from_thresholds(answers: dict, snapshot: dict, limits: Limits) -> Action:
    if snapshot["drawdown_pct"] > limits.max_drawdown_pct:
        return Action(
            KILL, reason=f"drawdown {snapshot['drawdown_pct']:.2%} over limit"
        )

    toxic = answers["toxic_flow"]["noul"]
    if toxic > THRESHOLDS.toxic_flow_pull_threshold:
        return Action(PULL_QUOTES, reason=f"toxic flow {toxic:.2f}")

    liquidity_stressed = answers["liquidity_stressed"]["noul"]
    if liquidity_stressed > THRESHOLDS.liquidity_stressed_widen_threshold:
        return Action(WIDEN, reason=f"liquidity stressed {liquidity_stressed:.2f}")

    q = answers["quote_environment"]
    inv_p = answers["inventory_pressure"]

    if (
        q["score"] >= THRESHOLDS.quote_env_full_score
        and q["confidence"] > THRESHOLDS.quote_env_full_confidence
    ):
        skew = inventory_skew(
            inv_p["score"],
            THRESHOLDS.inventory_pressure_max_score,
            snapshot["inventory"],
        )
        action = Action(
            QUOTE_BOTH_SIDES,
            skew=skew,
            reason=f"env {q['score']:.2f} conf {q['confidence']:.2f}",
        )
    elif q["score"] >= THRESHOLDS.quote_env_wide_score:
        action = Action(QUOTE_WIDE, reason=f"env {q['score']:.2f}")
    else:
        action = Action(STAND_DOWN, reason=f"env {q['score']:.2f} below quoting floor")

    # Directional leg: bolted onto a quoting action so the demo shows fills
    # constantly, not just resting quotes. Never overrides a KILL/PULL/WIDEN.
    if action.kind in (QUOTE_BOTH_SIDES, QUOTE_WIDE):
        direction = answers["direction"]
        if (
            direction["choice"] != "neutral"
            and direction["confidence"] > THRESHOLDS.direction_confidence_threshold
        ):
            action.direction_leg = direction["choice"]

    return action


def fallback_action(snapshot: dict, limits: Limits) -> Action:
    """Deterministic, Jev-free policy used on the RULES_ONLY rung (Jev down
    or unavailable). Uses only spread and imbalance, nothing that needed a
    judgment call. This is what keeps the system honestly '24/7' rather than
    '24/7 until the model has a bad day'."""
    if snapshot["drawdown_pct"] > limits.max_drawdown_pct:
        return Action(KILL, reason="drawdown breach (rules-only)")
    if snapshot["spread_bps"] > 15.0:
        return Action(STAND_DOWN, reason="spread too wide for rules-only quoting")
    imbalance = snapshot.get("imbalance")
    if imbalance is not None and abs(imbalance) > 0.6:
        return Action(WIDEN, reason="book imbalance too high for rules-only quoting")
    return Action(QUOTE_WIDE, reason="rules-only: spread and imbalance both acceptable")
```

Write `~/.claude/skills/jev-loop/jevloop/strategy.py`:

```python
"""strategy.py -- the file you edit to change how this loop trades.

This is the harness the video talks about, not the edge. Everything it
shipped with is a generic strategy pulled out of thin air, wired in only
so the demo has something to trade. Real strategies are hard to build
properly; this file is where yours goes.

Two things live here:

1. `StrategyThresholds`, one number per action in `compose_action()`
   (policy.py): when to pull quotes, when to widen, when the quote
   environment is good enough to quote both sides or just quote wide, how
   much inventory pressure skews sizing, and how confident Jev has to be
   about direction before a directional leg is taken. Change a number,
   restart the loop, see different behaviour on the next tick.

2. `apply_strategy()`, a hook called once per tick with the action
   `compose_action()` already produced from the thresholds above. Return
   it unchanged (the default) and nothing changes from what shipped in
   the video. Return a different action to override it, or an action
   with `kind=STAND_DOWN` to veto the tick outright. This is the one
   function a real strategy plugs into.

Shipped default: every threshold below matches what the video ran, and
`apply_strategy()` is a no-op. Nothing changes for someone who never
opens this file.

The hard risk caps (max position, max daily loss, max drawdown, and so
on) do NOT live here: they live in `jevloop/limits.py`, checked in
`risk.py` before every order, and this file cannot raise them. A
strategy can make the loop more conservative than the risk engine
allows; it can never make it less conservative than the risk engine
allows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StrategyThresholds:
    """One threshold per action in compose_action(). These are exactly the
    numbers the video shipped with."""

    toxic_flow_pull_threshold: float = 0.6  # ans["toxic_flow"] > this -> PULL_QUOTES
    liquidity_stressed_widen_threshold: float = (
        0.7  # ans["liquidity_stressed"] > this -> WIDEN
    )
    quote_env_full_score: float = 2.0  # env >= this and confident -> quote both sides
    quote_env_full_confidence: float = 0.80
    quote_env_wide_score: float = 1.0  # env >= this (but below full) -> quote wide
    inventory_pressure_max_score: float = 3.0  # denominator for the skew calculation

    # the directional leg, bolted on so the demo shows fills, not just quotes
    direction_confidence_threshold: float = (
        0.55  # direction.confidence above this -> take the leg
    )


THRESHOLDS = StrategyThresholds()


def apply_strategy(action, answers: dict, snapshot: dict, limits) -> object:
    """The strategy hook. Called once per tick, after compose_action() has
    already turned Jev's answers into an action using THRESHOLDS above.

    Default: return the action unchanged. That is the whole strategy the
    video ran, a generic one, pulled out of thin air, applied only so the
    demo shows real fills.

    To plug in your own strategy, edit this function. You can:
      - inspect `answers` (the seven Jev judgments this tick) or
        `snapshot` (the deterministic state) and return a different
        Action than the one compose_action() chose
      - veto the tick outright by returning
        `Action(STAND_DOWN, reason="my strategy said no")`
      - leave `action` alone most of the time and only step in on
        specific conditions

    `risk.py` still runs after this and still has the final veto, so
    nothing returned here can bypass a hard limit in limits.py, only add
    more caution on top of it.
    """
    return action
```

Write `~/.claude/skills/jev-loop/jevloop/pricing.py`:

```python
"""Avellaneda-Stoikov reservation price and half spread, in basis points.

Fifty-year-old market-making maths. Stays in code. No model call, ever.
Jev never sees this file's output as a question. It only answers whether
the state is worth quoting into at all (policy.py). This file answers
where to quote.

Everything is worked out in basis points of mid, never in dollars, so the
same gamma and kappa give a sensible spread on an $85,000 coin and a $30
stock alike. (The first published version added the liquidity term in
dollars: about $1.29 each side, which is 0.3 bps on BTC and 860 bps on a
$30 stock.)

    q             = position value / max_position_usd   (-1 .. 1)
    reservation   = -q * gamma * sigma_bps^2 * T         (bps offset from mid)
    half spread   = gamma * sigma_bps^2 * T + (2 / gamma) * ln(1 + gamma / kappa)

sigma_bps is the per-minute realised volatility in bps, T the horizon in
minutes. The half spread is clamped to [min_half_bps, max_half_bps].
"""

from __future__ import annotations

import math


def reservation_offset_bps(
    inventory_frac: float, gamma: float, sigma_bps: float, horizon_min: float
) -> float:
    """Skew away from the side that grows inventory: long (q > 0) pulls the
    reservation price below mid so the quotes favour selling."""
    return -inventory_frac * gamma * (sigma_bps**2) * horizon_min


def half_spread_bps(
    gamma: float, sigma_bps: float, horizon_min: float, kappa: float
) -> float:
    """Half the total quoted spread around the reservation price, in bps."""
    inventory_term = gamma * (sigma_bps**2) * horizon_min
    liquidity_term = (2.0 / gamma) * math.log1p(gamma / kappa)
    return inventory_term + liquidity_term


def quote_prices(
    mid: float,
    inventory_frac: float,
    sigma: float,
    gamma: float,
    kappa: float,
    horizon_s: float,
    min_half_bps: float = 2.0,
    max_half_bps: float = 50.0,
) -> tuple[float, float]:
    """Returns (bid, ask). `sigma` is the per-minute realised volatility as
    a fraction (0.0005 = 5 bps), as state.py computes it."""
    sigma_bps = sigma * 10_000
    horizon_min = horizon_s / 60.0
    q = max(-1.0, min(1.0, inventory_frac))
    r = reservation_offset_bps(q, gamma, sigma_bps, horizon_min)
    h = half_spread_bps(gamma, sigma_bps, horizon_min, kappa)
    h = max(min_half_bps, min(max_half_bps, h))
    return mid * (1 + (r - h) / 10_000), mid * (1 + (r + h) / 10_000)
```

Write `~/.claude/skills/jev-loop/jevloop/risk.py`:

```python
"""The risk engine. Nine hard limits, checked before every single order.

Never delegates to Jev. Every limit here is checkable from something other
than the model's own claim: a number in the snapshot, a counter the loop
itself keeps. A KILL verdict means flatten and stop, not "ask the model
whether it's really that bad".
"""

from __future__ import annotations

from dataclasses import dataclass

from .limits import Limits


@dataclass
class RiskVerdict:
    ok: bool
    veto: str | None = None
    kill: bool = False


def check(
    snapshot: dict,
    order_notional_usd: float,
    limits: Limits,
    api_error_streak: int,
    decision_latency_ms: float | None,
    closing: bool = False,
) -> RiskVerdict:
    """`order_notional_usd` is the dollar value of the order about to be
    placed (qty * price), not a base-unit quantity: that is what makes
    every limit below mean the same thing whether the asset is a coin or
    a stock. Position value is derived from the snapshot's own inventory
    and mid, never trusted from anywhere else.

    `closing=True` is for an order that only reduces the position. The
    kill limits still apply; the order-size and inventory-age vetoes do
    not, because blocking the exit is what froze the loop with a stuck
    position in the first published version."""
    # 1. max drawdown
    if snapshot["drawdown_pct"] > limits.max_drawdown_pct:
        return RiskVerdict(False, "max_drawdown breached", kill=True)

    # 2. max position (in dollars)
    position_usd = abs(snapshot["inventory"]) * snapshot["mid"]
    if position_usd > limits.max_position_usd:
        return RiskVerdict(False, "max_position_usd breached", kill=True)

    # 3. max daily loss
    if snapshot["daily_loss_usd"] > limits.max_daily_loss_usd:
        return RiskVerdict(False, "max_daily_loss breached", kill=True)

    # 4. max order notional
    if not closing and order_notional_usd > limits.max_order_notional_usd:
        return RiskVerdict(False, "order exceeds max_order_notional_usd")

    # 5. max inventory age
    if (
        not closing
        and snapshot["inventory"] != 0
        and snapshot["position_age_s"] > limits.max_inventory_age_s
    ):
        return RiskVerdict(False, "inventory held past max_inventory_age_s")

    # 6. max stale-data age
    if snapshot["data_age_s"] > limits.max_stale_data_age_s:
        return RiskVerdict(False, "market data stale past max_stale_data_age_s")

    # 7. max API errors
    if api_error_streak > limits.max_api_errors:
        return RiskVerdict(False, "max_api_errors breached", kill=True)

    # 8. max decision latency
    if (
        decision_latency_ms is not None
        and decision_latency_ms > limits.max_decision_latency_ms
    ):
        return RiskVerdict(False, "decision latency over max_decision_latency_ms")

    # 9. max leverage (spot only; always 1.0, checked anyway so the limit is real)
    if snapshot.get("leverage", 1.0) > limits.max_leverage:
        return RiskVerdict(False, "max_leverage breached", kill=True)

    return RiskVerdict(True)
```

Write `~/.claude/skills/jev-loop/jevloop/ladder.py`:

```python
"""The five-rung fallback ladder.

This is what makes "24/7" true past 2am, when the wifi drops or Jev has a
bad night. The loop always lands on exactly one rung per tick, and the rung
(not the model) decides whether to trade, shrink, hold, or flatten.

    healthy + high confidence  -> RUN         (normal operation)
    healthy + low confidence   -> REDUCE      (smaller size)
    late past block deadline   -> HOLD_LATE   (no stale quotes, ever)
    Jev unavailable            -> RULES_ONLY  (deterministic fallback only)
    hard limit breached        -> KILL        (flatten, stop, alert)
"""

from __future__ import annotations

from enum import Enum


class Rung(str, Enum):
    RUN = "run"
    REDUCE = "reduce"
    HOLD_LATE = "hold_late"
    RULES_ONLY = "rules_only"
    KILL = "kill"


def select_rung(
    *,
    risk_kill: bool,
    decision_late: bool,
    jev_down: bool,
    decision_confidence: float | None,
    low_confidence_threshold: float,
    execution_health_score: float | None = None,
    execution_health_floor: float = 1.0,
) -> Rung:
    """decision_confidence is the confidence of whichever answer the policy
    engine actually used to decide (quote_environment.confidence in the
    common case). None when no decision was made at all (late or down).

    execution_health_score is Jev's own execution_health judgment for this
    tick (0 = Broken, 3 = Optimal). Below execution_health_floor, the ladder
    treats the tick the same way it treats low confidence: REDUCE, never
    RUN. This is the one place execution_health feeds back into behaviour,
    not just the log."""
    if risk_kill:
        return Rung.KILL
    if decision_late:
        return Rung.HOLD_LATE
    if jev_down:
        return Rung.RULES_ONLY
    if (
        decision_confidence is not None
        and decision_confidence < low_confidence_threshold
    ):
        return Rung.REDUCE
    if (
        execution_health_score is not None
        and execution_health_score < execution_health_floor
    ):
        return Rung.REDUCE
    return Rung.RUN
```

Write `~/.claude/skills/jev-loop/jevloop/execution/__init__.py`:

```python

```

Write `~/.claude/skills/jev-loop/jevloop/execution/alpaca.py`:

```python
"""Alpaca paper execution and market data, crypto or US equities. Paper
by default, on purpose.

Refuses to run against anything but the paper trading base URL, unless
ALL THREE live-trading gates are satisfied at once: see
resolve_trading_base_url() and LiveTradingRefused below. Paper is what
every default in this file, and every call site in the rest of the
skill, resolves to unless a caller explicitly asks for live and proves
it three separate ways. Refuses to place an equity order while the
market is closed, live or paper.
"""

from __future__ import annotations

import collections
import os
import time
import uuid

try:
    import requests
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "The 'requests' package is required. Run: uv pip install requests"
    ) from exc

from ..assets import AssetSpec, resolve_symbol

PAPER_TRADING_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_TRADING_BASE_URL = "https://api.alpaca.markets"

# All three of these are required, together, before a single live order
# can be placed. Any one missing refuses outright rather than quietly
# trading paper instead, so a half-finished attempt to go live is never
# mistaken for a successful paper run.
LIVE_ALLOW_ENV_VAR = "JEV_LOOP_ALLOW_LIVE"
LIVE_ALLOW_ENV_VALUE = "i-understand-the-risk"
LIVE_CONFIRMATION_PHRASE = "I understand this trades real money"


class AlpacaConfigError(Exception):
    pass


class AlpacaAPIError(Exception):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"HTTP {status_code}: {body[:300]}")
        self.status_code = status_code
        self.body = body


class MarketClosedError(Exception):
    """Raised when an order is attempted on a closed equity market. This
    class exists so the loop can tell "the venue said no" (AlpacaAPIError)
    apart from "we refused to even ask" (MarketClosedError)."""


class LiveTradingRefused(Exception):
    """Raised when live trading was requested but not all three required
    gates were satisfied: the --live flag, JEV_LOOP_ALLOW_LIVE set to
    exactly 'i-understand-the-risk' in the environment, and a typed
    confirmation matching LIVE_CONFIRMATION_PHRASE exactly. This is never
    raised for a plain paper run: paper needs none of these three."""


def assert_paper_url(base_url: str) -> None:
    """Hard guard for the ordinary, ungated construction path: this will
    not accept anything but the Alpaca paper trading endpoint. Live
    trading only ever reaches AlpacaPaperClient through client_from_env()
    after resolve_trading_base_url() has already checked all three gates;
    this function is not part of that path and still refuses the live URL
    on its own, by design."""
    if base_url.rstrip("/") != PAPER_TRADING_BASE_URL:
        raise AlpacaConfigError(
            f"refusing to run: trading base URL must be {PAPER_TRADING_BASE_URL}, got {base_url!r}. "
            "This skill only ever trades paper here."
        )


def resolve_trading_base_url(
    live: bool,
    allow_live_env: str | None,
    confirmation: str | None,
) -> str:
    """Paper unless all three gates are satisfied.

    live=False (the default everywhere): always returns the paper URL.
    The other two arguments are not even inspected, so a plain run is
    never affected by a stray environment variable.

    live=True: requires JEV_LOOP_ALLOW_LIVE=i-understand-the-risk in the
    environment AND a typed confirmation exactly matching
    LIVE_CONFIRMATION_PHRASE. Either one missing or wrong raises
    LiveTradingRefused; it never falls back to paper silently, because
    silently trading paper when the user explicitly asked for live and
    got a detail wrong is its own kind of dangerous surprise.
    """
    if not live:
        return PAPER_TRADING_BASE_URL

    if allow_live_env != LIVE_ALLOW_ENV_VALUE:
        raise LiveTradingRefused(
            f"refusing: --live was passed but {LIVE_ALLOW_ENV_VAR} is not set to "
            f"{LIVE_ALLOW_ENV_VALUE!r} in the environment. All three gates "
            "(--live, the environment variable, and a typed confirmation) are "
            "required together."
        )
    if confirmation != LIVE_CONFIRMATION_PHRASE:
        raise LiveTradingRefused(
            "refusing: the typed confirmation did not match "
            f"{LIVE_CONFIRMATION_PHRASE!r} exactly. All three gates (--live, "
            f"{LIVE_ALLOW_ENV_VAR}, and a typed confirmation) are required "
            "together."
        )
    return LIVE_TRADING_BASE_URL


class RateLimiter:
    """Simple token-bucket-by-timestamp limiter: keeps calls under N per
    rolling 60s window, sleeping just enough when the caller is about to
    exceed it."""

    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self._timestamps: collections.deque[float] = collections.deque()

    def wait(self) -> None:
        now = time.monotonic()
        while self._timestamps and now - self._timestamps[0] > 60.0:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.calls_per_minute:
            sleep_for = 60.0 - (now - self._timestamps[0]) + 0.01
            if sleep_for > 0:
                time.sleep(sleep_for)
        self._timestamps.append(time.monotonic())


class AlpacaPaperClient:
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        spec: AssetSpec,
        base_url: str = PAPER_TRADING_BASE_URL,
        calls_per_minute: int = 90,
        _live_gate_passed: bool = False,
    ):
        if base_url.rstrip("/") == LIVE_TRADING_BASE_URL:
            if not _live_gate_passed:
                # Direct construction against the live URL, bypassing
                # client_from_env() and its three gates, is refused
                # unconditionally. There is no way to reach the live venue
                # from this class except through resolve_trading_base_url().
                raise AlpacaConfigError(
                    "refusing to run: the live trading base URL was passed directly, "
                    "bypassing the three live-trading gates in client_from_env(). "
                    "This skill only trades live via --live, JEV_LOOP_ALLOW_LIVE, "
                    "and a typed confirmation, all three, together."
                )
        else:
            assert_paper_url(base_url)
        self.base_url = base_url
        self.is_live = base_url.rstrip("/") == LIVE_TRADING_BASE_URL
        self.spec = spec
        self.symbol = spec.symbol
        self._headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }
        self._limiter = RateLimiter(calls_per_minute)
        self._clock_cache: tuple[float, dict] | None = None
        self.order_prefix = f"jevloop-{uuid.uuid4().hex[:8]}-"
        self._order_seq = 0

    # -- low-level HTTP -----------------------------------------------
    def _request(self, method: str, url: str, **kwargs) -> dict:
        self._limiter.wait()
        try:
            resp = requests.request(
                method, url, headers=self._headers, timeout=10, **kwargs
            )
        except requests.RequestException as exc:
            # A timeout or dropped connection is an API error like any other:
            # the loop counts it toward max_api_errors and carries on, rather
            # than crashing and skipping the clean-up.
            raise AlpacaAPIError(0, f"network error: {exc}") from exc
        if resp.status_code == 401:
            raise AlpacaAPIError(
                401,
                "unauthorized. The key in your .env is either wrong or was copied from the LIVE "
                "dashboard instead of the PAPER dashboard. Generate a new key at "
                "https://app.alpaca.markets/paper/dashboard/overview (look for 'Generate New Keys' "
                "under Your API Keys) and update ALPACA_API_KEY / ALPACA_SECRET_KEY.",
            )
        if resp.status_code >= 400:
            raise AlpacaAPIError(resp.status_code, resp.text)
        if resp.text:
            return resp.json()
        return {}

    # -- account / orders -----------------------------------------------
    def get_account(self) -> dict:
        return self._request("GET", f"{self.base_url}/v2/account")

    def get_orders(self, status: str = "all", limit: int = 10) -> list:
        return self._request(
            "GET",
            f"{self.base_url}/v2/orders",
            params={"status": status, "limit": limit},
        )

    def get_clock(self, cache_s: float = 5.0) -> dict:
        """GET /v2/clock, cached briefly: this is checked every tick for an
        equity symbol and there is no reason to hit the API more than a
        few times a minute for a value that changes twice a day."""
        now = time.monotonic()
        if self._clock_cache and now - self._clock_cache[0] < cache_s:
            return self._clock_cache[1]
        data = self._request("GET", f"{self.base_url}/v2/clock")
        self._clock_cache = (now, data)
        return data

    def is_market_open(self) -> bool:
        if self.spec.is_24_7:
            return True
        return bool(self.get_clock().get("is_open"))

    def _qty_str(self, qty: float) -> str:
        return f"{qty:.{self.spec.qty_precision}f}"

    def new_client_order_id(self) -> str:
        """Every order this loop places carries a client_order_id starting
        with this run's prefix, so the loop can find, reconcile and cancel
        its own orders without touching anything else on the account."""
        self._order_seq += 1
        return f"{self.order_prefix}{self._order_seq}"

    def submit_limit_order(
        self, side: str, qty: float, limit_price: float, tif: str = "gtc"
    ) -> dict:
        if not self.spec.is_24_7 and not self.is_market_open():
            raise MarketClosedError(
                f"{self.symbol} market is closed, refusing to submit an order"
            )
        body = {
            "symbol": self.symbol,
            "qty": self._qty_str(qty),
            "side": side,
            "type": "limit",
            "time_in_force": tif,
            "limit_price": f"{limit_price:.2f}",
            "client_order_id": self.new_client_order_id(),
        }
        return self._request("POST", f"{self.base_url}/v2/orders", json=body)

    def submit_market_order(self, side: str, qty: float) -> dict:
        if not self.spec.is_24_7 and not self.is_market_open():
            raise MarketClosedError(
                f"{self.symbol} market is closed, refusing to submit an order"
            )
        body = {
            "symbol": self.symbol,
            "qty": self._qty_str(qty),
            "side": side,
            "type": "market",
            "time_in_force": "gtc" if self.spec.asset_class == "crypto" else "day",
            "client_order_id": self.new_client_order_id(),
        }
        return self._request("POST", f"{self.base_url}/v2/orders", json=body)

    def cancel_order(self, order_id: str) -> None:
        self._request("DELETE", f"{self.base_url}/v2/orders/{order_id}")

    def get_own_orders(self, after_iso: str) -> list:
        """This run's orders only (matched on the client_order_id prefix),
        any status, newest first. One call covers every order the loop has
        placed, so fills are read from the broker rather than assumed."""
        orders = self._request(
            "GET",
            f"{self.base_url}/v2/orders",
            params={
                "status": "all",
                "after": after_iso,
                "limit": 500,
                "direction": "desc",
            },
        )
        return [
            o
            for o in (orders or [])
            if str(o.get("client_order_id", "")).startswith(self.order_prefix)
        ]

    def cancel_own_orders(self) -> int:
        """Cancel only the open orders this run placed. Never calls
        DELETE /v2/orders (which would cancel every order on the account,
        including ones from anything else you run there)."""
        open_orders = self._request(
            "GET",
            f"{self.base_url}/v2/orders",
            params={"status": "open", "limit": 500},
        )
        n = 0
        for o in open_orders or []:
            if str(o.get("client_order_id", "")).startswith(self.order_prefix):
                try:
                    self.cancel_order(o["id"])
                    n += 1
                except AlpacaAPIError as exc:
                    if exc.status_code != 422:  # 422 = already filled/cancelled
                        raise
        return n

    def get_position_qty(self) -> float:
        """Signed quantity Alpaca actually holds for this symbol (0 if none)."""
        sym = self.symbol.replace("/", "")
        try:
            pos = self._request("GET", f"{self.base_url}/v2/positions/{sym}")
        except AlpacaAPIError as exc:
            if exc.status_code == 404:
                return 0.0
            raise
        return float(pos.get("qty", 0.0))

    # -- market data -----------------------------------------------
    def get_orderbook(self) -> dict:
        """Real L2 depth on crypto. Returns {} on equities (has_depth is
        False there) rather than pretending a book exists."""
        if not self.spec.has_depth or self.spec.orderbook_url is None:
            return {}
        data = self._request(
            "GET", self.spec.orderbook_url, params={"symbols": self.symbol}
        )
        return data.get("orderbooks", {}).get(self.symbol, {})

    def get_latest_quote(self) -> dict:
        """Best bid/ask. The only depth source at all on equities."""
        data = self._request(
            "GET", self.spec.latest_quote_url, params={"symbols": self.symbol}
        )
        return data.get("quotes", {}).get(self.symbol, {})

    def get_latest_trade(self) -> dict:
        data = self._request(
            "GET", self.spec.latest_trade_url, params={"symbols": self.symbol}
        )
        return data.get("trades", {}).get(self.symbol, {})

    def _data_params(self, **extra) -> dict:
        params = {"symbols": self.symbol, **extra}
        if self.spec.asset_class != "crypto":
            params["feed"] = "iex"  # the free equities feed; SIP needs a paid plan
        return params

    def get_recent_trades(self, start_iso: str, limit: int = 1000) -> list:
        """Trades stamped at or after `start_iso`, oldest first, each with
        its real venue timestamp ("t"), price, size, taker side and id.
        Without `start` this endpoint returns the first trades of the UTC
        day, not the recent ones, so `start` is required."""
        data = self._request(
            "GET",
            self.spec.recent_trades_url,
            params=self._data_params(start=start_iso, limit=limit, sort="asc"),
        )
        return (data.get("trades") or {}).get(self.symbol, []) or []

    def get_minute_bars(self, start_iso: str, limit: int = 1000) -> list:
        """One-minute bars since `start_iso`. Used once at startup so the
        1m/5m/30m returns and volatility have real history from tick one."""
        url = self.spec.recent_trades_url.rsplit("/trades", 1)[0] + "/bars"
        data = self._request(
            "GET",
            url,
            params=self._data_params(start=start_iso, timeframe="1Min", limit=limit),
        )
        return (data.get("bars") or {}).get(self.symbol, []) or []


def client_from_env(
    symbol: str = "BTC/USD",
    live: bool = False,
    confirmation: str | None = None,
) -> AlpacaPaperClient:
    """Builds the execution client. Paper unless `live=True` AND
    JEV_LOOP_ALLOW_LIVE=i-understand-the-risk is set AND `confirmation`
    matches LIVE_CONFIRMATION_PHRASE exactly -- see
    resolve_trading_base_url(). `live` defaults to False everywhere it is
    called in this skill, so paper is always the default unless a caller
    goes out of its way to ask for live."""
    api_key = os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise AlpacaConfigError("ALPACA_API_KEY / ALPACA_SECRET_KEY not set")

    allow_live_env = os.environ.get(LIVE_ALLOW_ENV_VAR)
    base_url = resolve_trading_base_url(live, allow_live_env, confirmation)
    spec = resolve_symbol(symbol)

    if base_url == LIVE_TRADING_BASE_URL:
        print("\n" + "!" * 70)
        print("! LIVE TRADING ENABLED.")
        print("! Every order from here on spends real money in your real Alpaca")
        print("! account. There is no paper safety net under this run.")
        print("!" * 70 + "\n")
        return AlpacaPaperClient(
            api_key, secret_key, spec=spec, base_url=base_url, _live_gate_passed=True
        )

    # Paper path: still allow ALPACA_BASE_URL to point at a stand-in
    # server for testing, exactly as before live trading existed at all.
    override_url = os.environ.get("ALPACA_BASE_URL", base_url)
    return AlpacaPaperClient(api_key, secret_key, spec=spec, base_url=override_url)
```

Write `~/.claude/skills/jev-loop/jevloop/loop.py`:

```python
"""The nine-stage block loop.

    1. block event            (tick clock, "block" = one tick, default 2s)
    2. read the book          (Alpaca paper market data: L2 depth on crypto,
                               best bid/ask on equities, and recent trades)
    3. state snapshot         (deterministic, state.py)
    4. battery                (seven Jev judgments, one call, battery.py)
    5. policy engine          (compose_action, policy.py: code, not Jev)
    6. pricing                (Avellaneda-Stoikov, pricing.py: code)
    7. risk veto              (hard limits, risk.py: code, absolute veto)
    8. execute                (cancel-replace post-only quotes plus directional leg)
    9. log, fills, inventory  (JSONL and latest.json for the dashboard)

Paper by default. `--mock` forces the mock decision client even if a real
key is present, useful for a clean demo run that can never fail on network
or billing grounds. A mock answers with random numbers, so any mock run
(forced, or fallen back to mid-run) is also a dry run: no orders at all. `--dry-execution` reads real market data and fires a
real Jev battery but never submits an order to Alpaca; every fill line
reads "dry" instead. Useful for testing the full pipeline without touching
the paper account. `--ticks 0` or `--forever` runs continuously until
stopped (Ctrl+C, or a SIGTERM if it is running in the background), and
cancels the resting orders it placed (only those, matched on this run's
client_order_id prefix) before it exits rather than leaving them behind. `--live` is a separate, deliberately awkward opt-in documented in
execution/alpaca.py and SKILL.md; paper is what every default here
resolves to unless a caller goes out of its way to ask for live.

Any asset `jevloop/assets.py` resolves: a crypto pair runs 24/7; a US
equity ticker only trades while the market is open, and the loop holds
(never orders) while it is closed, per `execution/alpaca.py`'s market-hours
guard.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import sys
import time
from pathlib import Path

from . import control
from .assets import AssetSpec, UnknownSymbolError, resolve_symbol, size_order
from .battery import run_battery
from .client import (
    DecisionClientError,
    GatewayVerificationRequired,
    JevThrottle,
    RateLimited,
    resolve_decision_client,
)
from .execution.alpaca import (
    LIVE_CONFIRMATION_PHRASE,
    AlpacaAPIError,
    AlpacaConfigError,
    LiveTradingRefused,
    MarketClosedError,
    client_from_env,
)
from .ladder import Rung, select_rung
from .limits import Limits
from .policy import (
    KILL,
    PULL_QUOTES,
    QUOTE_BOTH_SIDES,
    QUOTE_WIDE,
    STAND_DOWN,
    WIDEN,
    compose_action,
    fallback_action,
)
from .pricing import quote_prices
from .state import (
    InventoryState,
    apply_fill,
    build_snapshot,
    record_fill_slippage,
    update_vwap,
)

LOG_DIR = Path(os.environ.get("JEV_LOOP_HOME", str(Path.home() / ".jev-loop")))
LOG_FILE = LOG_DIR / "log.jsonl"
LATEST_FILE = LOG_DIR / "latest.json"
LATEST_WINDOW = 120
HISTORY_S = 2400.0  # keep 40 minutes of real price history (return_30m needs 30; venues skip quiet minutes)
TRADE_TAPE_S = 60.0  # real trades kept for the flow fields (30s window + slack)
# --bar: decide once per bar close instead of every 2 s block.
BAR_CHOICES = {"1m": 60.0, "5m": 300.0, "15m": 900.0, "30m": 1800.0, "1h": 3600.0}
BAR_SETTLE_S = 2.0  # wait this long past the close so the venue has stamped the bar
BAR_DECISION_DEADLINE_S = 5.0  # Jev's answer still has to come back fast in bar mode
TERMINAL_ORDER_STATES = {"filled", "canceled", "expired", "rejected", "done_for_day"}


def _parse_ts(raw: str) -> float:
    """RFC 3339 venue timestamp (Alpaca sends nanoseconds) -> epoch seconds."""
    from datetime import datetime

    raw = raw.replace("Z", "+00:00")
    if "." in raw:
        head, rest = raw.split(".", 1)
        frac, tz = rest[:9], ""
        for sep in ("+", "-"):
            if sep in rest:
                frac, tz = rest.split(sep, 1)
                tz = sep + tz
                break
        raw = f"{head}.{frac[:6]}{tz}"
    return datetime.fromisoformat(raw).timestamp()


def _iso(ts: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def reconcile_fills(alpaca, inv: InventoryState, seen: dict, expected_px: dict, after_iso: str, now: float, open_buys: dict | None = None):
    """Read this run's orders back from Alpaca and fold in only the fill
    quantity that is new since the last check, at the broker's own average
    fill price. Returns (list of (side, qty, price) new fills, pending?)
    where pending means at least one of our orders is still working. If
    `open_buys` is given, open_buys["usd"] is set to the dollar value of
    this run's buy orders still working, so the position cap can count
    them before they fill."""
    new_fills = []
    pending = False
    working_buy_usd = 0.0
    for o in alpaca.get_own_orders(after_iso):
        oid = o.get("id")
        fq = float(o.get("filled_qty") or 0.0)
        avg = float(o.get("filled_avg_price") or 0.0)
        pq, pavg = seen.get(oid, (0.0, 0.0))
        if fq > pq + 1e-12 and avg > 0:
            dq = fq - pq
            px = (fq * avg - pq * pavg) / dq
            apply_fill(inv, o["side"], dq, px, now)
            exp = expected_px.get(o.get("client_order_id"))
            if exp:
                record_fill_slippage(inv, expected_price=exp, fill_price=px, side=o["side"])
            new_fills.append((o["side"], dq, px))
            seen[oid] = (fq, avg)
        if o.get("status") not in TERMINAL_ORDER_STATES:
            pending = True
            if o.get("side") == "buy":
                left = max(float(o.get("qty") or 0.0) - fq, 0.0)
                px_ = float(o.get("limit_price") or 0.0) or expected_px.get(o.get("client_order_id")) or avg
                working_buy_usd += left * (px_ or 0.0)
    if open_buys is not None:
        open_buys["usd"] = working_buy_usd
    return new_fills, pending


def sync_fees(inv: InventoryState, run_held: float, price: float) -> float:
    """Alpaca takes the fee on a crypto buy in the coin itself, so the
    account ends up holding a little less than the fills add up to. Left
    alone, the bot thinks it owns coin it doesn't, and its closing sells
    get rejected. `run_held` is what Alpaca says this run holds (account
    position minus whatever was there before the run started). When that
    is below the bot's own count on a long, the gap is the fee: shrink
    inventory to match and book the fee as a realised cost. Returns the
    fee in dollars (0.0 when nothing was taken)."""
    if inv.inventory <= 0 or run_held < 0 or run_held >= inv.inventory - 1e-12:
        return 0.0
    fee_qty = inv.inventory - run_held
    fee_usd = fee_qty * price
    inv.inventory = run_held
    if run_held <= 1e-12:
        inv.inventory = 0.0
        inv.entry_price = 0.0
        inv.position_opened_at = None
    inv.fees_usd += fee_usd
    inv.realised_pnl_usd -= fee_usd
    return fee_usd


def _floor_qty(qty: float, spec: AssetSpec) -> float:
    """Round a closing quantity DOWN to the asset's precision. Rounding up
    asks to sell more than is held, and Alpaca rejects it."""
    step = 10 ** spec.qty_precision
    return math.floor(round(qty * step, 6)) / step


def _flatten(alpaca, spec: AssetSpec, inv: InventoryState, dry: bool, seen: dict, expected_px: dict, after_iso: str, now: float) -> str:
    """KILL means flatten for real: cancel this run's own resting orders,
    then send a market order that closes the position this run built. It
    never sells more than Alpaca says is actually held, so it cannot open a
    short or close a position something else opened."""
    if dry:
        return f"dry: would cancel own orders and flatten {inv.inventory}"
    msgs = []
    try:
        n = alpaca.cancel_own_orders()
        msgs.append(f"cancelled {n} own order(s)")
        reconcile_fills(alpaca, inv, seen, expected_px, after_iso, now)
        held = alpaca.get_position_qty()
        bot = inv.inventory
        qty = min(abs(bot), abs(held)) if bot * held > 0 else 0.0
        qty = _floor_qty(qty, spec)
        if qty > 0:
            side = "sell" if bot > 0 else "buy"
            alpaca.submit_market_order(side, qty)
            for _ in range(5):
                time.sleep(0.5)
                fills, pending = reconcile_fills(alpaca, inv, seen, expected_px, after_iso, now)
                if not pending:
                    break
            msgs.append(f"market {side} {qty} sent, inventory now {inv.inventory}")
        else:
            msgs.append("nothing held to flatten")
    except (AlpacaAPIError, MarketClosedError) as exc:
        msgs.append(f"FLATTEN FAILED, close the position by hand in Alpaca: {exc}")
    return "; ".join(msgs)


def _close_position(alpaca, spec: AssetSpec, inv: InventoryState, mid: float, expected_px: dict | None) -> str:
    """Market order that closes the position this run built, never more
    than Alpaca says is held, rounded down so it is never rejected."""
    bot = inv.inventory
    held = alpaca.get_position_qty()
    qty = _floor_qty(min(abs(bot), abs(held)), spec) if bot * held > 0 else 0.0
    if qty <= 0:
        return "no position to close"
    side = "sell" if bot > 0 else "buy"
    inv.orders_submitted += 1
    o = alpaca.submit_market_order(side, qty)
    if expected_px is not None and o.get("client_order_id"):
        expected_px[o["client_order_id"]] = mid
    return f"sent market {side} {qty} (closing position)"


def _fmt_money(x: float) -> str:
    return f"{x:,.1f}"


class _StopRequested(Exception):
    """Raised by the SIGTERM handler so a run stopped from the background
    (`kill <pid>`) shuts down exactly as cleanly as a foreground Ctrl+C
    (KeyboardInterrupt) does: cancel resting orders, then exit."""


def _handle_sigterm(signum, frame) -> None:
    raise _StopRequested()


def run(
    symbol: str,
    ticks: int | None,
    mock: bool,
    limits: Limits,
    dry_execution: bool = False,
    live: bool = False,
    confirmation: str | None = None,
    bar_seconds: float | None = None,
) -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    try:
        spec = resolve_symbol(symbol)
    except UnknownSymbolError as exc:
        print(f"cannot start: {exc}")
        return 1

    try:
        alpaca = client_from_env(
            symbol=spec.symbol, live=live, confirmation=confirmation
        )
    except AlpacaConfigError as exc:
        print(f"cannot start: {exc}")
        return 1
    except LiveTradingRefused as exc:
        print(f"cannot start: {exc}")
        return 1

    # One shared client for the whole run, and one throttle in front of it.
    client = resolve_decision_client(mock=mock)
    throttle = JevThrottle()
    print(
        f"jev calls: at most one every {throttle.min_interval_s:g}s (sooner on a material "
        f"change, never under {throttle.min_gap_s:g}s), last judgment reused in between"
    )
    if client.name == "MOCK" and not dry_execution:
        # A mock answers with random numbers. Random numbers never place
        # orders, not even on paper: the mock is for exercising the pipeline.
        dry_execution = True
        print("mock decision client: forcing dry execution, no orders will be sent.")
    session_txt = "24/7" if spec.is_24_7 else "market hours only"
    print(
        f"asset: {spec.symbol} ({spec.asset_class}, {session_txt}, "
        f"min order ${spec.min_notional_usd:.2f}, depth: {'yes' if spec.has_depth else 'best bid/ask only'})"
    )
    # Bar mode: sleep to each bar close, then run one block. Otherwise one
    # block every limits.tick_seconds. Jev's deadline stays short either way.
    cadence_s = 0.0 if bar_seconds else limits.tick_seconds
    deadline_s = min(bar_seconds, BAR_DECISION_DEADLINE_S) if bar_seconds else limits.tick_seconds
    if bar_seconds:
        print(
            f"tick cadence: one decision at each {bar_seconds / 60:g}-minute bar close "
            f"(UTC-aligned), Jev deadline {deadline_s:.0f}s"
        )
    else:
        print(
            f"tick cadence: one block every {limits.tick_seconds:.1f}s "
            f"(Alpaca calls capped at {limits.max_alpaca_calls_per_minute}/min)"
        )
    print(
        "your strategy lives in strategy.py (edit thresholds, or the apply_strategy hook)"
    )
    if ticks is None:
        print(
            "running continuously until stopped (Ctrl+C, or `kill <pid>` if this is "
            "in the background). Resting orders are cancelled on shutdown."
        )
    if dry_execution:
        print(
            "dry execution: real market data and a real Jev battery, no orders sent to Alpaca."
        )
    if control.is_paused(LOG_DIR):
        print(
            "control: PAUSED from the dashboard, no new orders until you press Start "
            "(or run: uv run python -m jevloop resume)."
        )

    # Seed equity from the real account so drawdown is measured against real
    # money. If the account cannot be read (dry run without a working key),
    # fall back to the position cap, the most this loop can ever put at risk.
    try:
        start_equity = float(alpaca.get_account().get("equity") or 0.0)
    except AlpacaAPIError as exc:
        start_equity = 0.0
        print(f"could not read account equity ({exc.status_code}); ", end="")
    if start_equity <= 0:
        start_equity = limits.max_position_usd
        print(f"drawdown measured against the ${start_equity:.2f} position cap")
    else:
        print(f"account equity at start: ${start_equity:,.2f}")
    inv = InventoryState(equity_usd=start_equity, high_water_mark_usd=start_equity)
    # Whatever the account already held in this symbol before the run is
    # not the loop's: fees are measured against it, and it is never sold.
    start_held = 0.0
    if not dry_execution:
        try:
            start_held = alpaca.get_position_qty()
        except AlpacaAPIError:
            pass
    open_buys = {"usd": 0.0}
    session_start = time.time()
    session_start_iso = _iso(session_start - 5)
    fills_seen: dict = {}
    expected_px: dict = {}
    reconcile_needed = False

    # Real price history. Backfill 31 minutes of one-minute bars (stamped at
    # each bar's close) so returns and volatility are real from the first
    # tick, then add one real mid sample per tick with the time it was read.
    price_hist: list[tuple[float, float]] = []
    try:
        price_hist = _minute_bar_history(alpaca, session_start)
        print(f"price history: {len(price_hist)} one-minute bars backfilled")
    except (AlpacaAPIError, KeyError, ValueError) as exc:
        print(f"price history: no backfill ({exc}); returns fill in as ticks arrive")
    trade_tape: list[tuple[float, float, float, str]] = []  # (ts, price, size, side)
    seen_trade_ids: set = set()
    trades_since_iso = _iso(session_start - TRADE_TAPE_S)
    api_error_streak = 0
    jev_down = False
    rest_counter = 0
    resting_quotes: dict | None = None
    recent_ticks: list[dict] = []
    block = 0
    started_at = time.time()

    n = 0
    previous_sigterm_handler = None
    try:
        previous_sigterm_handler = signal.signal(signal.SIGTERM, _handle_sigterm)
    except (ValueError, AttributeError, OSError):
        pass  # not the main thread, or a platform without SIGTERM

    try:
        while ticks is None or n < ticks:
            if bar_seconds:
                time.sleep(_seconds_to_bar_close(time.time(), bar_seconds))
            tick_start = time.monotonic()
            block += 1
            now = time.time()

            # Market-hours guard for equities: never even ask Jev about a
            # frozen market, and never place an order while it is closed.
            if not spec.is_24_7:
                try:
                    market_open = alpaca.is_market_open()
                except AlpacaAPIError as exc:
                    api_error_streak += 1
                    print(f"tick {block} | alpaca error checking market hours: {exc}")
                    _sleep_remaining(tick_start, cadence_s)
                    n += 1
                    continue
                if not market_open:
                    record = _closed_market_record(block, now, spec.symbol)
                    _append_log(record)
                    recent_ticks.append(record)
                    if len(recent_ticks) > LATEST_WINDOW:
                        recent_ticks = recent_ticks[-LATEST_WINDOW:]
                    _write_latest(
                        spec.symbol,
                        block,
                        recent_ticks,
                        {"route": None, "model": None},
                        started_at,
                        api_error_streak,
                    )
                    print(
                        f"tick {block} | {spec.symbol} market is closed, prices are stale | HOLD"
                    )
                    n += 1
                    _sleep_remaining(tick_start, cadence_s)
                    continue

            # 2. read the book
            try:
                bids, asks = _read_top_of_book(alpaca, spec)
                if bar_seconds:
                    # Only the flow around this close; the gap since the last
                    # bar can hold more trades than one fetch returns.
                    trades_since_iso = _iso(now - TRADE_TAPE_S)
                recent = alpaca.get_recent_trades(start_iso=trades_since_iso)
                api_error_streak = 0
            except AlpacaAPIError as exc:
                api_error_streak += 1
                print(f"tick {block} | alpaca error: {exc}")
                _sleep_remaining(tick_start, cadence_s)
                n += 1
                continue

            # Real trades only, each with the venue's own timestamp, each
            # counted once (deduplicated on the trade id).
            new_trades = []
            for t in recent:
                tid = t.get("i")
                if tid in seen_trade_ids:
                    continue
                seen_trade_ids.add(tid)
                ts = _parse_ts(t["t"])
                if ts > now:
                    continue  # never let a trade stamped after as_of in
                side = "buy" if t.get("tks") == "B" else "sell"
                new_trades.append((ts, float(t["p"]), float(t["s"]), side))
            if new_trades:
                trades_since_iso = _iso(max(ts for ts, *_ in new_trades))
            trade_tape.extend(new_trades)
            trade_tape = [x for x in trade_tape if x[0] >= now - TRADE_TAPE_S]
            if len(seen_trade_ids) > 5000:
                seen_trade_ids = {t.get("i") for t in recent}
            update_vwap(inv, [(ts, p, sz) for ts, p, sz, _ in new_trades])

            last_trade_px = trade_tape[-1][1] if trade_tape else (price_hist[-1][1] if price_hist else 0.0)
            mid = (
                (bids[0][0] + asks[0][0]) / 2
                if bids and asks and bids[0][0] and asks[0][0]
                else last_trade_px
            )
            microprice = mid  # depth-weighted microprice; mid is a fair stand-in when depth is thin
            spread_bps = (
                (asks[0][0] - bids[0][0]) / mid * 10_000
                if (mid and bids and asks)
                else 0.0
            )

            data_ts = now
            if bar_seconds:
                try:
                    price_hist = _minute_bar_history(alpaca, now)
                except (AlpacaAPIError, KeyError, ValueError) as exc:
                    print(f"tick {block} | minute bars unavailable ({exc}), using the last history")
            if mid > 0:
                price_hist.append((now, mid))
            price_hist = [x for x in price_hist if x[0] >= now - HISTORY_S]
            trade_prices = price_hist
            trade_sides = [(ts, side) for ts, _, _, side in trade_tape]

            # Fills come from Alpaca, not from assumptions: read this run's
            # orders back and fold in only what actually filled, at the price
            # it actually filled at.
            recon_txt = None
            fill_qty = None
            fill_price = None
            if reconcile_needed and not dry_execution:
                try:
                    new_fills, reconcile_needed = reconcile_fills(
                        alpaca, inv, fills_seen, expected_px, session_start_iso, now,
                        open_buys=open_buys,
                    )
                    if not reconcile_needed:
                        open_buys["usd"] = 0.0
                    if new_fills:
                        fill_qty = sum(q for _, q, _ in new_fills)
                        fill_price = sum(q * px for _, q, px in new_fills) / fill_qty
                        recon_txt = ", ".join(
                            f"filled {sd} {q:.8g} @ {px:,.2f}" for sd, q, px in new_fills
                        )
                        fee = sync_fees(inv, alpaca.get_position_qty() - start_held, fill_price)
                        if fee:
                            recon_txt += f", fee ${fee:.4f}"
                except AlpacaAPIError as exc:
                    api_error_streak += 1
                    print(f"tick {block} | could not read fills back: {exc}")

            # 3. state snapshot
            snapshot = build_snapshot(
                as_of=now,
                mid=mid,
                microprice=microprice,
                spread_bps=spread_bps,
                bid_depth=bids,
                ask_depth=asks,
                trade_prices=trade_prices,
                trade_sides=trade_sides,
                inv=inv,
                data_timestamp=data_ts,
                has_depth=spec.has_depth,
            )
            equity_now = inv.equity_usd + inv.realised_pnl_usd + snapshot["unrealised_pnl_usd"]
            inv.high_water_mark_usd = max(inv.high_water_mark_usd, equity_now)

            # 4. battery, throttled. The fast loop never waits on Jev: Jev is
            # called only when the throttle says so, and every other tick
            # reuses the last judgment (see "Jev call rate" in README.md).
            elapsed = time.monotonic() - tick_start
            budget = max(0.05, deadline_s - elapsed - 0.15)
            decision_late = False
            answers = None
            meta = {"model": None, "latency_ms": None, "route": None}
            clock = time.monotonic()
            call_reason = throttle.due(snapshot, clock)
            jev_down = False
            if call_reason is not None:
                throttle.called(clock)
                try:
                    answers, meta = run_battery(client, snapshot, timeout=budget)
                    throttle.success(answers, meta, snapshot, clock)
                except RateLimited as exc:
                    wait = throttle.rate_limited(clock)
                    print(
                        f"tick {block} | Jev rate limit ({exc}), backing off {wait:.0f}s, "
                        f"reusing the last judgment meanwhile"
                    )
                except GatewayVerificationRequired as exc:
                    print(
                        f"tick {block} | gateway needs a card on file: {exc}\n"
                        f"           add one at https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%3Fmodal%3Dadd-credit-card, "
                        f"falling back to the mock decision client for the rest of this run."
                    )
                    client = resolve_decision_client(mock=True)
                    jev_down = True
                    if not dry_execution:
                        dry_execution = True
                        print(f"tick {block} | mock decisions: dry execution from here, no more orders.")
                except DecisionClientError as exc:
                    msg = str(exc)
                    if "deadline" in msg:
                        decision_late = True
                    else:
                        jev_down = True
                        print(f"tick {block} | decision client error: {exc}")
            if answers is None and not jev_down:
                cached = throttle.last(clock)
                if cached is not None:
                    answers, meta = cached
                    decision_late = False
                elif not decision_late:
                    jev_down = True  # no judgment young enough to reuse: RULES_ONLY

            # 5. policy engine (code) + 6. pricing (code)
            if decision_late:
                action = None
            elif jev_down or answers is None:
                action = fallback_action(snapshot, limits)
            else:
                action = compose_action(answers, snapshot, limits)

            sigma = snapshot["realised_vol_short"] or 0.0005
            bid_px, ask_px = quote_prices(
                mid=mid,
                inventory_frac=snapshot["inventory"] * mid / limits.max_position_usd,
                sigma=sigma,
                gamma=limits.as_gamma,
                kappa=limits.as_kappa,
                horizon_s=limits.as_horizon_s,
                min_half_bps=limits.min_half_spread_bps,
                max_half_bps=limits.max_half_spread_bps,
            )

            # ladder
            decision_conf = None
            if action is not None and answers is not None:
                decision_conf = answers.get("quote_environment", {}).get("confidence")
            execution_health_score = (
                answers["execution_health"]["score"] if answers else None
            )
            risk_kill_pre = snapshot["drawdown_pct"] > limits.max_drawdown_pct
            rung = select_rung(
                risk_kill=risk_kill_pre,
                decision_late=decision_late,
                jev_down=jev_down and not decision_late,
                decision_confidence=decision_conf,
                low_confidence_threshold=limits.low_confidence_threshold,
                execution_health_score=execution_health_score,
            )

            size_factor = limits.reduce_size_factor if rung == Rung.REDUCE else 1.0
            quote_notional = limits.quote_notional_usd * size_factor
            directional_notional = limits.directional_notional_usd * size_factor

            fill_txt = "-"
            kill = False
            seq_before = getattr(alpaca, "_order_seq", 0)
            if rung == Rung.HOLD_LATE or action is None:
                line_action = "HOLD (late)"
            elif rung == Rung.KILL or (action and action.kind == KILL):
                line_action = "KILL (flatten)"
                kill = True
            else:
                # 7. risk veto happens inside execute_action via risk.check
                (
                    line_action,
                    fill_txt,
                    _exec_fill_qty,
                    _exec_fill_price,
                    resting_quotes,
                    rest_counter,
                ) = _execute_action(
                    alpaca=alpaca,
                    spec=spec,
                    action=action,
                    bid_px=bid_px,
                    ask_px=ask_px,
                    mid=mid,
                    quote_notional=quote_notional,
                    directional_notional=directional_notional,
                    snapshot=snapshot,
                    limits=limits,
                    inv=inv,
                    api_error_streak=api_error_streak,
                    decision_latency_ms=meta.get("latency_ms"),
                    resting_quotes=resting_quotes,
                    rest_counter=rest_counter,
                    now=now,
                    dry=dry_execution,
                    expected_px=expected_px,
                    pending_buy_usd=open_buys["usd"],
                )
                if line_action.startswith("KILL"):
                    kill = True  # a hard risk limit tripped inside the risk check
            if getattr(alpaca, "_order_seq", 0) != seq_before:
                reconcile_needed = True
            if kill:
                rung = Rung.KILL
                resting_quotes = None
                fill_txt = _flatten(
                    alpaca, spec, inv, dry_execution, fills_seen, expected_px,
                    session_start_iso, now,
                )
            elif recon_txt:
                fill_txt = recon_txt if fill_txt == "-" else f"{fill_txt}; {recon_txt}"

            # 9. log
            record = {
                "tick": block,
                "ts": now,
                "symbol": spec.symbol,
                "mid": mid,
                "vwap": snapshot["vwap"],
                "spread_bps": round(spread_bps, 2),
                "has_depth": spec.has_depth,
                "regime": answers["regime"]["choice"] if answers else None,
                "regime_conf": answers["regime"]["confidence"] if answers else None,
                "direction": answers["direction"]["choice"] if answers else None,
                "direction_conf": (
                    answers["direction"]["confidence"] if answers else None
                ),
                "toxic_flow": answers["toxic_flow"]["noul"] if answers else None,
                "liquidity_stressed": (
                    answers["liquidity_stressed"]["noul"] if answers else None
                ),
                "quote_environment": (
                    answers["quote_environment"]["score"] if answers else None
                ),
                "quote_environment_conf": (
                    answers["quote_environment"]["confidence"] if answers else None
                ),
                "inventory_pressure": (
                    answers["inventory_pressure"]["score"] if answers else None
                ),
                "execution_health": (
                    answers["execution_health"]["score"] if answers else None
                ),
                "action": action.kind if action else "HOLD_LATE",
                "action_reason": action.reason if action else "block deadline exceeded",
                "direction_leg": action.direction_leg if action else None,
                "skew": action.skew if action else 0.0,
                "rung": rung.value,
                "paused": line_action.startswith("PAUSED"),
                "late": rung == Rung.HOLD_LATE,
                "latency_ms": None if meta.get("reused") else meta.get("latency_ms"),
                "jev_reused": bool(meta.get("reused")),
                "judgment_age_s": meta.get("age_s", 0.0 if answers else None),
                "model": meta.get("model"),
                "route": meta.get("route"),
                "inventory": inv.inventory,
                "unrealised_pnl_usd": snapshot["unrealised_pnl_usd"],
                "drawdown_pct": snapshot["drawdown_pct"],
                "fees_usd": round(inv.fees_usd, 4),
                "fill": fill_txt,
                "fill_qty": fill_qty,
                "fill_price": fill_price,
            }
            _append_log(record)
            recent_ticks.append(record)
            if len(recent_ticks) > LATEST_WINDOW:
                recent_ticks = recent_ticks[-LATEST_WINDOW:]
            _write_latest(
                spec.symbol, block, recent_ticks, meta, started_at, api_error_streak
            )

            regime_txt = (
                f"{answers['regime']['choice']} {answers['regime']['confidence']*100:.0f}%"
                if answers
                else "n/a"
            )
            tox_txt = f"{answers['toxic_flow']['noul']:.2f}" if answers else "n/a"
            env_txt = (
                f"{answers['quote_environment']['score']:.1f}" if answers else "n/a"
            )
            xh_txt = f"{answers['execution_health']['score']:.1f}" if answers else "n/a"
            ms_txt = (
                f"reused {meta.get('age_s', 0):.0f}s" if meta.get("reused")
                else f"{meta.get('latency_ms'):.0f} ms" if meta.get("latency_ms") else "late"
            )
            print(
                f"tick {block} | mid {_fmt_money(mid)} | regime {regime_txt} | "
                f"tox {tox_txt} | env {env_txt} | xh {xh_txt} | {ms_txt} | {line_action} | {fill_txt}"
            )

            if rung == Rung.KILL:
                print(f"tick {block} | KILL: hard limit breached, {fill_txt}, stopping.")
                break

            n += 1
            _sleep_remaining(tick_start, cadence_s)

        return 0
    except (KeyboardInterrupt, _StopRequested):
        print(f"\ntick {block} | stopping: interrupt received.")
        return 0
    finally:
        # Every way out (Ctrl+C, kill, --ticks N finishing, KILL, a crash)
        # cancels the resting orders this run placed. The first published
        # version only did this on Ctrl+C, so a finished run left its
        # quotes working at the broker.
        if getattr(alpaca, "_order_seq", 0) and not dry_execution:
            try:
                n_cancelled = alpaca.cancel_own_orders()
                print(
                    f"tick {block} | {n_cancelled} of this run's resting orders cancelled "
                    "(nothing else on the account touched), shut down cleanly."
                )
            except AlpacaAPIError as exc:
                print(
                    f"tick {block} | could not cancel resting orders cleanly: {exc}. "
                    "Check Open Orders in Alpaca and cancel any starting with 'jevloop-'."
                )
        else:
            print(f"tick {block} | shut down cleanly, no resting orders to cancel.")
        if previous_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, previous_sigterm_handler)


def _read_top_of_book(
    alpaca, spec: AssetSpec
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Crypto: real L2 depth from the order book. Equities: best bid/ask
    from the latest quote only, wrapped in the same (price, size) shape so
    the rest of the loop never has to know the difference. Returns empty
    lists, never fabricated levels, when nothing is available."""
    if spec.has_depth:
        book = alpaca.get_orderbook()
        bids = [(float(l["p"]), float(l["s"])) for l in book.get("b", [])]
        asks = [(float(l["p"]), float(l["s"])) for l in book.get("a", [])]
        return bids, asks

    quote = alpaca.get_latest_quote()
    bids = (
        [(float(quote["bp"]), float(quote.get("bs", 0.0)))] if quote.get("bp") else []
    )
    asks = (
        [(float(quote["ap"]), float(quote.get("as", 0.0)))] if quote.get("ap") else []
    )
    return bids, asks


def _closed_market_record(block: int, now: float, symbol: str) -> dict:
    return {
        "tick": block,
        "ts": now,
        "symbol": symbol,
        "mid": None,
        "vwap": None,
        "spread_bps": None,
        "has_depth": False,
        "regime": None,
        "regime_conf": None,
        "direction": None,
        "toxic_flow": None,
        "liquidity_stressed": None,
        "quote_environment": None,
        "quote_environment_conf": None,
        "inventory_pressure": None,
        "execution_health": None,
        "action": "MARKET_CLOSED",
        "action_reason": "market closed, prices are stale",
        "direction_leg": None,
        "skew": 0.0,
        "rung": "hold_late",
        "late": False,
        "latency_ms": None,
        "model": None,
        "route": None,
        "inventory": 0.0,
        "unrealised_pnl_usd": 0.0,
        "drawdown_pct": 0.0,
        "fill": "-",
        "fill_qty": None,
        "fill_price": None,
    }


def _execute_action(
    *,
    alpaca,
    spec: AssetSpec,
    action,
    bid_px,
    ask_px,
    mid,
    quote_notional,
    directional_notional,
    snapshot,
    limits,
    inv,
    api_error_streak,
    decision_latency_ms,
    resting_quotes,
    rest_counter,
    now,
    dry: bool = False,
    expected_px: dict | None = None,
    pending_buy_usd: float = 0.0,
):
    """Runs the risk check, then places (or, if `dry` is true, only logs)
    the order implied by `action`. `dry` never calls cancel_own_orders,
    submit_limit_order, or submit_market_order: it reads real market data
    and gets a real Jev battery answer, but never touches the Alpaca order
    book. Every fill line in dry mode starts with "dry:". Order sizes are
    computed from a dollar target (assets.size_order), not a fixed
    quantity, so the same limits work across any asset."""
    from .risk import check as risk_check

    # Held too long: stop adding and close it out. The first published
    # version vetoed every order instead, the exit included, so a stuck
    # position froze the loop after 15 minutes.
    aged = (
        snapshot.get("inventory", 0) != 0
        and snapshot.get("position_age_s", 0) > limits.max_inventory_age_s
    )
    order_notional_usd = max(quote_notional, directional_notional)
    verdict = risk_check(
        snapshot, order_notional_usd, limits, api_error_streak, decision_latency_ms,
        closing=aged,
    )
    if not verdict.ok:
        if verdict.kill:
            return f"KILL ({verdict.veto})", "-", None, None, None, 0
        return (
            f"VETOED ({verdict.veto})",
            "-",
            None,
            None,
            resting_quotes,
            rest_counter,
        )

    # Stop on the dashboard: checked before every order. Pulls this run's
    # resting quotes so nothing new can fill, and places nothing. It never
    # closes a position; a KILL (above, and in the loop) still does.
    if control.is_paused(LOG_DIR):
        fill_txt = "-"
        if resting_quotes and not dry:
            try:
                alpaca.cancel_own_orders()
                fill_txt = "resting quotes pulled"
            except AlpacaAPIError as exc:
                fill_txt = f"could not pull resting quotes: {exc}"
        return "PAUSED (no new orders)", fill_txt, None, None, None, 0

    if aged:
        line_action = "EXIT (held past max_inventory_age_s)"
        if dry:
            return line_action, f"dry: would close {inv.inventory}", None, None, None, 0
        try:
            alpaca.cancel_own_orders()
            fill_txt = _close_position(alpaca, spec, inv, mid, expected_px)
        except MarketClosedError as exc:
            fill_txt = f"exit skipped: {exc}"
        except AlpacaAPIError as exc:
            inv.orders_rejected += 1
            fill_txt = f"exit rejected: {exc}"
        return line_action, fill_txt, None, None, None, 0

    # Room left under the position cap, counting buys still working at the
    # broker, not just what has filled. Without this, resting bids and buy
    # legs piled up past max_position_usd before any of them showed as
    # inventory.
    position_usd = max(snapshot.get("inventory", 0.0), 0.0) * mid
    buy_room_usd = limits.max_position_usd - position_usd - pending_buy_usd

    fill_txt = "-"
    line_action = action.kind

    if action.kind in (PULL_QUOTES, STAND_DOWN):
        if resting_quotes and not dry:
            try:
                alpaca.cancel_own_orders()
            except AlpacaAPIError:
                pass
        return line_action, fill_txt, None, None, None, 0

    if action.kind == WIDEN:
        wide_bid, wide_ask = bid_px * 0.999, ask_px * 1.001
        return (
            f"{line_action} bid {wide_bid:,.1f}/ask {wide_ask:,.1f}",
            fill_txt,
            None,
            None,
            resting_quotes,
            rest_counter,
        )

    if action.kind in (QUOTE_BOTH_SIDES, QUOTE_WIDE):
        fill_qty, fill_price = None, None
        buy_qty = size_order(quote_notional, bid_px, spec)
        sell_qty = size_order(quote_notional, ask_px, spec)
        # Gas-honesty rule: only cancel-replace every `rest_ticks` ticks.
        rest_counter += 1
        if resting_quotes is None or rest_counter >= limits.rest_ticks:
            if dry:
                resting_quotes = {"bid": bid_px, "ask": ask_px}
                rest_counter = 0
                fill_txt = f"dry: would quote {buy_qty}/{sell_qty} @ {bid_px:,.2f}/{ask_px:,.2f}"
            else:
                # Note: this account cannot short. A sell quote placed with
                # no inventory to back it is a real, expected rejection on a
                # cash account, caught as an AlpacaAPIError below.
                try:
                    if resting_quotes:
                        alpaca.cancel_own_orders()
                        # Our resting bid is gone; only filled coin counts now.
                        held_usd = max(alpaca.get_position_qty(), inv.inventory, 0.0) * mid
                        buy_room_usd = limits.max_position_usd - held_usd
                    sides = [("sell", sell_qty, ask_px)]
                    if buy_qty * bid_px <= buy_room_usd:
                        sides.insert(0, ("buy", buy_qty, bid_px))
                        buy_room_usd -= buy_qty * bid_px
                    else:
                        fill_txt = f"bid skipped: ${limits.max_position_usd:.0f} position cap"
                    inv.orders_submitted += len(sides)
                    for side_, qty_, px_ in sides:
                        o = alpaca.submit_limit_order(side_, qty_, px_)
                        if expected_px is not None and o.get("client_order_id"):
                            expected_px[o["client_order_id"]] = px_
                    resting_quotes = {"bid": bid_px, "ask": ask_px}
                    rest_counter = 0
                except MarketClosedError as exc:
                    return (
                        f"{line_action} ({exc})",
                        fill_txt,
                        None,
                        None,
                        resting_quotes,
                        rest_counter,
                    )
                except AlpacaAPIError as exc:
                    return (
                        f"{line_action} (order error: {exc})",
                        fill_txt,
                        None,
                        None,
                        resting_quotes,
                        rest_counter,
                    )

        if action.direction_leg == "down" and not spec.shorting_allowed:
            # Alpaca crypto is spot and this account is cash, so it cannot
            # short. The bot runs long or flat: a SELL closes the long this
            # run built (never more than Alpaca says is held) and does
            # nothing when flat.
            line_action = f"{action.kind} skew {action.skew:+.1f} + sell leg"
            own = max(inv.inventory, 0.0)
            if own <= 0:
                fill_txt = ("dry: " if dry else "") + "no position to close"
            elif dry:
                fill_txt = f"dry: would close long {own}"
                line_action += " (dry)"
            else:
                try:
                    held = max(alpaca.get_position_qty(), 0.0)
                    qty = _floor_qty(min(own, held), spec)
                    if qty <= 0:
                        fill_txt = "no position to close"
                    else:
                        inv.orders_submitted += 1
                        o = alpaca.submit_market_order("sell", qty)
                        if expected_px is not None and o.get("client_order_id"):
                            expected_px[o["client_order_id"]] = mid
                        fill_txt = f"sent market sell {qty} (closing long)"
                except MarketClosedError as exc:
                    fill_txt = f"leg skipped: {exc}"
                except AlpacaAPIError as exc:
                    inv.orders_rejected += 1
                    fill_txt = f"leg rejected: {exc}"
        elif action.direction_leg in ("up", "down"):
            side = "buy" if action.direction_leg == "up" else "sell"
            fill_px = bid_px if side == "sell" else ask_px
            leg_qty = size_order(directional_notional, fill_px, spec)
            if side == "buy" and leg_qty * fill_px > buy_room_usd:
                fill_txt = f"buy leg skipped: ${limits.max_position_usd:.0f} position cap"
                line_action = f"{action.kind} skew {action.skew:+.1f}"
            elif dry:
                fill_txt = f"dry: would {side} {leg_qty} @ {fill_px:,.2f}"
                line_action = (
                    f"{action.kind} skew {action.skew:+.1f} + {side} leg (dry)"
                )
            else:
                try:
                    inv.orders_submitted += 1
                    o = alpaca.submit_market_order(side, leg_qty)
                    if expected_px is not None and o.get("client_order_id"):
                        expected_px[o["client_order_id"]] = mid
                    # Not recorded as filled here: inventory and PnL only move
                    # when Alpaca reports the fill (reconcile_fills, next tick).
                    fill_txt = f"sent market {side} {leg_qty}"
                    line_action = f"{action.kind} skew {action.skew:+.1f} + {side} leg"
                except MarketClosedError as exc:
                    fill_txt = f"leg skipped: {exc}"
                except AlpacaAPIError as exc:
                    inv.orders_rejected += 1
                    fill_txt = f"leg rejected: {exc}"
        else:
            line_action = f"{action.kind} skew {action.skew:+.1f}"

        return line_action, fill_txt, fill_qty, fill_price, resting_quotes, rest_counter

    return line_action, fill_txt, None, None, resting_quotes, rest_counter


def _seconds_to_bar_close(now: float, bar_seconds: float, settle: float = BAR_SETTLE_S) -> float:
    """Seconds from `now` until the next bar close (wall clock, UTC-aligned,
    so 30m bars close at :00 and :30), plus a short settle."""
    next_close = (math.floor((now - settle) / bar_seconds) + 1) * bar_seconds + settle
    return max(0.0, next_close - now)


def _minute_bar_history(alpaca, now: float) -> list[tuple[float, float]]:
    """Real one-minute closes for the last HISTORY_S seconds, each stamped at
    its bar's close. Used at startup, and at every bar close in --bar mode so
    the 1m/5m/30m returns and volatility stay real between decisions."""
    hist: list[tuple[float, float]] = []
    for b in alpaca.get_minute_bars(_iso(now - HISTORY_S)):
        close_ts = _parse_ts(b["t"]) + 60.0
        if close_ts <= now and float(b.get("c", 0)) > 0:
            hist.append((close_ts, float(b["c"])))
    return hist


def _sleep_remaining(tick_start: float, tick_seconds: float) -> None:
    elapsed = time.monotonic() - tick_start
    remaining = tick_seconds - elapsed
    if remaining > 0:
        time.sleep(remaining)


def _append_log(record: dict) -> None:
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(record) + "\n")


def _write_latest(symbol, block, ticks, meta, started_at, api_error_streak) -> None:
    calls = len(ticks)
    late = sum(1 for t in ticks if t["action"] in ("HOLD_LATE", "MARKET_CLOSED"))
    latencies = [t["latency_ms"] for t in ticks if t.get("latency_ms")]
    avg_ms = sum(latencies) / len(latencies) if latencies else None
    payload = {
        "generated_at": time.time(),
        "symbol": symbol,
        "block": block,
        "ticks": ticks,
        "stats": {
            "avg_ms": avg_ms,
            "calls": calls,
            "late_count": late,
            "uptime_s": time.time() - started_at,
            "decision_client": meta.get("route"),
            "model": meta.get("model"),
            "api_error_streak": api_error_streak,
        },
    }
    _atomic_write(LATEST_FILE, json.dumps(payload))


def _atomic_write(path: Path, text: str, attempts: int = 8, first_wait_s: float = 0.01) -> bool:
    """Write to a temp file, then swap it in with os.replace. On Windows the
    swap raises PermissionError while another process (the dashboard server)
    has the old file open, where Mac and Linux allow it. Retry with a short
    backoff (10, 20, 40 ... ms, about 2.5 s in total); if the file is still
    locked, skip this tick's refresh rather than crash the loop. The next
    tick writes a fresh copy anyway."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text)
    wait = first_wait_s
    for attempt in range(attempts):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            if attempt == attempts - 1:
                break
            time.sleep(wait)
            wait *= 2
    try:
        tmp.unlink()
    except OSError:
        pass
    print(f"note: {path.name} was locked by a reader, skipped one refresh")
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jev-loop run")
    parser.add_argument(
        "--paper",
        action="store_true",
        default=True,
        help="paper mode (the default, and the only mode unless --live is used)",
    )
    parser.add_argument(
        "--mock", action="store_true", help="force the mock decision client"
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=None,
        help="stop after N ticks; 0 means run forever (same as --forever)",
    )
    parser.add_argument(
        "--forever",
        action="store_true",
        help="run continuously until stopped (Ctrl+C, or SIGTERM in the background), same as --ticks 0",
    )
    parser.add_argument("--symbol", default=os.environ.get("DEFAULT_SYMBOL", "BTC/USD"))
    parser.add_argument(
        "--dry-execution",
        action="store_true",
        help="real market data and a real Jev battery, but never submit an order to Alpaca",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "trade real money on Alpaca's live endpoint instead of paper. Also "
            "requires JEV_LOOP_ALLOW_LIVE=i-understand-the-risk in the environment "
            "and a typed confirmation at startup; missing either refuses to start. "
            "See SKILL.md / README.md before ever using this."
        ),
    )
    parser.add_argument(
        "--bar",
        choices=sorted(BAR_CHOICES, key=BAR_CHOICES.get),
        default=None,
        help=(
            "decide once per bar close (e.g. 30m = at :00 and :30 UTC) instead of "
            "every 2 s block. Returns and volatility come from real one-minute bars."
        ),
    )
    args = parser.parse_args(argv)

    ticks = None if (args.forever or args.ticks == 0) else args.ticks

    confirmation = None
    if args.live:
        print("\n" + "!" * 70)
        print("! --live was passed. This is not paper trading.")
        print("! Every order this places spends real money in your real Alpaca")
        print("! account, with no paper safety net.")
        print("!" * 70)
        try:
            confirmation = input(
                f"Type exactly '{LIVE_CONFIRMATION_PHRASE}' to continue, anything else cancels: "
            )
        except EOFError:
            confirmation = None

    limits = Limits()
    return run(
        symbol=args.symbol,
        ticks=ticks,
        mock=args.mock,
        limits=limits,
        dry_execution=args.dry_execution,
        live=args.live,
        confirmation=confirmation,
        bar_seconds=BAR_CHOICES[args.bar] if args.bar else None,
    )


if __name__ == "__main__":
    sys.exit(main())
```

Write `~/.claude/skills/jev-loop/jevloop/calibrate.py`:

```python
"""Calibration: does 80% mean 80% on this venue?

Reads the tick log, pairs each up/down `direction` call and Jev's own
confidence in it with the realised price move N ticks later, and reports a
Brier score plus a 10-bin reliability table (stated confidence vs how often
calls at that confidence were right). Writes reliability.png if matplotlib
happens to be installed; otherwise the table alone is enough.

This is not "did Jev predict price" in isolation. It is the honest check
the article insists on: if the model says 80%, does 80% actually happen.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

LOG_DIR = Path(os.environ.get("JEV_LOOP_HOME", str(Path.home() / ".jev-loop")))
LOG_FILE = LOG_DIR / "log.jsonl"


def load_ticks() -> list[dict]:
    if not LOG_FILE.exists():
        return []
    ticks = []
    with LOG_FILE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                ticks.append(json.loads(line))
    return ticks


def pair_predictions(ticks: list[dict], horizon: int = 5) -> list[tuple[float, int]]:
    """(stated confidence, was the call right) pairs for every up/down
    direction call, checked `horizon` ticks later.

    The confidence is Jev's own confidence in that direction call
    (`direction_conf` in the log), nothing else. A "neutral" call makes no
    up/down claim, so it is left out rather than scored as 50%. A tick
    whose outcome price is missing (market closed) is skipped. Logs written
    before `direction_conf` existed carry no direction confidence at all
    and produce no pairs: there is no honest number to score them on."""
    pairs = []
    for i, t in enumerate(ticks):
        direction = t.get("direction")
        conf = t.get("direction_conf")
        if direction not in ("up", "down") or conf is None:
            continue
        j = i + horizon
        if j >= len(ticks):
            continue
        start, end = t.get("mid"), ticks[j].get("mid")
        if start is None or end is None or end == start:
            continue  # no move, nothing to score
        moved_up = end > start
        correct = 1 if moved_up == (direction == "up") else 0
        pairs.append((float(conf), correct))
    return pairs


def brier_score(pairs: list[tuple[float, int]]) -> float:
    if not pairs:
        return float("nan")
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def reliability_table(pairs: list[tuple[float, int]], n_bins: int = 10) -> list[dict]:
    bins = [[] for _ in range(n_bins)]
    for p, y in pairs:
        idx = min(n_bins - 1, int(p * n_bins))
        bins[idx].append((p, y))
    rows = []
    for i, b in enumerate(bins):
        lo, hi = i / n_bins, (i + 1) / n_bins
        if b:
            mean_pred = sum(p for p, _ in b) / len(b)
            empirical = sum(y for _, y in b) / len(b)
        else:
            mean_pred, empirical = float("nan"), float("nan")
        rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(b), "mean_predicted": mean_pred, "empirical": empirical})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jev-loop calibrate")
    parser.add_argument("--horizon", type=int, default=5, help="ticks ahead to check the realised outcome")
    args = parser.parse_args(argv)

    ticks = load_ticks()
    if not ticks:
        print(f"No log found at {LOG_FILE}. Run `jev-loop run --ticks 60` first.")
        return 1

    pairs = pair_predictions(ticks, horizon=args.horizon)
    if not pairs:
        print(
            "Not enough up/down direction calls with a logged confidence yet. "
            "Run a longer session (logs from before this update carry no "
            "direction confidence and cannot be scored)."
        )
        return 1

    score = brier_score(pairs)
    print(f"\ncalibration over {len(pairs)} decisions, horizon {args.horizon} ticks")
    print(f"Brier score: {score:.4f} (0 = perfect, 0.25 = coin flip, 1 = always wrong)\n")
    print(f"{'bin':>10} {'n':>5} {'stated conf':>15} {'hit rate':>10}")
    for row in reliability_table(pairs):
        mp = f"{row['mean_predicted']:.2f}" if row["n"] else "-"
        emp = f"{row['empirical']:.2f}" if row["n"] else "-"
        print(f"{row['bin']:>10} {row['n']:>5} {mp:>15} {emp:>10}")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        rows = reliability_table(pairs)
        xs = [i / len(rows) + 0.5 / len(rows) for i in range(len(rows))]
        ys = [r["empirical"] for r in rows]
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfectly calibrated")
        ax.plot(xs, ys, marker="o", label="this run")
        ax.set_xlabel("stated confidence in the direction call")
        ax.set_ylabel("how often the call was right")
        ax.set_title("Reliability: does 80% mean 80%?")
        ax.legend()
        out = LOG_DIR / "reliability.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        print(f"\nwrote {out}")
    except ImportError:
        print("\n(matplotlib not installed, skipping reliability.png; the table above is the same data)")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
```

Write `~/.claude/skills/jev-loop/jevloop/control.py`:

```python
"""Start / Stop for the loop, driven from the dashboard.

Two small files in ~/.jev-loop/ (or $JEV_LOOP_HOME):

  control.json   {"state": "RUNNING"} or {"state": "PAUSED"}. The loop reads
                 it before every order, so a press on the dashboard takes
                 effect on the next tick, and it survives a page refresh or
                 a restart of either process. No file means RUNNING.
  control.token  a random per-install secret, made the first time the
                 dashboard server starts. The dashboard sends it with every
                 Start/Stop press; anything without it is refused.

PAUSED stops new orders only. Market data, Jev decisions, the log and the
dashboard all keep updating. It does not close a position: the KILL switch
(the hard risk limits) does that, and still does while paused.
"""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path

RUNNING = "RUNNING"
PAUSED = "PAUSED"
STATES = (RUNNING, PAUSED)


def _state_file(home: Path) -> Path:
    return Path(home) / "control.json"


def read_state(home: Path, attempts: int = 5, wait_s: float = 0.02) -> str:
    """RUNNING or PAUSED. A missing file is RUNNING. A file that can't be
    read after a few tries (a Windows lock that won't clear, or garbage) is
    treated as PAUSED: when in doubt, don't place the order."""
    path = _state_file(home)
    for _ in range(attempts):
        try:
            state = json.loads(path.read_bytes()).get("state")
            return state if state in STATES else PAUSED
        except FileNotFoundError:
            return RUNNING
        except (PermissionError, ValueError, AttributeError):
            time.sleep(wait_s)
    return PAUSED


def is_paused(home: Path) -> bool:
    return read_state(home) == PAUSED


def write_state(home: Path, state: str, attempts: int = 8) -> None:
    """Atomic swap with a short retry, so a reader never sees half a file
    and a Windows reader holding it open only delays the swap."""
    if state not in STATES:
        raise ValueError(f"state must be one of {STATES}, got {state!r}")
    path = _state_file(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"state": state, "changed_at": time.time()}))
    wait = 0.01
    for i in range(attempts):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == attempts - 1:
                tmp.unlink(missing_ok=True)
                raise
            time.sleep(wait)
            wait *= 2


def load_or_create_token(home: Path) -> str:
    """The per-install token. Created once with owner-only permissions
    where the OS supports them (Mac, Linux); on Windows the file sits in
    the user's own profile folder, which other users can't read."""
    path = Path(home) / "control.token"
    try:
        token = path.read_text().strip()
        if token:
            return token
    except FileNotFoundError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return token
```


Write `~/.claude/skills/jev-loop/jevloop/serve.py`:

```python
"""`jevloop serve`: a tiny static file server for the dashboard.

Serves the dashboard HTML files alongside ~/.jev-loop/latest.json so
dashboard/index.html and dashboard/wall.html can poll it with a plain
fetch(). No framework, no build step: http.server with two directories
merged via a symlink-free request handler.

Start / Stop: GET /control returns {"state": "RUNNING" | "PAUSED"}; POST
/control with {"state": ...} changes it. The server only listens on
127.0.0.1. A POST needs the per-install token from ~/.jev-loop/control.token
in an X-Jev-Token header, which the server writes into the dashboard page
it serves; a page on any other site can't read it (no CORS headers are ever
sent) and can't send that header without a CORS preflight, which is
refused. The Host header must be 127.0.0.1 or localhost, so a website
that re-points its own name at 127.0.0.1 (DNS rebinding) is refused too.
"""

from __future__ import annotations

import argparse
import hmac
import http.server
import json
import os
import socketserver
import time
from pathlib import Path

from . import control

LOG_DIR = Path(os.environ.get("JEV_LOOP_HOME", str(Path.home() / ".jev-loop")))
SKILL_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = SKILL_DIR / "dashboard"


_last_good: dict[str, bytes] = {}


def read_feed(path: Path, attempts: int = 5, wait_s: float = 0.02) -> bytes | None:
    """Read a feed file in one go and close it straight away, so the server
    never holds latest.json open while the loop swaps in a new copy (on
    Windows an open file blocks that swap). A read that hits the swap
    mid-way (PermissionError, or JSON cut short) is retried briefly, then
    falls back to the last good copy served, never an error page."""
    for _ in range(attempts):
        try:
            data = path.read_bytes()
            if path.suffix == ".json":
                json.loads(data)  # a partial write fails here, not in the browser
            _last_good[path.name] = data
            return data
        except FileNotFoundError:
            break
        except (PermissionError, ValueError):
            time.sleep(wait_s)
    return _last_good.get(path.name)


TOKEN_PLACEHOLDER = b"__JEV_CONTROL_TOKEN__"
MAX_CONTROL_BODY = 1024


class Handler(http.server.SimpleHTTPRequestHandler):
    def _host_ok(self) -> bool:
        port = self.server.server_address[1]
        host = (self.headers.get("Host") or "").lower()
        return host in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _send(self, code: int, data: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_state(self, code: int = 200) -> None:
        self._send(code, json.dumps({"state": control.read_state(LOG_DIR)}).encode())

    def _refuse(self, code: int, why: str) -> None:
        self._send(code, json.dumps({"error": why}).encode())

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path != "/control":
            return self._refuse(404, "not found")
        if not self._host_ok():
            return self._refuse(403, "bad host")
        port = self.server.server_address[1]
        origin = self.headers.get("Origin")
        if origin and origin.lower() not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
            return self._refuse(403, "bad origin")
        sent = self.headers.get("X-Jev-Token", "")
        token = control.load_or_create_token(LOG_DIR)
        if not hmac.compare_digest(sent.encode(), token.encode()):
            return self._refuse(403, "bad token")
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_CONTROL_BODY:
                raise ValueError
            state = json.loads(self.rfile.read(length) or b"{}").get("state")
            if state not in control.STATES:
                raise ValueError
        except (ValueError, AttributeError):
            return self._refuse(400, 'send {"state": "RUNNING"} or {"state": "PAUSED"}')
        try:
            control.write_state(LOG_DIR, state)
        except PermissionError:
            return self._refuse(503, "control file busy, try again")
        self._send_state()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path == "/control":
            if not self._host_ok():
                return self._refuse(403, "bad host")
            return self._send_state()
        if path in ("/", "/index.html"):
            # The Start/Stop token goes into the page, and only for a
            # request addressed to this machine by name or IP.
            if not self._host_ok():
                return self._refuse(403, "bad host")
            try:
                page = (DASHBOARD_DIR / "index.html").read_bytes()
            except FileNotFoundError:
                return self._refuse(404, "dashboard/index.html missing")
            page = page.replace(TOKEN_PLACEHOLDER, control.load_or_create_token(LOG_DIR).encode())
            return self._send(200, page, "text/html; charset=utf-8")
        if path not in ("/latest.json", "/log.jsonl"):
            return super().do_GET()
        data = read_feed(LOG_DIR / path.lstrip("/"))
        if data is None:
            data = b'{"ticks": [], "stats": {}}' if path == "/latest.json" else b""
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/json" if path == "/latest.json" else "text/plain",
        )
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def translate_path(self, path: str) -> str:
        path = path.split("?", 1)[0].split("#", 1)[0]
        if path in ("/latest.json", "/log.jsonl"):
            return str(LOG_DIR / path.lstrip("/"))
        if path == "/":
            path = "/index.html"
        candidate = DASHBOARD_DIR / path.lstrip("/")
        return str(candidate)

    def log_message(self, format, *args):  # noqa: A002
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jev-loop serve")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    latest = LOG_DIR / "latest.json"
    if not latest.exists():
        latest.write_text('{"ticks": [], "stats": {}}')
    control.load_or_create_token(LOG_DIR)

    with socketserver.TCPServer(("127.0.0.1", args.port), Handler) as httpd:
        print(f"dashboard: http://127.0.0.1:{args.port}/index.html")
        print(f"dark wall: http://127.0.0.1:{args.port}/wall.html")
        print(f"raw feed:  http://127.0.0.1:{args.port}/latest.json")
        print(f"control:   {control.read_state(LOG_DIR)} (Start/Stop buttons on the dashboard)")
        print("Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
```

Write `~/.claude/skills/jev-loop/jevloop/__main__.py`:

```python
"""CLI dispatcher: `jev-loop run|calibrate|serve|pause|resume|validate-symbol|explain-split`.

Also invocable as `uv run python -m jevloop <command> ...` from inside the
skill directory, which is what the /jev-loop skill's SKILL.md tells Claude
Code to run.
"""

from __future__ import annotations

import sys

USAGE = "usage: jev-loop <run|calibrate|serve|pause|resume|validate-symbol|explain-split> [options]"


def _validate_symbol(argv: list[str]) -> int:
    from .assets import UnknownSymbolError, resolve_symbol

    if not argv:
        print("usage: jev-loop validate-symbol <SYMBOL>")
        return 1
    try:
        spec = resolve_symbol(argv[0])
    except UnknownSymbolError as exc:
        print(str(exc))
        return 1

    session = "24/7 (crypto)" if spec.is_24_7 else "market hours only (US equity)"
    print(f"resolved: {spec.symbol}")
    print(f"  asset class:       {spec.asset_class}")
    print(f"  session:           {session}")
    print(f"  min order notional: ${spec.min_notional_usd:.2f}")
    print(f"  quantity precision: {spec.qty_precision} decimal places")
    print(f"  shorting allowed:   {spec.shorting_allowed}")
    print(f"  order book depth:   {'yes' if spec.has_depth else 'best bid/ask only'}")
    return 0


def _explain_split(argv: list[str]) -> int:
    from .split import render_split_table

    print(render_split_table())
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(USAGE)
        return 1

    command, rest = sys.argv[1], sys.argv[2:]
    if command == "run":
        from . import loop

        return loop.main(rest)
    if command == "calibrate":
        from . import calibrate

        return calibrate.main(rest)
    if command == "serve":
        from . import serve

        return serve.main(rest)
    if command in ("pause", "resume"):
        from . import control
        from .loop import LOG_DIR

        state = control.PAUSED if command == "pause" else control.RUNNING
        control.write_state(LOG_DIR, state)
        print(f"control: {state}" + (" (no new orders; positions stay open)" if state == control.PAUSED else ""))
        return 0
    if command == "validate-symbol":
        return _validate_symbol(rest)
    if command == "explain-split":
        return _explain_split(rest)

    print(f"unknown command: {command!r}. {USAGE}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

Write `~/.claude/skills/jev-loop/dashboard/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="jev-control-token" content="__JEV_CONTROL_TOKEN__" />
    <title>PTQ · Jev loop</title>
    <link
      href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Fragment+Mono&family=Instrument+Serif:ital@1&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --canvas: #f6f6f8;
        --ink: #0b0b10;
        --ink2: #3b3f4b;
        --ink3: #5b5f6b;
        --muted: #8a8f9c;
        --hair: rgba(11, 11, 16, 0.1);
        --hair2: rgba(11, 11, 16, 0.14);
        --blue: #0a8cff;
        --green: #1f7a4d;
        --red: #b91c1c;
        --amber: #b7791f;
        --green-soft: rgba(31, 122, 77, 0.1);
        --red-soft: rgba(216, 13, 13, 0.08);
        --amber-soft: rgba(183, 121, 31, 0.1);
        --blue-soft: rgba(10, 140, 255, 0.1);
        --card: rgba(255, 255, 255, 0.72);
        --sans: "Instrument Sans", -apple-system, Helvetica, Arial, sans-serif;
        --mono: "Fragment Mono", ui-monospace, Menlo, monospace;
        --serif: "Instrument Serif", Georgia, serif;
      }
      * {
        box-sizing: border-box;
      }
      html,
      body {
        margin: 0;
        height: 100%;
        background: var(--canvas);
        color: var(--ink);
        font-family: var(--sans);
        font-size: 14px;
        -webkit-font-smoothing: antialiased;
      }
      body {
        background:
          radial-gradient(
            60% 55% at 12% 0%,
            rgba(255, 138, 212, 0.35),
            transparent 60%
          ),
          radial-gradient(
            55% 60% at 88% 8%,
            rgba(140, 200, 255, 0.38),
            transparent 60%
          ),
          radial-gradient(
            50% 50% at 70% 100%,
            rgba(179, 157, 255, 0.3),
            transparent 60%
          ),
          radial-gradient(
            45% 45% at 15% 100%,
            rgba(255, 178, 122, 0.28),
            transparent 60%
          ),
          var(--canvas);
        display: grid;
        place-items: center;
        padding: 28px;
      }
      .frame {
        width: min(1640px, 100%);
        height: calc(100vh - 56px);
        min-height: 720px;
        display: flex;
        flex-direction: column;
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 22px;
        box-shadow: 0 30px 80px rgba(11, 11, 16, 0.1);
        padding: 22px 26px 24px;
      }
      header {
        display: flex;
        align-items: center;
        gap: 18px;
      }
      .brand {
        display: flex;
        align-items: baseline;
        gap: 10px;
      }
      .brand b {
        font-size: 19px;
        font-weight: 600;
        letter-spacing: -0.01em;
      }
      .brand i {
        font-family: var(--serif);
        font-style: italic;
        font-size: 19px;
        color: var(--ink2);
      }
      .block {
        font-family: var(--mono);
        color: var(--ink3);
        font-size: 13px;
        margin-left: 6px;
      }
      .pills {
        margin-left: auto;
        display: flex;
        gap: 8px;
      }
      .pill {
        font-family: var(--mono);
        font-size: 12px;
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid var(--hair2);
        background: rgba(255, 255, 255, 0.7);
        color: var(--ink2);
      }
      .pill.blue {
        background: var(--blue-soft);
        border-color: transparent;
        color: #0763b8;
      }
      .pill.live {
        background: var(--green-soft);
        border-color: transparent;
        color: var(--green);
      }
      .pill.mock {
        background: var(--amber-soft);
        border-color: transparent;
        color: var(--amber);
      }
      .pill .dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--green);
        margin-right: 7px;
        animation: pulse 1.2s infinite;
      }
      .control {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .ctlstate.running {
        background: var(--green-soft);
        border-color: transparent;
        color: var(--green);
      }
      .ctlstate.paused {
        background: var(--amber-soft);
        border-color: transparent;
        color: var(--amber);
      }
      .ctlbtn {
        font-family: var(--mono);
        font-size: 12px;
        padding: 6px 14px;
        border-radius: 999px;
        border: 1px solid var(--hair2);
        background: rgba(255, 255, 255, 0.9);
        color: var(--ink);
        cursor: pointer;
      }
      .ctlbtn:hover:not(:disabled) {
        border-color: var(--ink3);
      }
      .ctlbtn:disabled {
        opacity: 0.4;
        cursor: default;
      }
      .ctlnote {
        font-family: var(--mono);
        font-size: 12px;
        color: var(--ink3);
        margin: 8px 0 0;
      }
      .ctlnote.err {
        color: var(--red);
      }
      @keyframes pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.35;
        }
      }
      .stats {
        display: flex;
        gap: 22px;
        margin: 10px 0 14px;
        font-family: var(--mono);
        font-size: 12.5px;
        color: var(--ink3);
      }
      .stats b {
        color: var(--ink);
        font-weight: 500;
      }
      .stats .right {
        margin-left: auto;
      }
      .grid {
        display: grid;
        grid-template-columns: 1.3fr 0.9fr;
        gap: 16px;
        flex: 1;
        min-height: 0;
      }
      .card {
        background: var(--card);
        border: 1px solid var(--hair);
        border-radius: 16px;
        padding: 18px 20px;
        position: relative;
        overflow: hidden;
        min-height: 0;
      }
      .left {
        display: flex;
        flex-direction: column;
      }
      .eyebrow {
        font-family: var(--mono);
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }
      .pricebar {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
      }
      .price {
        font-family: var(--mono);
        font-size: 46px;
        line-height: 1;
        letter-spacing: -0.02em;
      }
      .sub {
        display: flex;
        gap: 14px;
        margin-top: 8px;
        font-size: 13px;
        color: var(--ink3);
      }
      .sub .pnl {
        font-family: var(--mono);
      }
      .pnl.neg {
        color: var(--red);
      }
      .pnl.pos {
        color: var(--green);
      }
      .verdict {
        text-align: right;
      }
      .verdict .act {
        font-size: 32px;
        font-weight: 500;
        letter-spacing: -0.01em;
        transition: color 0.15s;
      }
      .verdict .meta {
        font-family: var(--mono);
        font-size: 12.5px;
        color: var(--ink3);
        margin-top: 6px;
      }
      .act.buy {
        color: var(--green);
      }
      .act.sell {
        color: var(--red);
      }
      .act.late {
        color: var(--amber);
      }
      .snap {
        margin-top: 12px;
        padding: 8px 10px;
        border-radius: 10px;
        background: rgba(11, 11, 16, 0.04);
        font-family: var(--mono);
        font-size: 11.5px;
        color: var(--ink3);
        display: flex;
        flex-wrap: wrap;
        gap: 6px 16px;
      }
      .snap b {
        font-weight: 400;
        color: var(--ink);
      }
      .snap .k {
        color: var(--muted);
      }
      .chart {
        margin-top: 10px;
        flex: 1;
        min-height: 240px;
        position: relative;
      }
      .chart svg {
        width: 100%;
        height: 100%;
        display: block;
        overflow: visible;
      }
      .axis {
        font-family: var(--mono);
        font-size: 11px;
        fill: var(--muted);
      }
      .tag {
        font-family: var(--mono);
        font-size: 12px;
      }
      .strip {
        display: flex;
        gap: 3px;
        height: 22px;
        margin-top: 10px;
        align-items: flex-end;
      }
      .strip i {
        flex: 1;
        min-width: 0;
        height: 100%;
        border-radius: 3px;
        background: var(--hair);
        transition: background 0.2s;
      }
      .strip i.buy {
        background: #7cc9a0;
      }
      .strip i.sell {
        background: #e79a94;
      }
      .strip i.late {
        background: #e2c072;
      }
      .strip i:last-child {
        outline: 2px solid var(--ink);
        outline-offset: 1px;
      }
      .foot {
        display: flex;
        justify-content: space-between;
        margin-top: 12px;
        font-family: var(--mono);
        font-size: 11.5px;
        color: var(--muted);
      }
      /* right */
      .rcol {
        display: grid;
        grid-template-rows: auto auto minmax(0, 1fr);
        gap: 16px;
        min-height: 0;
      }
      .order {
        font-family: var(--mono);
        font-size: 12.5px;
        color: var(--ink2);
        margin-top: 8px;
        line-height: 1.6;
      }
      .side {
        position: relative;
      }
      .side .big {
        display: flex;
        align-items: baseline;
        gap: 16px;
        margin-top: 8px;
      }
      .side .word {
        font-size: 64px;
        font-weight: 600;
        letter-spacing: -0.03em;
        line-height: 1;
      }
      .side .pct {
        font-family: var(--mono);
        font-size: 30px;
        color: var(--ink2);
      }
      .side.buy .word {
        color: var(--green);
      }
      .side.sell .word {
        color: var(--red);
      }
      .side.late .word {
        color: var(--amber);
      }
      .side .word.flip {
        animation: flip 0.45s ease;
      }
      @keyframes flip {
        0% {
          transform: translateY(10px);
          opacity: 0;
        }
        60% {
          transform: translateY(-3px);
          opacity: 1;
        }
        100% {
          transform: none;
        }
      }
      .side .flash {
        position: absolute;
        inset: 0;
        pointer-events: none;
        opacity: 0;
        border-radius: 16px;
      }
      .side.buy .flash {
        background: var(--green-soft);
      }
      .side.sell .flash {
        background: var(--red-soft);
      }
      .side .flash.go {
        animation: flash 0.5s ease;
      }
      @keyframes flash {
        0% {
          opacity: 1;
        }
        100% {
          opacity: 0;
        }
      }
      .bars {
        margin-top: 18px;
        display: grid;
        gap: 12px;
      }
      .brow {
        display: grid;
        grid-template-columns: 44px 1fr 52px;
        align-items: center;
        gap: 12px;
        font-size: 14px;
      }
      .brow .lbl {
        color: var(--ink3);
      }
      .brow.buy .lbl {
        color: var(--green);
      }
      .brow.sell .lbl {
        color: var(--red);
      }
      .bar {
        height: 12px;
        border-radius: 999px;
        background: rgba(11, 11, 16, 0.07);
        overflow: hidden;
      }
      .bar span {
        display: block;
        height: 100%;
        border-radius: 999px;
        transition: width 0.3s ease;
      }
      .brow.buy .bar span {
        background: #7cc9a0;
      }
      .brow.sell .bar span {
        background: #e79a94;
      }
      .brow .v {
        font-family: var(--mono);
        text-align: right;
      }
      .feed {
        display: flex;
        flex-direction: column;
      }
      .feed table {
        width: 100%;
        border-collapse: collapse;
        font-family: var(--mono);
        font-size: 12.5px;
        margin-top: 10px;
      }
      .feed td {
        padding: 7px 8px;
        white-space: nowrap;
        color: var(--ink3);
      }
      .feed tr.buy td {
        background: var(--green-soft);
      }
      .feed tr.sell td {
        background: var(--red-soft);
      }
      .feed tr.late td {
        background: var(--amber-soft);
      }
      .feed td.a {
        font-weight: 600;
        color: var(--ink);
      }
      .feed tr.buy td.a {
        color: var(--green);
      }
      .feed tr.sell td.a {
        color: var(--red);
      }
      .feed tr.late td.a {
        color: var(--amber);
      }
      .feed tr:first-child td {
        animation: in 0.35s ease;
      }
      @keyframes in {
        from {
          opacity: 0;
          transform: translateY(-4px);
        }
        to {
          opacity: 1;
          transform: none;
        }
      }
    </style>
  </head>
  <body>
    <div class="frame">
      <header>
        <div class="brand"><b>PTQ</b><i>Jev loop</i></div>
        <span class="block">tick <span id="blk">—</span></span>
        <div class="pills">
          <span class="pill live" id="modepill"
            ><span class="dot"></span>paper mode</span
          ><span class="pill" id="symbolpill">—</span
          ><span class="pill blue" id="modelpill">—</span>
        </div>
        <div class="control">
          <span class="pill ctlstate" id="ctlstate">—</span>
          <button class="ctlbtn" id="ctlstart" type="button" disabled>Start</button>
          <button class="ctlbtn" id="ctlstop" type="button" disabled>Stop</button>
        </div>
      </header>
      <div class="ctlnote" id="ctlnote">
        Stop pauses new orders only. Data and this page keep updating, and
        open positions stay open. Closing positions is the KILL switch's job
        (the hard risk limits), which still works while paused.
      </div>
      <div class="stats">
        <span>last <b id="lastms">—</b></span
        ><span>avg <b id="avgms">—</b></span
        ><span><b id="calls">0</b> decisions</span
        ><span>late <b id="late">0</b></span
        ><span class="right">uptime <b id="up">00:00:00</b></span>
      </div>
      <div class="grid">
        <section class="card left">
          <div class="pricebar">
            <div>
              <div class="price" id="px">0.00</div>
              <div class="sub">
                <span id="pos">flat</span
                ><span class="pnl" id="pnl">p&amp;l 0.00 (0.00%)</span
                ><span id="spread">spread — bps</span>
              </div>
            </div>
            <div class="verdict">
              <div class="act buy" id="act">—</div>
              <div class="meta">
                <span id="actms">— ms</span> · <span id="actreason">—</span>
              </div>
            </div>
          </div>
          <div class="snap" id="snap"></div>
          <div class="chart"><svg id="svg"></svg></div>
          <div class="strip" id="strip"></div>
          <div class="foot">
            <span
              >one dot per tick · green buy · red sell · amber late/hold</span
            ><span id="cadence">— s ticks · one decision per tick</span>
          </div>
        </section>
        <div class="rcol">
          <section class="card">
            <div class="eyebrow">Standing order</div>
            <div class="order">
              &gt; quote both sides of the book on Alpaca paper crypto, every
              tick. take a small directional fill when Jev's direction call is
              confident. hold if late. never live.
            </div>
          </section>
          <section class="card side buy" id="side">
            <div class="flash" id="flash"></div>
            <div class="eyebrow">Battery this tick</div>
            <div class="big">
              <span class="word" id="word">—</span
              ><span class="pct" id="wpct"></span>
            </div>
            <div class="bars">
              <div class="brow buy">
                <span class="lbl">env</span>
                <div class="bar"><span id="bb"></span></div>
                <span class="v" id="bv">—</span>
              </div>
              <div class="brow sell">
                <span class="lbl">tox</span>
                <div class="bar"><span id="sb"></span></div>
                <span class="v" id="sv">—</span>
              </div>
            </div>
          </section>
          <section class="card feed">
            <div class="eyebrow">Feed</div>
            <table id="feed"></table>
          </section>
        </div>
      </div>
    </div>
    <script>
      // This dashboard reads the real jev-loop output. It polls latest.json
      // (written by jevloop/loop.py, one entry per tick, last 120 ticks) and
      // renders it with the exact layout used in the video. Nothing here is
      // simulated: if latest.json is empty, the dashboard is honestly empty.
      const $ = (id) => document.getElementById(id);
      const hist = [],
        N = 90,
        svg = $("svg"),
        strip = $("strip"),
        feed = $("feed");
      for (let i = 0; i < N; i++)
        strip.appendChild(document.createElement("i"));
      let lastTick = -1,
        startedAt = null;

      function sideOf(t) {
        if (t.paused || t.late || t.action === "HOLD_LATE") return "late";
        if (t.direction_leg === "up") return "buy";
        if (t.direction_leg === "down") return "sell";
        if (t.action === "PULL_QUOTES" || t.action === "STAND_DOWN")
          return "late";
        return (t.skew || 0) < 0 ? "sell" : "buy"; // quoting with no leg: colour by skew direction
      }

      // Start / Stop. The state lives in ~/.jev-loop/control.json, so it
      // survives a refresh; the loop reads it before every order.
      const ctlToken =
        document.querySelector('meta[name="jev-control-token"]').content;
      const ctlNoteText = $("ctlnote").textContent;
      function showControl(state) {
        const el = $("ctlstate");
        el.textContent = state;
        el.className =
          "pill ctlstate " + (state === "PAUSED" ? "paused" : "running");
        $("ctlstart").disabled = state !== "PAUSED";
        $("ctlstop").disabled = state !== "RUNNING";
      }
      function controlError(msg) {
        const n = $("ctlnote");
        n.className = "ctlnote err";
        n.textContent = msg;
      }
      async function pollControl() {
        try {
          const res = await fetch("control", { cache: "no-store" });
          if (res.ok) showControl((await res.json()).state);
        } catch (e) {
          /* server restarting: keep the last state shown */
        }
        setTimeout(pollControl, 2000);
      }
      async function setControl(state) {
        $("ctlstart").disabled = $("ctlstop").disabled = true;
        try {
          const res = await fetch("control", {
            method: "POST",
            cache: "no-store",
            headers: {
              "Content-Type": "application/json",
              "X-Jev-Token": ctlToken,
            },
            body: JSON.stringify({ state }),
          });
          const body = await res.json();
          if (!res.ok) throw new Error(body.error || res.status);
          const n = $("ctlnote");
          n.className = "ctlnote";
          n.textContent = ctlNoteText;
          showControl(body.state);
        } catch (e) {
          controlError(
            "Could not change state (" + e.message + "). Open this page from jevloop serve at http://127.0.0.1:8765/ and try again.",
          );
          const res = await fetch("control", { cache: "no-store" }).catch(() => null);
          if (res && res.ok) showControl((await res.json()).state);
        }
      }
      $("ctlstart").onclick = () => setControl("RUNNING");
      $("ctlstop").onclick = () => setControl("PAUSED");
      pollControl();

      async function poll() {
        try {
          const res = await fetch("latest.json", { cache: "no-store" });
          const data = await res.json();
          render(data);
        } catch (e) {
          /* dashboard stays on last good frame if the loop is between writes */
        }
        setTimeout(poll, 1000);
      }

      function render(data) {
        const ticks = data.ticks || [];
        if (!ticks.length) return;
        const stats = data.stats || {};
        if (startedAt === null)
          startedAt = Date.now() - (stats.uptime_s || 0) * 1000;

        $("symbolpill").textContent = data.symbol || "—";
        $("modelpill").textContent = stats.model || "—";
        const modePill = $("modepill");
        if ((stats.decision_client || "").toUpperCase() === "MOCK") {
          modePill.className = "pill mock";
          modePill.innerHTML = '<span class="dot"></span>MOCK';
        } else {
          modePill.className = "pill live";
          modePill.innerHTML = '<span class="dot"></span>paper mode';
        }
        $("cadence").textContent =
          (stats.tick_seconds || 2) + "s ticks · one decision per tick";

        const t = ticks[ticks.length - 1];
        if (t.tick === lastTick) {
          drawChart();
          return;
        }
        lastTick = t.tick;

        $("blk").textContent = t.tick.toLocaleString();
        $("px").textContent = t.mid
          ? t.mid.toLocaleString(undefined, { maximumFractionDigits: 1 })
          : "0.00";
        $("lastms").textContent = t.latency_ms
          ? Math.round(t.latency_ms) + " ms"
          : "late";
        $("avgms").textContent = stats.avg_ms
          ? Math.round(stats.avg_ms) + " ms"
          : "—";
        $("calls").textContent = (stats.calls || 0).toLocaleString();
        $("late").textContent = stats.late_count || 0;
        const upS = Math.floor((Date.now() - startedAt) / 1000);
        $("up").textContent = [upS / 3600, (upS % 3600) / 60, upS % 60]
          .map((x) => String(Math.floor(x)).padStart(2, "0"))
          .join(":");

        $("pos").textContent = !t.inventory
          ? "flat"
          : (t.inventory > 0 ? "long " : "short ") + Math.abs(t.inventory);
        const pnlEl = $("pnl");
        const pnl = t.unrealised_pnl_usd || 0;
        pnlEl.textContent = `p&l ${pnl >= 0 ? "+" : ""}${pnl.toFixed(3)} (${((t.drawdown_pct || 0) * 100).toFixed(2)}% dd)`;
        pnlEl.className = "pnl " + (pnl >= 0 ? "pos" : "neg");
        $("spread").textContent =
          "spread " +
          (t.spread_bps != null ? t.spread_bps.toFixed(1) : "—") +
          " bps";

        const side = sideOf(t);
        const a = $("act");
        a.textContent = t.paused
          ? "PAUSED · no new orders"
          : t.action + (t.direction_leg ? ` (${t.direction_leg} leg)` : "");
        a.className = "act " + side;
        $("actms").textContent = t.latency_ms
          ? Math.round(t.latency_ms) + " ms"
          : "late";
        $("actreason").textContent = t.action_reason || "";

        $("snap").innerHTML =
          `<span class=k>route</span><span><b>${t.route || "—"}</b></span>` +
          `<span class=k>regime</span><span><b>${t.regime || "—"} ${t.regime_conf ? Math.round(t.regime_conf * 100) + "%" : ""}</b></span>` +
          `<span class=k>direction</span><span><b>${t.direction || "—"}</b></span>` +
          `<span class=k>toxic</span><span><b>${t.toxic_flow != null ? t.toxic_flow.toFixed(2) : "—"}</b></span>` +
          `<span class=k>liquidity stress</span><span><b>${t.liquidity_stressed != null ? t.liquidity_stressed.toFixed(2) : "—"}</b></span>` +
          `<span class=k>env</span><span><b>${t.quote_environment != null ? t.quote_environment.toFixed(2) : "—"}</b></span>` +
          `<span class=k>inv pressure</span><span><b>${t.inventory_pressure != null ? t.inventory_pressure.toFixed(2) : "—"}</b></span>` +
          `<span class=k>execution health</span><span><b>${t.execution_health != null ? t.execution_health.toFixed(2) : "—"}</b></span>` +
          `<span class=k>vwap</span><span><b>${t.vwap != null ? t.vwap.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—"}</b></span>` +
          `<span class=k>rung</span><span><b>${t.rung || "—"}</b></span>`;

        const sideEl = $("side"),
          word = $("word");
        sideEl.className = "card side " + side;
        const label =
          side === "late"
            ? t.paused
              ? "PAUSED"
              : t.action === "HOLD_LATE"
              ? "LATE"
              : t.action
            : side.toUpperCase();
        if (word.textContent !== label) {
          word.textContent = label;
          word.classList.remove("flip");
          void word.offsetWidth;
          word.classList.add("flip");
          const f = $("flash");
          f.classList.remove("go");
          void f.offsetWidth;
          f.classList.add("go");
        }
        $("wpct").textContent =
          t.quote_environment_conf != null
            ? Math.round(t.quote_environment_conf * 100) + "%"
            : "";
        const envPct =
          t.quote_environment != null
            ? Math.min(100, (t.quote_environment / 3) * 100)
            : 0;
        const toxPct = t.toxic_flow != null ? t.toxic_flow * 100 : 0;
        $("bb").style.width = envPct + "%";
        $("sb").style.width = toxPct + "%";
        $("bv").textContent =
          t.quote_environment != null
            ? t.quote_environment.toFixed(1) + "/3"
            : "—";
        $("sv").textContent =
          t.toxic_flow != null ? t.toxic_flow.toFixed(2) : "—";

        hist.length = 0;
        for (const row of ticks) hist.push({ px: row.mid, side: sideOf(row) });
        const bars = strip.children;
        for (let i = 0; i < N; i++) {
          const h = hist[hist.length - N + i];
          bars[i].className = h ? h.side : "";
        }

        const tr = document.createElement("tr");
        tr.className = side;
        const fill = t.fill_qty
          ? `${t.fill_qty} @ ${t.fill_price ? t.fill_price.toLocaleString(undefined, { maximumFractionDigits: 1 }) : "—"}`
          : "—";
        tr.innerHTML = `<td>${t.tick}</td><td class="a">${label}</td><td>${t.quote_environment_conf != null ? "conf " + t.quote_environment_conf.toFixed(2) : ""}</td><td>${t.latency_ms ? Math.round(t.latency_ms) + "ms" : "late"}</td><td>${fill}</td><td>paper</td>`;
        feed.prepend(tr);
        while (feed.children.length > 16) feed.lastChild.remove();

        drawChart();
      }

      function drawChart() {
        const box = svg.parentElement.getBoundingClientRect(),
          W = Math.max(300, box.width),
          H = Math.max(200, box.height),
          padR = 96,
          padB = 18,
          pts = hist;
        svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
        if (pts.length < 2) return;
        const xs = pts.map((p) => p.px).filter((v) => v != null);
        if (!xs.length) return;
        const lo = Math.min(...xs),
          hi = Math.max(...xs),
          span = Math.max(hi - lo, lo * 0.0001);
        const X = (i) => (i * (W - padR)) / (N - 1),
          Y = (v) => 12 + (H - padB - 24) * (1 - (v - lo) / span),
          off = N - pts.length;
        let d = "";
        pts.forEach((p, i) => {
          if (p.px == null) return;
          const x = X(i + off),
            y = Y(p.px);
          d += d ? ` H${x.toFixed(1)} V${y.toFixed(1)}` : `M${x} ${y}`;
        });
        const last = pts[pts.length - 1],
          lx = X(N - 1),
          ly = Y(last.px),
          col = { buy: "#1f7a4d", sell: "#b91c1c", late: "#b7791f" };
        const grid = [0, 1, 2, 3]
          .map((k) => {
            const v = lo + (span * k) / 3,
              y = Y(v);
            return `<line x1="0" x2="${W - padR}" y1="${y}" y2="${y}" stroke="rgba(11,11,16,.08)" stroke-dasharray="3 4"/><text class="axis" x="${W - padR + 8}" y="${y + 4}">${v.toFixed(1)}</text>`;
          })
          .join("");
        const dots = pts
          .map((p, i) =>
            p.px == null
              ? ""
              : `<circle cx="${X(i + off)}" cy="${Y(p.px)}" r="3.4" fill="${col[p.side] || "#999"}" opacity=".9"/>`,
          )
          .join("");
        svg.innerHTML = `<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="rgba(10,140,255,.16)"/><stop offset="1" stop-color="rgba(10,140,255,0)"/></linearGradient></defs>${grid}<path d="${d} V${H - padB} H${X(off)} Z" fill="url(#g)"/><path d="${d}" fill="none" stroke="#0b0b10" stroke-width="1.6"/>${dots}<line x1="${lx}" x2="${lx}" y1="${ly}" y2="${H - padB}" stroke="rgba(11,11,16,.25)" stroke-dasharray="2 3"/><circle cx="${lx}" cy="${ly}" r="6" fill="${col[last.side] || "#999"}" stroke="#fff" stroke-width="2"/><rect x="${lx + 10}" y="${ly - 12}" rx="11" width="78" height="24" fill="#0b0b10"/><text class="tag" x="${lx + 16}" y="${ly + 4}" fill="#fff">${last.px.toLocaleString(undefined, { maximumFractionDigits: 1 })}</text>`;
      }

      poll();
    </script>
  </body>
</html>
```

Write `~/.claude/skills/jev-loop/dashboard/wall.html`:

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>PTQ × Jev · analysis wall</title>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@500;600&family=Fragment+Mono&display=swap" rel="stylesheet">
<style>
html,body{margin:0;height:100%;background:#0a0a0a;color:#fff;font-family:"Instrument Sans",Helvetica,Arial,sans-serif;overflow:hidden}
.top{position:absolute;left:40px;top:26px;display:flex;align-items:center;gap:18px;z-index:2}
.logo{width:56px;height:56px;border-radius:14px;background:#0a8cff;display:grid;place-items:center;font-weight:600;font-size:22px;letter-spacing:-.02em}
h1{margin:0;font-size:40px;font-weight:600;letter-spacing:-.02em;text-transform:uppercase}
h1 span{color:#5cf07a}
.hud{position:absolute;right:40px;top:34px;font-family:"Fragment Mono",monospace;font-size:14px;color:rgba(255,255,255,.75);text-align:right;line-height:1.7;z-index:2}
.hud b{color:#fff;font-weight:400}
.mockflag{color:#ffd166}
canvas{position:absolute;inset:0;width:100%;height:100%}
</style></head><body>
<div class="top"><div class="logo">P</div><h1>PTQ × Jev: 24/7 <span>HFT</span> loop</h1></div>
<div class="hud">
  <span id="s" style="font-size:32px;font-weight:600;font-family:'Instrument Sans',sans-serif;letter-spacing:-.02em">—</span><br>
  tick <b id="b">—</b><br>
  last <b id="ms">—</b> · seven judgments · one call<br>
  decisions <b id="n">0</b> · <span id="mode">paper mode</span><br>
  <span style="color:#5cf07a">green line = buying</span> · <span style="color:#ff5f5f">red line = selling</span>
</div>
<canvas id="c"></canvas>
<script>
// Reads the real jev-loop output from latest.json. No simulation: every
// point plotted here is a tick the loop actually decided on.
const c=document.getElementById('c'),ctx=c.getContext('2d');let W,H;
function rs(){W=c.width=innerWidth*devicePixelRatio;H=c.height=innerHeight*devicePixelRatio;ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0)}
addEventListener('resize',rs);rs();
const TOP=130,BOT=innerHeight-70,LEFT=40,RIGHT=innerWidth-110;
let lo=null,hi=null,lastTick=-1;
const pts=[],sides=[],marks=[],pulses=[];let bigWord=null,band=null;

function y(p){ if(lo===null||hi===null) return (TOP+BOT)/2; return TOP+(BOT-TOP)*(1-(p-lo)/Math.max(hi-lo,1e-6)); }

function sideOf(t){
  if(t.paused || t.late || t.action==='HOLD_LATE') return 'late';
  if(t.direction_leg==='up') return 'buy';
  if(t.direction_leg==='down') return 'sell';
  if(t.action==='PULL_QUOTES'||t.action==='STAND_DOWN') return 'late';
  return (t.skew||0) < 0 ? 'sell' : 'buy';
}

async function poll(){
  try{
    const res=await fetch('latest.json',{cache:'no-store'});
    const data=await res.json();
    ingest(data);
  }catch(e){}
  setTimeout(poll,1000);
}

function ingest(data){
  const ticks=data.ticks||[];
  if(!ticks.length) return;
  const prices=ticks.map(t=>t.mid).filter(v=>v!=null);
  if(prices.length){ lo=Math.min(...prices); hi=Math.max(...prices); const pad=(hi-lo)*0.1||hi*0.001; lo-=pad; hi+=pad; }

  pts.length=0; sides.length=0;
  for(const t of ticks){ pts.push(t.mid); sides.push(sideOf(t)); }

  const t=ticks[ticks.length-1];
  if(t.tick===lastTick) return;
  lastTick=t.tick;

  const side=sideOf(t);
  const conf = t.quote_environment_conf!=null? t.quote_environment_conf : (t.regime_conf||0.5);
  document.getElementById('s').textContent=(side==='late'?(t.paused?'PAUSED':(t.action||'HOLD')):side.toUpperCase())+' '+Math.round(conf*100)+'%';
  document.getElementById('s').style.color= side==='buy'?'#5cf07a':side==='sell'?'#ff5f5f':'#ffd166';
  document.getElementById('b').textContent=t.tick.toLocaleString();
  document.getElementById('ms').textContent=t.latency_ms? Math.round(t.latency_ms)+' ms':'late';
  document.getElementById('n').textContent=(data.stats&&data.stats.calls||0).toLocaleString();
  const modeEl=document.getElementById('mode');
  const isMock=(data.stats&&(data.stats.decision_client||'').toUpperCase()==='MOCK');
  modeEl.textContent = isMock? 'MOCK DECISION CLIENT · paper mode' : 'paper mode';
  modeEl.className = isMock? 'mockflag' : '';

  band={side,a:1};
  bigWord={side,conf,a:1};
  pulses.push({side,conf,a:1});
}

function draw(){
  ctx.fillStyle='#0a0a0a';ctx.fillRect(0,0,innerWidth,innerHeight);
  if(band){band.a-=.035;if(band.a>0){ctx.fillStyle=(band.side==='buy'?'rgba(92,240,122,':band.side==='sell'?'rgba(255,80,80,':'rgba(255,209,102,')+(band.a*.22)+')';ctx.fillRect(RIGHT-140,TOP,140,BOT-TOP)}}
  ctx.strokeStyle='rgba(255,255,255,.07)';ctx.setLineDash([2,6]);ctx.lineWidth=1;
  if(lo!==null){
    for(let k=0;k<=4;k++){const v=lo+(hi-lo)*k/4,yy=y(v);ctx.beginPath();ctx.moveTo(LEFT,yy);ctx.lineTo(RIGHT,yy);ctx.stroke();ctx.fillStyle='rgba(255,255,255,.6)';ctx.font='12px "Fragment Mono",monospace';ctx.fillText(v.toFixed(1),RIGHT+14,yy+4)}
  }
  ctx.setLineDash([]);

  if(pts.length>1){
    const N=pts.length,stepX=(RIGHT-LEFT)/Math.max(1,Math.min(N,120)-1),start=Math.max(0,N-120);
    ctx.lineWidth=2.2;
    for(let i=start+1;i<N;i++){
      if(pts[i]==null||pts[i-1]==null) continue;
      const x0=LEFT+(i-1-start)*stepX,x1=LEFT+(i-start)*stepX;
      ctx.strokeStyle=sides[i]==='buy'?'#5cf07a':sides[i]==='sell'?'#ff5f5f':'rgba(255,255,255,.85)';
      ctx.beginPath();ctx.moveTo(x0,y(pts[i-1]));ctx.lineTo(x1,y(pts[i-1]));ctx.lineTo(x1,y(pts[i]));ctx.stroke();
    }
    const lastPx=pts[N-1];
    if(lastPx!=null){
      const lx=RIGHT,ly=y(lastPx);
      ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(lx,ly,5,0,7);ctx.fill();
      ctx.fillStyle='#0a8cff';ctx.fillRect(lx+8,ly-11,84,22);
      ctx.fillStyle='#fff';ctx.font='12px "Fragment Mono",monospace';ctx.fillText(lastPx.toFixed(1),lx+14,ly+4);
    }
  }

  if(bigWord){bigWord.a-=.02;if(bigWord.a>0){
    ctx.globalAlpha=Math.min(1,bigWord.a*1.4);
    ctx.fillStyle=bigWord.side==='buy'?'#5cf07a':bigWord.side==='sell'?'#ff5f5f':'#ffd166';
    ctx.font='600 100px "Instrument Sans",sans-serif';ctx.textAlign='right';
    ctx.fillText(bigWord.side.toUpperCase(),RIGHT-30,TOP+150+(1-bigWord.a)*-20);
    ctx.font='26px "Fragment Mono",monospace';ctx.fillText('conf '+Math.round(bigWord.conf*100)+'%',RIGHT-34,TOP+186);
    ctx.textAlign='left';ctx.globalAlpha=1;
  }}

  for(const q of pulses){q.a-=.012;}
  while(pulses.length&&pulses[0].a<=0)pulses.shift();
  for(const q of pulses){
    if(q.a<=0)continue;
    const yy = lo!==null && pts.length ? y(pts[pts.length-1]) : (TOP+BOT)/2;
    ctx.globalAlpha=q.a*.9;ctx.strokeStyle=q.side==='buy'?'#5cf07a':q.side==='sell'?'#ff5f5f':'#ffd166';ctx.lineWidth=2.5;
    ctx.beginPath();ctx.arc(RIGHT,yy,8+(1-q.a)*44,0,7);ctx.stroke();ctx.globalAlpha=1;
  }

  const now=new Date();ctx.fillStyle='rgba(255,255,255,.55)';ctx.font='11px "Fragment Mono",monospace';
  for(let i=0;i<9;i++){const x=LEFT+i*(RIGHT-LEFT)/8;const d=new Date(now-(8-i)*4000);ctx.fillText(d.toTimeString().slice(0,8),x-28,BOT+24)}
  requestAnimationFrame(draw);
}
poll();draw();
</script></body></html>
```

Write `~/.claude/skills/jev-loop/tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture(autouse=True)
def _isolated_jev_home(tmp_path, monkeypatch):
    """Every test gets its own ~/.jev-loop, so a PAUSED left on the real
    dashboard can never change a test result (and tests never touch it)."""
    from jevloop import loop, serve

    home = tmp_path / "jev-home"
    home.mkdir()
    monkeypatch.setattr(loop, "LOG_DIR", home)
    monkeypatch.setattr(loop, "LOG_FILE", home / "log.jsonl")
    monkeypatch.setattr(loop, "LATEST_FILE", home / "latest.json")
    monkeypatch.setattr(serve, "LOG_DIR", home)
    return home
```

Write `~/.claude/skills/jev-loop/tests/test_assets.py`:

```python
import pytest

from jevloop.assets import UnknownSymbolError, resolve_symbol, size_order


def test_resolves_known_crypto_pairs():
    for sym in ("BTC/USD", "ETH/USD", "SOL/USD"):
        spec = resolve_symbol(sym)
        assert spec.asset_class == "crypto"
        assert spec.is_24_7 is True
        assert spec.has_depth is True
        assert spec.min_notional_usd == 10.0


def test_resolves_known_equity_tickers():
    for sym in ("AAPL", "SPY", "TSLA", "NVDA"):
        spec = resolve_symbol(sym)
        assert spec.asset_class == "us_equity"
        assert spec.is_24_7 is False
        assert spec.has_depth is False


def test_resolution_is_case_insensitive():
    assert resolve_symbol("btc/usd").symbol == "BTC/USD"
    assert resolve_symbol("aapl").symbol == "AAPL"


def test_unknown_symbol_raises_with_a_helpful_message():
    with pytest.raises(UnknownSymbolError) as exc_info:
        resolve_symbol("not a real symbol!!")
    assert "BTC/USD" in str(exc_info.value)
    assert "AAPL" in str(exc_info.value)


def test_equity_has_no_orderbook_url():
    spec = resolve_symbol("AAPL")
    assert spec.orderbook_url is None


def test_crypto_has_an_orderbook_url():
    spec = resolve_symbol("BTC/USD")
    assert spec.orderbook_url is not None


# -- size_order: never below the venue minimum --------------------------


def test_size_order_meets_crypto_minimum_at_high_price():
    spec = resolve_symbol("BTC/USD")
    qty = size_order(notional_usd=20.0, price=85_000.0, spec=spec)
    assert qty * 85_000.0 >= spec.min_notional_usd


def test_size_order_meets_crypto_minimum_at_low_target():
    # A tiny requested notional must still clear the venue floor -- this is
    # exactly the bug a fixed quantity had: 0.0002 BTC cleared $10 most of
    # the time, but nothing enforced it when price moved.
    spec = resolve_symbol("BTC/USD")
    qty = size_order(notional_usd=0.01, price=85_000.0, spec=spec)
    assert qty * 85_000.0 >= spec.min_notional_usd


def test_size_order_meets_equity_minimum():
    spec = resolve_symbol("AAPL")
    qty = size_order(notional_usd=0.10, price=337.0, spec=spec)
    assert qty * 337.0 >= spec.min_notional_usd


def test_size_order_respects_precision():
    spec = resolve_symbol("AAPL")
    qty = size_order(notional_usd=50.0, price=337.03, spec=spec)
    # qty_precision is 4 for equities
    assert round(qty, spec.qty_precision) == qty


def test_size_order_rejects_non_positive_price():
    spec = resolve_symbol("BTC/USD")
    with pytest.raises(ValueError):
        size_order(notional_usd=20.0, price=0.0, spec=spec)
```

Write `~/.claude/skills/jev-loop/tests/test_split.py`:

```python
import pytest

from jevloop.battery import build_questions
from jevloop.split import (
    ALLOWED_QUESTIONS,
    SplitViolation,
    assert_split_respected,
    render_split_table,
)


def test_the_real_battery_respects_the_split():
    # build_questions() already calls assert_split_respected internally;
    # calling it here too pins the behaviour independently of that wiring.
    assert_split_respected(build_questions())


def test_every_allowed_question_is_a_judgment_not_a_calculation():
    for qid, (_qtype, description) in ALLOWED_QUESTIONS.items():
        assert "calculate" not in description.lower()
        assert "compute" not in description.lower()


def test_unknown_question_id_is_rejected():
    with pytest.raises(SplitViolation):
        assert_split_respected(
            {"a_new_thing": {"type": "noul", "instructions": "is this ok"}}
        )


def test_arithmetic_instructions_are_rejected_even_on_an_allowed_id():
    with pytest.raises(SplitViolation):
        assert_split_respected(
            {
                "regime": {
                    "type": "choice",
                    "instructions": "Please calculate the regime.",
                    "criteria": {},
                }
            }
        )


def test_vwap_request_is_rejected():
    with pytest.raises(SplitViolation):
        assert_split_respected(
            {
                "quote_environment": {
                    "type": "score",
                    "instructions": "What is the VWAP right now?",
                    "criteria": [],
                }
            }
        )


def test_structured_instructions_are_also_scanned():
    # instructions can be a dict with the question in one field and data in
    # others (see the API docs); the scanner must look inside it too.
    with pytest.raises(SplitViolation):
        assert_split_respected(
            {
                "toxic_flow": {
                    "type": "noul",
                    "instructions": {
                        "data": {"mid": 100},
                        "question": "Compute the exact value of the spread.",
                    },
                }
            }
        )


def test_legitimate_judgment_passes():
    assert_split_respected(
        {
            "toxic_flow": {
                "type": "noul",
                "instructions": "Is the aggressive flow informed rather than noise?",
            }
        }
    )


def test_render_split_table_names_both_sides():
    table = render_split_table()
    assert "DETERMINISTIC" in table
    assert "PROBABILISTIC" in table
    assert "state.py" in table
    assert "battery.py" in table
```

Write `~/.claude/skills/jev-loop/tests/test_policy.py`:

```python
from jevloop.limits import Limits
from jevloop.policy import (
    KILL,
    PULL_QUOTES,
    QUOTE_BOTH_SIDES,
    QUOTE_WIDE,
    STAND_DOWN,
    WIDEN,
    compose_action,
    fallback_action,
    inventory_skew,
)

L = Limits()

BASE_SNAPSHOT = dict(
    drawdown_pct=0.01,
    inventory=0.0,
    daily_loss_usd=0.0,
    position_age_s=0.0,
    data_age_s=0.1,
    leverage=1.0,
    spread_bps=4.0,
    imbalance=0.0,
)

BASE_ANSWERS = {
    "toxic_flow": {"noul": 0.2},
    "liquidity_stressed": {"noul": 0.1},
    "quote_environment": {"score": 2.3, "confidence": 0.84},
    "inventory_pressure": {"score": 1.1},
    "direction": {"choice": "neutral", "confidence": 0.9},
}


def test_kill_on_drawdown_breach():
    snap = dict(BASE_SNAPSHOT, drawdown_pct=0.2)
    action = compose_action(BASE_ANSWERS, snap, L)
    assert action.kind == KILL


def test_pull_quotes_on_toxic_flow():
    answers = dict(BASE_ANSWERS, toxic_flow={"noul": 0.75})
    action = compose_action(answers, BASE_SNAPSHOT, L)
    assert action.kind == PULL_QUOTES


def test_widen_on_liquidity_stress():
    answers = dict(BASE_ANSWERS, liquidity_stressed={"noul": 0.85})
    action = compose_action(answers, BASE_SNAPSHOT, L)
    assert action.kind == WIDEN


def test_quote_both_sides_matches_article_example():
    # env 2.3, confidence 0.84 -- the article's own worked example.
    action = compose_action(BASE_ANSWERS, BASE_SNAPSHOT, L)
    assert action.kind == QUOTE_BOTH_SIDES


def test_quote_wide_below_full_confidence():
    answers = dict(BASE_ANSWERS, quote_environment={"score": 2.3, "confidence": 0.5})
    action = compose_action(answers, BASE_SNAPSHOT, L)
    assert action.kind == QUOTE_WIDE


def test_stand_down_below_quoting_floor():
    answers = dict(BASE_ANSWERS, quote_environment={"score": 0.5, "confidence": 0.9})
    action = compose_action(answers, BASE_SNAPSHOT, L)
    assert action.kind == STAND_DOWN


def test_directional_leg_only_when_confident_and_quoting():
    answers = dict(BASE_ANSWERS, direction={"choice": "up", "confidence": 0.9})
    action = compose_action(answers, BASE_SNAPSHOT, L)
    assert action.kind == QUOTE_BOTH_SIDES
    assert action.direction_leg == "up"

    low_conf = dict(BASE_ANSWERS, direction={"choice": "up", "confidence": 0.1})
    action2 = compose_action(low_conf, BASE_SNAPSHOT, L)
    assert action2.direction_leg is None


def test_directional_leg_never_fires_on_pull_or_widen():
    answers = dict(
        BASE_ANSWERS,
        toxic_flow={"noul": 0.9},
        direction={"choice": "up", "confidence": 0.99},
    )
    action = compose_action(answers, BASE_SNAPSHOT, L)
    assert action.kind == PULL_QUOTES
    assert action.direction_leg is None


def test_inventory_skew_direction():
    # Long inventory should skew toward selling (negative).
    assert inventory_skew(3.0, 3.0, inventory=0.01) < 0
    # Short inventory should skew toward buying (positive).
    assert inventory_skew(3.0, 3.0, inventory=-0.01) > 0
    # Flat inventory: no skew regardless of pressure.
    assert inventory_skew(3.0, 3.0, inventory=0.0) == 0.0


def test_fallback_action_never_touches_jev():
    # Confirms fallback_action's signature takes no `answers` argument at all --
    # a structural guarantee that the rules-only rung cannot call the model.
    import inspect

    sig = inspect.signature(fallback_action)
    assert "answers" not in sig.parameters

    action = fallback_action(BASE_SNAPSHOT, L)
    assert action.kind in (KILL, STAND_DOWN, WIDEN, QUOTE_WIDE)
```

Write `~/.claude/skills/jev-loop/tests/test_risk.py`:

```python
from jevloop.limits import Limits
from jevloop.risk import check

L = Limits()

OK_SNAPSHOT = dict(
    drawdown_pct=0.01,
    inventory=0.0005,
    mid=40_000.0,  # position value = 0.0005 * 40,000 = $20, under max_position_usd (50.0)
    daily_loss_usd=1.0,
    position_age_s=10.0,
    data_age_s=0.2,
    leverage=1.0,
)


def test_ok_case_passes():
    v = check(
        OK_SNAPSHOT,
        order_notional_usd=20.0,
        limits=L,
        api_error_streak=0,
        decision_latency_ms=90.0,
    )
    assert v.ok
    assert v.veto is None
    assert not v.kill


def test_drawdown_kills():
    snap = dict(OK_SNAPSHOT, drawdown_pct=0.5)
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and v.kill


def test_max_position_kills():
    # inventory * mid must exceed max_position_usd (50.0 by default)
    snap = dict(OK_SNAPSHOT, inventory=1.0, mid=85_000.0)
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and v.kill


def test_max_position_scales_with_price_not_just_quantity():
    # Same tiny quantity, but a high enough price still breaches the dollar cap.
    snap = dict(OK_SNAPSHOT, inventory=0.01, mid=10_000.0)  # $100 position
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and v.kill


def test_max_daily_loss_kills():
    snap = dict(OK_SNAPSHOT, daily_loss_usd=999.0)
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and v.kill


def test_order_notional_vetoes_without_kill():
    v = check(
        OK_SNAPSHOT,
        order_notional_usd=10_000.0,
        limits=L,
        api_error_streak=0,
        decision_latency_ms=90.0,
    )
    assert not v.ok and not v.kill


def test_inventory_age_vetoes_without_kill():
    snap = dict(OK_SNAPSHOT, position_age_s=99999.0)
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and not v.kill


def test_stale_data_vetoes():
    snap = dict(OK_SNAPSHOT, data_age_s=999.0)
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and not v.kill


def test_api_error_streak_kills():
    v = check(OK_SNAPSHOT, 20.0, L, api_error_streak=99, decision_latency_ms=90.0)
    assert not v.ok and v.kill


def test_decision_latency_vetoes_without_kill():
    v = check(OK_SNAPSHOT, 20.0, L, api_error_streak=0, decision_latency_ms=99999.0)
    assert not v.ok and not v.kill


def test_leverage_kills():
    snap = dict(OK_SNAPSHOT, leverage=5.0)
    v = check(snap, 20.0, L, 0, 90.0)
    assert not v.ok and v.kill


def test_risk_never_reads_jev_answers():
    """Structural guarantee: check() takes a snapshot, not a battery answer dict."""
    import inspect

    sig = inspect.signature(check)
    assert "answers" not in sig.parameters
```

Write `~/.claude/skills/jev-loop/tests/test_ladder.py`:

```python
from jevloop.ladder import Rung, select_rung


def test_kill_wins_over_everything():
    r = select_rung(
        risk_kill=True,
        decision_late=True,
        jev_down=True,
        decision_confidence=0.99,
        low_confidence_threshold=0.5,
    )
    assert r == Rung.KILL


def test_late_beats_jev_down_and_confidence():
    r = select_rung(
        risk_kill=False,
        decision_late=True,
        jev_down=True,
        decision_confidence=0.99,
        low_confidence_threshold=0.5,
    )
    assert r == Rung.HOLD_LATE


def test_jev_down_routes_to_rules_only():
    r = select_rung(
        risk_kill=False,
        decision_late=False,
        jev_down=True,
        decision_confidence=None,
        low_confidence_threshold=0.5,
    )
    assert r == Rung.RULES_ONLY


def test_low_confidence_reduces():
    r = select_rung(
        risk_kill=False,
        decision_late=False,
        jev_down=False,
        decision_confidence=0.2,
        low_confidence_threshold=0.5,
    )
    assert r == Rung.REDUCE


def test_healthy_high_confidence_runs():
    r = select_rung(
        risk_kill=False,
        decision_late=False,
        jev_down=False,
        decision_confidence=0.9,
        low_confidence_threshold=0.5,
    )
    assert r == Rung.RUN


def test_degraded_execution_health_reduces_even_with_high_confidence():
    r = select_rung(
        risk_kill=False,
        decision_late=False,
        jev_down=False,
        decision_confidence=0.9,
        low_confidence_threshold=0.5,
        execution_health_score=0.4,  # "Degraded" zone (Broken=0 .. Optimal=3)
    )
    assert r == Rung.REDUCE


def test_healthy_execution_and_confidence_runs():
    r = select_rung(
        risk_kill=False,
        decision_late=False,
        jev_down=False,
        decision_confidence=0.9,
        low_confidence_threshold=0.5,
        execution_health_score=2.7,  # "Optimal" zone
    )
    assert r == Rung.RUN


def test_execution_health_never_overrides_kill_or_late():
    r = select_rung(
        risk_kill=True,
        decision_late=False,
        jev_down=False,
        decision_confidence=0.9,
        low_confidence_threshold=0.5,
        execution_health_score=3.0,
    )
    assert r == Rung.KILL
```

Write `~/.claude/skills/jev-loop/tests/test_state.py`:

```python
import time

from jevloop.state import InventoryState, approx_token_count, build_snapshot


def _snapshot(now):
    inv = InventoryState(
        inventory=0.001,
        entry_price=99.5,
        position_opened_at=now - 30,
        equity_usd=1000.0,
        high_water_mark_usd=1000.0,
        fills=3,
        orders_submitted=4,
        recent_latencies_ms=[80, 90, 75],
    )
    prices = [(now - i, 100 + (i % 5)) for i in range(0, 120)]
    sides = [(now - i, "buy" if i % 2 == 0 else "sell") for i in range(0, 40)]
    return build_snapshot(
        as_of=now,
        mid=100.2,
        microprice=100.21,
        spread_bps=3.4,
        bid_depth=[(100.1, 0.5), (100.0, 0.4), (99.9, 0.3)],
        ask_depth=[(100.3, 0.4), (100.4, 0.3), (100.5, 0.2)],
        trade_prices=prices,
        trade_sides=sides,
        inv=inv,
        data_timestamp=now - 0.5,
    )


def test_snapshot_has_all_required_field_groups():
    now = time.time()
    snap = _snapshot(now)
    for key in [
        "mid",
        "microprice",
        "return_1m",
        "return_5m",
        "return_30m",
        "spread_bps",
        "bid_depth_3",
        "ask_depth_3",
        "imbalance",
        "aggressive_buy_ratio",
        "trade_intensity_per_s",
        "realised_vol_short",
        "realised_vol_medium",
        "inventory",
        "unrealised_pnl_usd",
        "daily_loss_usd",
        "drawdown_pct",
        "position_age_s",
        "fill_ratio",
        "reject_count",
        "last_10_latencies_ms",
        "data_age_s",
    ]:
        assert key in snap, f"missing field {key}"


def test_snapshot_stays_under_roughly_400_tokens():
    now = time.time()
    snap = _snapshot(now)
    assert approx_token_count(snap) < 400


def test_timestamp_discipline_ignores_future_data():
    now = time.time()
    inv = InventoryState(equity_usd=1000.0, high_water_mark_usd=1000.0)
    # A price point stamped in the future must never affect a return calc.
    prices = [(now - 70, 100.0), (now - 10, 105.0), (now + 1000, 999999.0)]
    snap = build_snapshot(
        as_of=now,
        mid=100.0,
        microprice=100.0,
        spread_bps=3.0,
        bid_depth=[(99.9, 1)],
        ask_depth=[(100.1, 1)],
        trade_prices=prices,
        trade_sides=[(now - 10, "buy")],
        inv=inv,
        data_timestamp=now,
    )
    assert snap["return_1m"] is not None
    assert snap["return_1m"] < 100


def test_top3_depth_used_for_imbalance():
    now = time.time()
    inv = InventoryState(equity_usd=1000.0, high_water_mark_usd=1000.0)
    snap = build_snapshot(
        as_of=now,
        mid=100.0,
        microprice=100.0,
        spread_bps=3.0,
        bid_depth=[(99.9, 10), (99.8, 10), (99.7, 10)],
        ask_depth=[(100.1, 1), (100.2, 1), (100.3, 1)],
        trade_prices=[(now, 100.0)],
        trade_sides=[(now, "buy")],
        inv=inv,
        data_timestamp=now,
    )
    assert snap["imbalance"] > 0.5  # much more bid depth than ask depth
```

Write `~/.claude/skills/jev-loop/tests/test_mock_client.py`:

```python
from jevloop.battery import build_questions, validate_answers
from jevloop.client import MockDecisionClient


def test_mock_answers_validate_against_battery_schema():
    client = MockDecisionClient(seed=42)
    state = {"imbalance": 0.2, "inventory": 0.0005}
    questions = build_questions()
    answers, meta = client.ask(state, questions, timeout=2.0)
    validate_answers(answers)
    assert meta["model"].startswith("mock-")
    assert meta["route"] == "MOCK"


def test_mock_is_persistent_not_pure_noise():
    """Two consecutive calls on the same client shouldn't be uncorrelated --
    the regime/direction latent should move gradually, not teleport."""
    client = MockDecisionClient(seed=7)
    state = {"imbalance": 0.0, "inventory": 0.0}
    a1, _ = client.ask(state, build_questions(), timeout=2.0)
    a2, _ = client.ask(state, build_questions(), timeout=2.0)
    p1 = a1["regime"]["probabilities"]
    p2 = a2["regime"]["probabilities"]
    # The leading option's probability shouldn't swing by more than ~0.9
    # between consecutive ticks -- a loose bound that only catches "pure
    # random every tick" behaviour, not normal drift.
    top_option = max(p1, key=p1.get)
    assert abs(p1[top_option] - p2[top_option]) < 0.9


def test_mock_never_claims_to_be_real():
    client = MockDecisionClient()
    assert "mock" in client.model.lower()
    assert client.name == "MOCK"


def test_mock_choice_answers_have_confidence_and_probabilities():
    client = MockDecisionClient(seed=1)
    answers, _ = client.ask({"imbalance": 0.1}, build_questions(), timeout=2.0)
    for key in ("regime", "direction"):
        assert "confidence" in answers[key]
        assert abs(sum(answers[key]["probabilities"].values()) - 1.0) < 1e-3


def test_mock_score_answers_have_legend():
    client = MockDecisionClient(seed=1)
    answers, _ = client.ask({"inventory": 0.002}, build_questions(), timeout=2.0)
    for key in ("quote_environment", "inventory_pressure"):
        assert set(answers[key]["legend"].keys()) == {"0", "1", "2", "3"}
```

Write `~/.claude/skills/jev-loop/tests/test_throttle.py`:

```python
"""The loop must stay under the Vercel AI Gateway's ~20-30 requests a minute."""
from unittest import mock

import pytest

from jevloop import client as jc
from jevloop.client import JevThrottle, RateLimited

SNAP = {"mid": 100.0, "spread_bps": 5.0, "inventory": 0.0}
ANS = {"regime": {"choice": "trending"}}


def _throttle():
    return JevThrottle(min_interval_s=4.0, min_gap_s=3.0, move_bps=15.0, max_age_s=60.0)


def test_calls_at_most_once_per_interval_on_a_500ms_loop():
    t = _throttle()
    calls = 0
    for i in range(120):  # one minute of 500 ms ticks, state unchanged
        now = i * 0.5
        if t.due(SNAP, now):
            t.called(now)
            t.success(ANS, {"latency_ms": 90}, SNAP, now)
            calls += 1
    assert calls == 15  # one every 4 s


def test_material_change_calls_early_but_never_under_the_gap():
    t = _throttle()
    t.called(0.0)
    t.success(ANS, {}, SNAP, 0.0)
    moved = dict(SNAP, mid=101.0)  # 100 bps
    assert t.due(moved, 1.0) is None  # under min_gap_s
    assert t.due(moved, 3.0) == "price moved"
    assert t.due(SNAP, 3.0) is None  # no change, interval not up


def test_rate_limit_backs_off_exponentially_and_keeps_the_last_judgment():
    t = _throttle()
    t.called(0.0)
    t.success(ANS, {"latency_ms": 90}, SNAP, 0.0)
    w1 = t.rate_limited(4.0)
    assert t.due(SNAP, 4.0 + w1 - 0.01) is None
    w2 = t.rate_limited(4.0 + w1)
    assert w2 > w1
    answers, meta = t.last(10.0)
    assert answers == ANS and meta["reused"] is True


def test_old_judgment_is_not_reused():
    t = _throttle()
    t.success(ANS, {}, SNAP, 0.0)
    assert t.last(61.0) is None


@pytest.mark.parametrize("status,text", [(429, ""), (400, "access frequency is too high")])
def test_rate_limit_responses_raise_without_retrying(status, text):
    resp = mock.Mock(status_code=status, text=text)
    with mock.patch.object(jc.requests, "post", return_value=resp) as post:
        with pytest.raises(RateLimited):
            jc._post_with_retry("https://x", {}, {}, timeout=2.0)
    assert post.call_count == 1  # retrying a rate limit only adds requests
```

Write `~/.claude/skills/jev-loop/tests/test_alpaca_guard.py`:

```python
import pytest

from jevloop.assets import resolve_symbol
from jevloop.execution.alpaca import (
    PAPER_TRADING_BASE_URL,
    AlpacaConfigError,
    AlpacaPaperClient,
    MarketClosedError,
    assert_paper_url,
)

BTC_SPEC = resolve_symbol("BTC/USD")


def test_paper_url_passes():
    assert_paper_url(PAPER_TRADING_BASE_URL)
    assert_paper_url(PAPER_TRADING_BASE_URL + "/")  # trailing slash tolerated


def test_live_url_is_refused():
    with pytest.raises(AlpacaConfigError):
        assert_paper_url("https://api.alpaca.markets")


def test_client_construction_refuses_live_base_url():
    with pytest.raises(AlpacaConfigError):
        AlpacaPaperClient(
            api_key="x",
            secret_key="y",
            spec=BTC_SPEC,
            base_url="https://api.alpaca.markets",
        )


def test_client_construction_accepts_paper_base_url():
    client = AlpacaPaperClient(api_key="x", secret_key="y", spec=BTC_SPEC)
    assert client.base_url == PAPER_TRADING_BASE_URL


def test_client_construction_works_for_equity_spec():
    equity_spec = resolve_symbol("AAPL")
    client = AlpacaPaperClient(api_key="x", secret_key="y", spec=equity_spec)
    assert client.symbol == "AAPL"
    assert client.spec.asset_class == "us_equity"


# -- closed-market guard: never place an equity order while the market is shut --


def test_limit_order_refused_when_equity_market_closed():
    equity_spec = resolve_symbol("AAPL")
    client = AlpacaPaperClient(api_key="x", secret_key="y", spec=equity_spec)
    client.is_market_open = lambda: False  # no network: force the closed branch
    with pytest.raises(MarketClosedError):
        client.submit_limit_order("buy", 1.0, 100.0)


def test_market_order_refused_when_equity_market_closed():
    equity_spec = resolve_symbol("AAPL")
    client = AlpacaPaperClient(api_key="x", secret_key="y", spec=equity_spec)
    client.is_market_open = lambda: False
    with pytest.raises(MarketClosedError):
        client.submit_market_order("sell", 1.0)


def test_crypto_never_checks_market_hours():
    # is_24_7 short-circuits the check entirely; is_market_open should not
    # even be consulted for a crypto spec. No network: _request is stubbed.
    crypto_client = AlpacaPaperClient(api_key="x", secret_key="y", spec=BTC_SPEC)

    def _boom():
        raise AssertionError("is_market_open should never be called for a 24/7 asset")

    crypto_client.is_market_open = _boom
    crypto_client._request = lambda method, url, **kwargs: {"id": "fake-order"}

    result = crypto_client.submit_limit_order("buy", 0.001, 100.0)
    assert result == {"id": "fake-order"}
```

Write `~/.claude/skills/jev-loop/tests/test_live_gate.py`:

```python
import pytest

from jevloop.assets import resolve_symbol
from jevloop.execution.alpaca import (
    LIVE_ALLOW_ENV_VALUE,
    LIVE_ALLOW_ENV_VAR,
    LIVE_CONFIRMATION_PHRASE,
    LIVE_TRADING_BASE_URL,
    PAPER_TRADING_BASE_URL,
    AlpacaConfigError,
    AlpacaPaperClient,
    LiveTradingRefused,
    client_from_env,
    resolve_trading_base_url,
)

BTC_SPEC = resolve_symbol("BTC/USD")


# -- resolve_trading_base_url(): the pure gate logic, no I/O -----------------


def test_paper_is_the_default_regardless_of_env_or_confirmation():
    # live=False must always win, even if the other two gates happen to be
    # set correctly -- paper stays the default everywhere unless --live is
    # explicitly passed.
    assert (
        resolve_trading_base_url(
            live=False,
            allow_live_env=LIVE_ALLOW_ENV_VALUE,
            confirmation=LIVE_CONFIRMATION_PHRASE,
        )
        == PAPER_TRADING_BASE_URL
    )
    assert (
        resolve_trading_base_url(live=False, allow_live_env=None, confirmation=None)
        == PAPER_TRADING_BASE_URL
    )


def test_live_refused_when_env_var_missing():
    with pytest.raises(LiveTradingRefused):
        resolve_trading_base_url(
            live=True, allow_live_env=None, confirmation=LIVE_CONFIRMATION_PHRASE
        )


def test_live_refused_when_env_var_wrong_value():
    with pytest.raises(LiveTradingRefused):
        resolve_trading_base_url(
            live=True, allow_live_env="yes", confirmation=LIVE_CONFIRMATION_PHRASE
        )


def test_live_refused_when_confirmation_missing():
    with pytest.raises(LiveTradingRefused):
        resolve_trading_base_url(
            live=True, allow_live_env=LIVE_ALLOW_ENV_VALUE, confirmation=None
        )


def test_live_refused_when_confirmation_does_not_match_exactly():
    with pytest.raises(LiveTradingRefused):
        resolve_trading_base_url(
            live=True,
            allow_live_env=LIVE_ALLOW_ENV_VALUE,
            confirmation="i understand this trades real money",  # wrong case/text
        )


def test_live_refused_when_flag_missing_even_with_the_other_two_set():
    # live=False short-circuits before either gate is even inspected.
    assert (
        resolve_trading_base_url(
            live=False,
            allow_live_env=LIVE_ALLOW_ENV_VALUE,
            confirmation=LIVE_CONFIRMATION_PHRASE,
        )
        == PAPER_TRADING_BASE_URL
    )


def test_live_routes_to_live_base_url_when_all_three_gates_pass():
    assert (
        resolve_trading_base_url(
            live=True,
            allow_live_env=LIVE_ALLOW_ENV_VALUE,
            confirmation=LIVE_CONFIRMATION_PHRASE,
        )
        == LIVE_TRADING_BASE_URL
    )


# -- AlpacaPaperClient: cannot reach the live URL except through the gate ---


def test_direct_construction_against_live_url_is_refused():
    with pytest.raises(AlpacaConfigError):
        AlpacaPaperClient(
            api_key="x", secret_key="y", spec=BTC_SPEC, base_url=LIVE_TRADING_BASE_URL
        )


def test_construction_against_live_url_succeeds_only_with_gate_flag():
    client = AlpacaPaperClient(
        api_key="x",
        secret_key="y",
        spec=BTC_SPEC,
        base_url=LIVE_TRADING_BASE_URL,
        _live_gate_passed=True,
    )
    assert client.base_url == LIVE_TRADING_BASE_URL
    assert client.is_live is True


# -- client_from_env(): the real call site every command in the CLI uses ---


def test_client_from_env_defaults_to_paper(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "x")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "y")
    monkeypatch.delenv(LIVE_ALLOW_ENV_VAR, raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    client = client_from_env(symbol="BTC/USD")
    assert client.base_url == PAPER_TRADING_BASE_URL
    assert client.is_live is False


def test_client_from_env_live_flag_alone_is_refused(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "x")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "y")
    monkeypatch.delenv(LIVE_ALLOW_ENV_VAR, raising=False)
    with pytest.raises(LiveTradingRefused):
        client_from_env(
            symbol="BTC/USD", live=True, confirmation=LIVE_CONFIRMATION_PHRASE
        )


def test_client_from_env_env_var_alone_is_refused(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "x")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "y")
    monkeypatch.setenv(LIVE_ALLOW_ENV_VAR, LIVE_ALLOW_ENV_VALUE)
    with pytest.raises(LiveTradingRefused):
        client_from_env(symbol="BTC/USD", live=True, confirmation=None)


def test_client_from_env_confirmation_alone_is_refused(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "x")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "y")
    monkeypatch.delenv(LIVE_ALLOW_ENV_VAR, raising=False)
    with pytest.raises(LiveTradingRefused):
        client_from_env(
            symbol="BTC/USD", live=True, confirmation=LIVE_CONFIRMATION_PHRASE
        )


def test_client_from_env_routes_to_live_when_all_three_present(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "x")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "y")
    monkeypatch.setenv(LIVE_ALLOW_ENV_VAR, LIVE_ALLOW_ENV_VALUE)
    client = client_from_env(
        symbol="BTC/USD", live=True, confirmation=LIVE_CONFIRMATION_PHRASE
    )
    assert client.base_url == LIVE_TRADING_BASE_URL
    assert client.is_live is True


def test_client_from_env_ignores_live_env_var_when_live_flag_not_passed(monkeypatch):
    # Even with the env var correctly set, omitting --live (live=False, the
    # CLI default) must still produce a paper client. Paper is the default
    # everywhere unless a caller explicitly opts in with --live.
    monkeypatch.setenv("ALPACA_API_KEY", "x")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "y")
    monkeypatch.setenv(LIVE_ALLOW_ENV_VAR, LIVE_ALLOW_ENV_VALUE)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    client = client_from_env(
        symbol="BTC/USD", live=False, confirmation=LIVE_CONFIRMATION_PHRASE
    )
    assert client.base_url == PAPER_TRADING_BASE_URL
    assert client.is_live is False
```

Write `~/.claude/skills/jev-loop/tests/test_continuous_mode.py`:

```python
import pytest

from jevloop.loop import _StopRequested, _handle_sigterm, main


def test_sigterm_handler_raises_stop_requested():
    with pytest.raises(_StopRequested):
        _handle_sigterm(signum=15, frame=None)


def test_ticks_zero_and_forever_both_mean_run_forever(monkeypatch):
    # main() maps --ticks 0 and --forever to ticks=None (run forever) before
    # ever calling run(); intercept run() itself so no network/loop executes.
    calls = []

    def fake_run(**kwargs):
        calls.append(kwargs)
        return 0

    monkeypatch.setattr("jevloop.loop.run", fake_run)

    main(["--ticks", "0", "--symbol", "BTC/USD"])
    assert calls[-1]["ticks"] is None

    main(["--forever", "--symbol", "BTC/USD"])
    assert calls[-1]["ticks"] is None


def test_explicit_ticks_count_is_preserved(monkeypatch):
    calls = []
    monkeypatch.setattr("jevloop.loop.run", lambda **kwargs: calls.append(kwargs) or 0)
    main(["--ticks", "30", "--symbol", "BTC/USD"])
    assert calls[-1]["ticks"] == 30
    assert calls[-1]["live"] is False
```

Write `~/.claude/skills/jev-loop/tests/test_member_fixes.py`:

```python
"""Regression tests for the bugs members reported on the published prompt:
the Windows latest.json lock crash, fake price history, VWAP double
counting, a drawdown switch that could never fire, KILL not selling,
assumed fills, account-wide cancels, the calibration proxy, and mock
decisions placing orders."""

import json
import os
import time

import pytest

from jevloop import calibrate, loop, serve
from jevloop.assets import resolve_symbol
from jevloop.execution.alpaca import AlpacaAPIError, AlpacaPaperClient
from jevloop.state import InventoryState, apply_fill, build_snapshot, update_vwap

# -- 1. Windows: swapping latest.json while the dashboard reads it -----------


def test_atomic_write_retries_through_a_windows_style_lock(tmp_path, monkeypatch):
    target = tmp_path / "latest.json"
    target.write_text('{"old": true}')
    real_replace = os.replace
    calls = {"n": 0}

    def locked_twice(src, dst):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise PermissionError(13, "The process cannot access the file")
        return real_replace(src, dst)

    monkeypatch.setattr(loop.os, "replace", locked_twice)
    assert loop._atomic_write(target, '{"new": true}') is True
    assert calls["n"] == 3
    assert json.loads(target.read_text()) == {"new": True}
    assert not list(tmp_path.glob("*.tmp"))


def test_atomic_write_skips_a_refresh_instead_of_crashing(tmp_path, monkeypatch):
    target = tmp_path / "latest.json"
    target.write_text('{"old": true}')

    def always_locked(src, dst):
        raise PermissionError(13, "locked")

    monkeypatch.setattr(loop.os, "replace", always_locked)
    assert loop._atomic_write(target, '{"new": true}', first_wait_s=0.001) is False
    assert json.loads(target.read_text()) == {"old": True}  # old copy intact
    assert not list(tmp_path.glob("*.tmp"))


def test_reader_tolerates_lock_and_partial_file(tmp_path, monkeypatch):
    feed = tmp_path / "latest.json"
    feed.write_text('{"ticks": [1]}')
    assert json.loads(serve.read_feed(feed)) == {"ticks": [1]}

    feed.write_text('{"ticks": [1, 2')  # caught mid-write
    assert json.loads(serve.read_feed(feed, wait_s=0.001)) == {"ticks": [1]}

    real = type(feed).read_bytes
    calls = {"n": 0}

    def locked_once(self):
        calls["n"] += 1
        if calls["n"] == 1:
            raise PermissionError(13, "locked")
        return real(self)

    feed.write_text('{"ticks": [1, 2]}')
    monkeypatch.setattr(type(feed), "read_bytes", locked_once)
    assert json.loads(serve.read_feed(feed, wait_s=0.001)) == {"ticks": [1, 2]}


# -- 2. real price history, real timestamps, VWAP once -----------------------


def _snap(prices, inv=None, now=None, mid=100.0):
    now = now or time.time()
    return build_snapshot(
        as_of=now,
        mid=mid,
        microprice=mid,
        spread_bps=1.0,
        bid_depth=[(99.9, 1)],
        ask_depth=[(100.1, 1)],
        trade_prices=prices,
        trade_sides=[(now - 1, "buy")],
        inv=inv or InventoryState(equity_usd=1000.0, high_water_mark_usd=1000.0),
        data_timestamp=now,
    )


def test_moving_prices_give_nonzero_returns_and_vol():
    now = time.time()
    # 31 one-minute points that actually move
    prices = [(now - 60 * k, 100 + (k % 3) - 0.05 * k) for k in range(31, 0, -1)]
    prices.append((now, 101.0))
    snap = _snap(prices, now=now)
    for key in (
        "return_1m",
        "return_5m",
        "return_30m",
        "realised_vol_short",
        "realised_vol_medium",
    ):
        assert snap[key] not in (None, 0.0), key


def test_flat_history_is_zero_and_missing_history_is_none():
    now = time.time()
    assert _snap([(now, 100.0)], now=now)["return_1m"] is None
    assert _snap([(now, 100.0)], now=now)["realised_vol_short"] is None


def test_parse_ts_keeps_real_venue_time():
    ts = loop._parse_ts("2026-09-24T21:44:30.980346366Z")
    assert abs(ts - 1790286270.980346) < 1e-3


def test_vwap_counts_each_trade_once_across_overlapping_fetches():
    inv = InventoryState()
    batch = [(1.0, 100.0, 1.0), (2.0, 102.0, 1.0)]
    update_vwap(inv, batch)
    update_vwap(inv, batch)  # same trades seen again next tick
    update_vwap(inv, batch + [(3.0, 110.0, 2.0)])
    assert inv.vwap_cum_vol == 4.0
    assert inv.vwap_cum_pv == 100 + 102 + 220


# -- 3. drawdown switch can fire ---------------------------------------------


def test_drawdown_is_measured_against_real_equity():
    inv = InventoryState(equity_usd=1000.0, high_water_mark_usd=1000.0)
    apply_fill(inv, "buy", 1.0, 1000.0, time.time())
    snap = _snap([(time.time(), 900.0)], inv=inv, mid=900.0)
    assert snap["unrealised_pnl_usd"] == -100.0
    assert snap["drawdown_pct"] == pytest.approx(0.10)


def test_apply_fill_realises_pnl():
    inv = InventoryState()
    apply_fill(inv, "buy", 2.0, 100.0, 0)
    apply_fill(inv, "sell", 1.0, 110.0, 1)
    assert inv.inventory == 1.0 and inv.realised_pnl_usd == 10.0
    apply_fill(inv, "sell", 1.0, 90.0, 2)
    assert inv.inventory == 0.0 and inv.realised_pnl_usd == 0.0


# -- 4-6. fills from the broker, own orders only, KILL flattens -------------


class FakeAlpaca:
    """Stands in for AlpacaPaperClient's order endpoints."""

    order_prefix = "jevloop-test-"

    def __init__(self, held=0.0):
        self._order_seq = 0
        self.orders = []
        self.cancelled = []
        self.held = held
        self.foreign_order = {
            "id": "other",
            "client_order_id": "someone-else",
            "status": "new",
        }

    def submit_market_order(self, side, qty):
        self._order_seq += 1
        o = {
            "id": f"o{self._order_seq}",
            "client_order_id": f"{self.order_prefix}{self._order_seq}",
            "side": side,
            "status": "filled",
            "filled_qty": str(qty),
            "filled_avg_price": "100.5",
        }
        self.orders.append(o)
        self.held += qty if side == "buy" else -qty
        return o

    def get_own_orders(self, after_iso):
        return [
            o for o in self.orders if o["client_order_id"].startswith(self.order_prefix)
        ]

    def cancel_own_orders(self):
        mine = [o for o in self.orders if o["status"] == "new"]
        self.cancelled += [o["id"] for o in mine]
        return len(mine)

    def get_position_qty(self):
        return self.held


def test_fills_are_read_back_not_assumed():
    alp = FakeAlpaca()
    inv = InventoryState()
    alp.submit_market_order("buy", 0.5)
    assert inv.inventory == 0.0  # nothing assumed on submit
    seen = {}
    fills, pending = loop.reconcile_fills(alp, inv, seen, {}, "x", time.time())
    assert fills == [("buy", 0.5, 100.5)] and inv.inventory == 0.5 and not pending
    fills, _ = loop.reconcile_fills(alp, inv, seen, {}, "x", time.time())
    assert fills == [] and inv.inventory == 0.5  # never counted twice


def test_kill_sends_a_real_closing_order_and_never_sells_more_than_held():
    alp = FakeAlpaca()
    inv = InventoryState()
    alp.submit_market_order("buy", 0.5)
    seen = {}
    loop.reconcile_fills(alp, inv, seen, {}, "x", time.time())
    alp.held = 0.3  # the account holds less than the bot thinks
    txt = loop._flatten(
        alp, resolve_symbol("BTC/USD"), inv, False, seen, {}, "x", time.time()
    )
    closing = alp.orders[-1]
    assert closing["side"] == "sell" and float(closing["filled_qty"]) == 0.3
    assert "market sell 0.3" in txt


def test_kill_is_dry_in_dry_mode():
    alp = FakeAlpaca()
    txt = loop._flatten(
        alp,
        resolve_symbol("BTC/USD"),
        InventoryState(inventory=1.0),
        True,
        {},
        {},
        "x",
        0,
    )
    assert txt.startswith("dry:") and alp.orders == []


def test_cancel_never_hits_the_account_wide_endpoint(monkeypatch):
    client = AlpacaPaperClient(
        api_key="x", secret_key="y", spec=resolve_symbol("BTC/USD")
    )
    assert not hasattr(client, "cancel_all_orders")
    calls = []

    def fake_request(method, url, **kw):
        calls.append((method, url))
        if method == "GET":
            return [
                {"id": "a", "client_order_id": client.order_prefix + "1"},
                {"id": "b", "client_order_id": "manual-order"},
            ]
        return {}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.cancel_own_orders() == 1
    deletes = [u for m, u in calls if m == "DELETE"]
    assert deletes == [f"{client.base_url}/v2/orders/a"]


def test_orders_carry_this_runs_client_order_id(monkeypatch):
    client = AlpacaPaperClient(
        api_key="x", secret_key="y", spec=resolve_symbol("BTC/USD")
    )
    bodies = []
    monkeypatch.setattr(
        client, "_request", lambda m, u, **kw: bodies.append(kw["json"]) or kw["json"]
    )
    client.submit_limit_order("buy", 0.001, 100.0)
    client.submit_market_order("sell", 0.001)
    assert all(b["client_order_id"].startswith(client.order_prefix) for b in bodies)


# -- 7. calibration uses the direction confidence ---------------------------


def test_calibration_scores_direction_confidence_not_quote_env():
    ticks = [
        {
            "direction": "up",
            "direction_conf": 0.9,
            "quote_environment_conf": 0.1,
            "mid": 100,
        },
        {
            "direction": "down",
            "direction_conf": 0.6,
            "quote_environment_conf": 0.9,
            "mid": 101,
        },
        {"direction": "neutral", "direction_conf": 0.8, "mid": 102},
        {"direction": None, "mid": 99},
    ]
    pairs = calibrate.pair_predictions(ticks, horizon=1)
    # up at 100 -> 101: right. down at 101 -> 102: wrong. neutral: not scored.
    assert pairs == [(0.9, 1), (0.6, 0)]


def test_calibration_skips_old_logs_without_direction_conf():
    ticks = [
        {"direction": "up", "quote_environment_conf": 0.9, "mid": 100},
        {"mid": 101},
    ]
    assert calibrate.pair_predictions(ticks, horizon=1) == []


# -- Alpaca crypto is spot, long only: SELL closes the long, never shorts ----


def _sell_signal(monkeypatch, alp, inv, dry=False):
    from jevloop import risk
    from jevloop.limits import Limits
    from jevloop.policy import QUOTE_BOTH_SIDES, Action

    monkeypatch.setattr(risk, "check", lambda *a, **k: risk.RiskVerdict(ok=True))
    return loop._execute_action(
        alpaca=alp,
        spec=resolve_symbol("BTC/USD"),
        action=Action(QUOTE_BOTH_SIDES, "test", skew=-0.5, direction_leg="down"),
        bid_px=100.0,
        ask_px=101.0,
        mid=100.5,
        quote_notional=10.0,
        directional_notional=10.0,
        snapshot={},
        limits=Limits(),
        inv=inv,
        api_error_streak=0,
        decision_latency_ms=100.0,
        resting_quotes={"bid": 100.0, "ask": 101.0},  # no re-quote this tick
        rest_counter=0,
        now=time.time(),
        dry=dry,
        expected_px={},
    )


def test_sell_when_flat_does_nothing(monkeypatch):
    alp = FakeAlpaca()
    for dry in (False, True):
        _, fill_txt, *_ = _sell_signal(monkeypatch, alp, InventoryState(), dry=dry)
        assert "no position to close" in fill_txt
    assert alp.orders == []  # no order, so no short


def test_sell_when_long_closes_the_long_and_no_more(monkeypatch):
    alp = FakeAlpaca()
    inv = InventoryState()
    alp.submit_market_order("buy", 0.0005)
    loop.reconcile_fills(alp, inv, {}, {}, "x", time.time())
    alp.held = 0.0003  # the account holds less than this run thinks
    _, fill_txt, *_ = _sell_signal(monkeypatch, alp, inv)
    closing = alp.orders[-1]
    assert closing["side"] == "sell" and float(closing["filled_qty"]) == 0.0003
    assert "closing long" in fill_txt and alp.held == 0.0  # flat, never short
```

Write `~/.claude/skills/jev-loop/tests/test_run_fixes.py`:

```python
"""Regression tests for the second round of member-reported bugs: buys
piling up past the position cap, a spread fixed in dollars, a stuck
position freezing the loop, orders left open after a run, fees not
tracked, closing sells rounded up, and a network timeout crashing the
loop."""

import time

import pytest
import requests

from jevloop import loop
from jevloop.assets import resolve_symbol
from jevloop.execution.alpaca import AlpacaAPIError, AlpacaPaperClient
from jevloop.limits import Limits
from jevloop.policy import QUOTE_BOTH_SIDES, Action
from jevloop.pricing import quote_prices
from jevloop.risk import check
from jevloop.state import InventoryState, apply_fill


class _Broker:
    order_prefix = "jevloop-test-"

    def __init__(self, held=0.0):
        self._order_seq = 0
        self.sent, self.cancels, self.held = [], 0, held

    def submit_limit_order(self, side, qty, px):
        self._order_seq += 1
        self.sent.append(("limit", side, qty))
        return {"client_order_id": f"t-{self._order_seq}"}

    def submit_market_order(self, side, qty):
        self._order_seq += 1
        self.sent.append(("market", side, qty))
        return {"client_order_id": f"t-{self._order_seq}"}

    def cancel_own_orders(self):
        self.cancels += 1
        return 0

    def get_position_qty(self):
        return self.held


def _snap(**kw):
    base = dict(
        drawdown_pct=0.0, inventory=0.0, mid=100.0, daily_loss_usd=0.0,
        position_age_s=0.0, data_age_s=0.1,
    )
    base.update(kw)
    return base


def _execute(broker, inv, snapshot, *, resting=None, leg=None, pending=0.0, mid=100.0):
    return loop._execute_action(
        alpaca=broker,
        spec=resolve_symbol("ETH/USD"),
        action=Action(QUOTE_BOTH_SIDES, "test", skew=0.0, direction_leg=leg),
        bid_px=mid * 0.999,
        ask_px=mid * 1.001,
        mid=mid,
        quote_notional=20.0,
        directional_notional=20.0,
        snapshot=snapshot,
        limits=Limits(),
        inv=inv,
        api_error_streak=0,
        decision_latency_ms=100.0,
        resting_quotes=resting,
        rest_counter=0,
        now=time.time(),
        expected_px={},
        pending_buy_usd=pending,
    )


# -- 1. buys counted against the $50 cap before they fill -------------------


def test_bid_and_buy_leg_stop_at_the_cap():
    b = _Broker(held=0.3)  # $30 held at $100, $20 of room
    inv = InventoryState(inventory=0.3)
    _, fill_txt, *_ = _execute(b, inv, _snap(inventory=0.3), leg="up")
    buys = [s for s in b.sent if s[1] == "buy"]
    assert len(buys) == 1  # the $20 bid fits, the $20 leg on top does not
    assert "buy leg skipped" in fill_txt


def test_working_buys_block_a_new_buy_leg():
    b = _Broker()
    inv = InventoryState()
    # a $40 bid still working at the broker, no rest-cycle this tick
    _, fill_txt, *_ = _execute(b, inv, _snap(), resting={"bid": 1, "ask": 2}, leg="up", pending=40.0)
    assert not [s for s in b.sent if s[1] == "buy"]
    assert "buy leg skipped" in fill_txt


def test_reconcile_reports_working_buy_dollars():
    class A:
        def get_own_orders(self, after):
            return [
                {"id": "1", "client_order_id": "c1", "side": "buy", "status": "new",
                 "qty": "0.2", "filled_qty": "0", "limit_price": "100"},
                {"id": "2", "client_order_id": "c2", "side": "sell", "status": "new",
                 "qty": "0.2", "filled_qty": "0", "limit_price": "101"},
            ]
    ob = {}
    _, pending = loop.reconcile_fills(A(), InventoryState(), {}, {}, "x", 0, open_buys=ob)
    assert pending and ob["usd"] == pytest.approx(20.0)


# -- 2. spread in bps, the same on BTC and a $30 stock ----------------------


def test_spread_is_proportional_to_price():
    L = Limits()
    kw = dict(inventory_frac=0.0, sigma=0.0005, gamma=L.as_gamma, kappa=L.as_kappa,
              horizon_s=L.as_horizon_s)
    b1, a1 = quote_prices(mid=85_000.0, **kw)
    b2, a2 = quote_prices(mid=30.0, **kw)
    bps1 = (a1 - b1) / 85_000.0 * 1e4
    bps2 = (a2 - b2) / 30.0 * 1e4
    assert bps1 == pytest.approx(bps2)
    assert 2 <= bps1 <= 100


def test_long_inventory_skews_quotes_down():
    L = Limits()
    kw = dict(mid=100.0, sigma=0.001, gamma=L.as_gamma, kappa=L.as_kappa, horizon_s=60.0)
    b0, a0 = quote_prices(inventory_frac=0.0, **kw)
    b1, a1 = quote_prices(inventory_frac=1.0, **kw)
    assert b1 < b0 and a1 < a0


# -- 3. a stuck position is closed, not frozen ------------------------------


def test_aged_inventory_closes_instead_of_freezing():
    b = _Broker(held=0.3)
    inv = InventoryState(inventory=0.3)
    line, fill_txt, *_ = _execute(b, inv, _snap(inventory=0.3, position_age_s=99999.0))
    assert line.startswith("EXIT")
    assert b.sent == [("market", "sell", 0.3)]


def test_closing_orders_pass_the_age_veto_but_not_the_kill_limits():
    L = Limits()
    assert check(_snap(inventory=0.3, position_age_s=99999.0), 30.0, L, 0, 90.0, closing=True).ok
    v = check(_snap(inventory=0.3, drawdown_pct=0.5), 30.0, L, 0, 90.0, closing=True)
    assert not v.ok and v.kill


# -- 4. every way out cancels this run's resting orders ---------------------


def test_cancel_runs_on_every_way_out():
    import inspect

    src = inspect.getsource(loop.run)
    finally_block = src.rsplit("finally:", 1)[1]
    assert "cancel_own_orders()" in finally_block
    handler = src.split("except (KeyboardInterrupt, _StopRequested):")[1].split("finally:")[0]
    assert "cancel_own_orders" not in handler  # not only on Ctrl+C any more


# -- 5. fees taken in coin are tracked --------------------------------------


def test_fee_in_coin_shrinks_inventory_and_books_the_cost():
    inv = InventoryState()
    apply_fill(inv, "buy", 0.001, 100_000.0, 0)
    fee = loop.sync_fees(inv, run_held=0.0009975, price=100_000.0)
    assert inv.inventory == pytest.approx(0.0009975)
    assert fee == pytest.approx(0.25) and inv.fees_usd == pytest.approx(0.25)
    assert inv.realised_pnl_usd == pytest.approx(-0.25)


def test_no_fee_when_broker_matches():
    inv = InventoryState()
    apply_fill(inv, "buy", 0.001, 100_000.0, 0)
    assert loop.sync_fees(inv, run_held=0.001, price=100_000.0) == 0.0


# -- 6. closing sells round down --------------------------------------------


def test_closing_quantity_rounds_down():
    spec = resolve_symbol("BTC/USD")
    step = 10 ** -spec.qty_precision
    held = 3 * step - step / 3  # just under three steps
    assert loop._floor_qty(held, spec) <= held


# -- 7. a network timeout is an API error, not a crash ----------------------


def test_timeout_becomes_an_api_error(monkeypatch):
    client = AlpacaPaperClient(api_key="x", secret_key="y", spec=resolve_symbol("BTC/USD"))

    def timeout(*a, **k):
        raise requests.exceptions.ReadTimeout("read timed out")

    monkeypatch.setattr(requests, "request", timeout)
    with pytest.raises(AlpacaAPIError) as e:
        client.get_account()
    assert e.value.status_code == 0 and "network error" in str(e.value)
```

Write `~/.claude/skills/jev-loop/tests/test_bar_mode.py`:

```python
"""--bar: one decision per bar close (e.g. 30-minute bars) instead of every 2 s block."""

from jevloop import loop
from jevloop.limits import Limits


def test_bar_close_is_utc_aligned_with_a_short_settle():
    base = 1800.0 * 1_000_000  # a :00 or :30 boundary
    assert loop._seconds_to_bar_close(base + 100, 1800) == 1800 - 100 + loop.BAR_SETTLE_S
    assert loop._seconds_to_bar_close(base + 1, 1800) == 1.0  # still inside the settle
    assert loop._seconds_to_bar_close(base + loop.BAR_SETTLE_S, 1800) == 1800


def test_cli_bar_30m_passes_1800_seconds_and_default_is_off(monkeypatch):
    calls = []
    monkeypatch.setattr("jevloop.loop.run", lambda **kw: calls.append(kw) or 0)
    loop.main(["--bar", "30m", "--symbol", "PAXG/USD", "--ticks", "3"])
    assert calls[-1]["bar_seconds"] == 1800.0 and calls[-1]["symbol"] == "PAXG/USD"
    loop.main(["--ticks", "3"])
    assert calls[-1]["bar_seconds"] is None


class _FakeAlpaca:
    def __init__(self):
        self.bar_fetches = 0

    def get_account(self):
        return {"equity": "1000"}

    def get_orderbook(self):
        return {"b": [{"p": 4250.0, "s": 1.0}], "a": [{"p": 4260.0, "s": 1.0}]}

    def get_recent_trades(self, start_iso):
        return []

    def get_minute_bars(self, start_iso):
        self.bar_fetches += 1
        import time as _t
        from datetime import datetime, timezone

        now = _t.time()
        return [
            {"t": datetime.fromtimestamp(now - 60 * (40 - i) - 60, timezone.utc).isoformat(), "c": 4200.0 + i}
            for i in range(40)
        ]

    def cancel_own_orders(self):
        return []

    def get_own_orders(self, after_iso):
        return []

    def get_position_qty(self):
        return 0.0


def test_bar_mode_waits_for_each_close_and_refreshes_minute_bars(tmp_path, monkeypatch):
    monkeypatch.setattr(loop, "LOG_DIR", tmp_path)
    monkeypatch.setattr(loop, "LOG_FILE", tmp_path / "log.jsonl")
    monkeypatch.setattr(loop, "LATEST_FILE", tmp_path / "latest.json")
    alp = _FakeAlpaca()
    monkeypatch.setattr(loop, "client_from_env", lambda **kw: alp)
    sleeps, closes = [], []
    monkeypatch.setattr(loop.time, "sleep", lambda s: sleeps.append(s))
    real_close = loop._seconds_to_bar_close
    monkeypatch.setattr(loop, "_seconds_to_bar_close", lambda *a: closes.append(real_close(*a)) or closes[-1])
    rc = loop.run(symbol="PAXG/USD", ticks=2, mock=True, limits=Limits(), bar_seconds=1800.0)
    assert rc == 0
    assert len(closes) == 2 and all(c in sleeps for c in closes)  # slept to each close
    assert all(s <= 1800 + loop.BAR_SETTLE_S for s in sleeps)  # no 2 s cadence on top
    assert alp.bar_fetches == 3  # startup backfill + one refresh per bar close
    lines = (tmp_path / "log.jsonl").read_text().splitlines()
    assert len(lines) == 2
```

Write `~/.claude/skills/jev-loop/tests/test_control.py`:

```python
"""Start / Stop from the dashboard: a pause blocks every new order, Start
resumes, and the control endpoint only takes a POST carrying this install's
token, addressed to 127.0.0.1, with no CORS."""

import http.client
import json
import threading
import time

import pytest

from jevloop import control, loop, serve
from jevloop.assets import resolve_symbol
from jevloop.limits import Limits
from jevloop.policy import QUOTE_BOTH_SIDES, Action
from jevloop.state import InventoryState


class _Broker:
    _order_seq = 0

    def __init__(self, held=0.0):
        self.sent, self.cancels, self.held = [], 0, held

    def submit_limit_order(self, side, qty, px):
        self.sent.append(("limit", side, qty))
        return {"client_order_id": f"t-{len(self.sent)}"}

    def submit_market_order(self, side, qty):
        self.sent.append(("market", side, qty))
        return {"client_order_id": f"t-{len(self.sent)}"}

    def cancel_own_orders(self):
        self.cancels += 1
        return 0

    def get_position_qty(self):
        return self.held


def _tick(monkeypatch, broker, leg, inv=None, resting=None):
    from jevloop import risk

    monkeypatch.setattr(risk, "check", lambda *a, **k: risk.RiskVerdict(ok=True))
    return loop._execute_action(
        alpaca=broker,
        spec=resolve_symbol("BTC/USD"),
        action=Action(QUOTE_BOTH_SIDES, "test", skew=0.5, direction_leg=leg),
        bid_px=100.0,
        ask_px=101.0,
        mid=100.5,
        quote_notional=20.0,
        directional_notional=20.0,
        snapshot={},
        limits=Limits(),
        inv=inv or InventoryState(),
        api_error_streak=0,
        decision_latency_ms=100.0,
        resting_quotes=resting,
        rest_counter=0,
        now=time.time(),
        dry=False,
        expected_px={},
    )


def test_no_control_file_means_running(_isolated_jev_home):
    assert control.read_state(_isolated_jev_home) == control.RUNNING


def test_pause_blocks_every_new_order_and_pulls_resting_quotes(monkeypatch, _isolated_jev_home):
    control.write_state(_isolated_jev_home, control.PAUSED)
    inv = InventoryState(inventory=0.5)
    for leg in ("up", "down", None):
        b = _Broker(held=0.5)
        line, fill, *_rest = _tick(monkeypatch, b, leg, inv=inv, resting={"bid": 1, "ask": 2})
        assert b.sent == []  # no quote, no buy leg, no sell leg
        assert line.startswith("PAUSED") and b.cancels == 1  # resting quotes pulled
        assert _rest[-2] is None  # nothing left marked as resting
    assert inv.inventory == 0.5  # the position is untouched: Stop is not KILL


def test_resume_places_orders_again(monkeypatch, _isolated_jev_home):
    control.write_state(_isolated_jev_home, control.PAUSED)
    b = _Broker()
    _tick(monkeypatch, b, "up")
    assert b.sent == []
    control.write_state(_isolated_jev_home, control.RUNNING)
    line, *_ = _tick(monkeypatch, b, "up")
    assert not line.startswith("PAUSED")
    assert ("limit", "buy", pytest.approx(b.sent[0][2])) in b.sent and ("market", "buy", pytest.approx(b.sent[-1][2])) in b.sent


def test_pause_survives_and_a_bad_file_fails_safe(_isolated_jev_home):
    control.write_state(_isolated_jev_home, control.PAUSED)
    assert control.read_state(_isolated_jev_home) == control.PAUSED  # a fresh read, like a refresh
    (_isolated_jev_home / "control.json").write_text("{half a fi")
    assert control.is_paused(_isolated_jev_home)  # unreadable: don't trade


def test_cli_pause_and_resume(monkeypatch, _isolated_jev_home):
    from jevloop import __main__ as cli

    monkeypatch.setattr("sys.argv", ["jevloop", "pause"])
    assert cli.main() == 0 and control.is_paused(_isolated_jev_home)
    monkeypatch.setattr("sys.argv", ["jevloop", "resume"])
    assert cli.main() == 0 and not control.is_paused(_isolated_jev_home)


def test_token_is_per_install_and_stable(_isolated_jev_home, tmp_path):
    t1 = control.load_or_create_token(_isolated_jev_home)
    assert len(t1) >= 32 and control.load_or_create_token(_isolated_jev_home) == t1
    assert control.load_or_create_token(tmp_path / "other") != t1


# -- the HTTP endpoint -------------------------------------------------------


@pytest.fixture
def server(_isolated_jev_home):
    import socketserver

    httpd = socketserver.TCPServer(("127.0.0.1", 0), serve.Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield httpd.server_address[1], control.load_or_create_token(_isolated_jev_home)
    httpd.shutdown()
    httpd.server_close()


def _req(port, method, path, body=None, headers=None):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    h = {"Host": f"127.0.0.1:{port}"}
    h.update(headers or {})
    c.request(method, path, body=json.dumps(body) if body is not None else None, headers=h)
    r = c.getresponse()
    out = (r.status, dict(r.getheaders()), r.read())
    c.close()
    return out


def test_post_needs_the_token(server, _isolated_jev_home):
    port, token = server
    for hdrs in ({}, {"X-Jev-Token": "wrong"}, {"X-Jev-Token": token[:-1]}):
        status, _, _ = _req(port, "POST", "/control", {"state": "PAUSED"}, hdrs)
        assert status == 403
    assert not control.is_paused(_isolated_jev_home)
    status, h, body = _req(port, "POST", "/control", {"state": "PAUSED"}, {"X-Jev-Token": token})
    assert status == 200 and json.loads(body) == {"state": "PAUSED"}
    assert control.is_paused(_isolated_jev_home)
    assert not any(k.lower().startswith("access-control") for k in h)  # no CORS
    status, _, body = _req(port, "GET", "/control")
    assert status == 200 and json.loads(body)["state"] == "PAUSED"
    status, _, _ = _req(port, "POST", "/control", {"state": "RUNNING"}, {"X-Jev-Token": token})
    assert status == 200 and not control.is_paused(_isolated_jev_home)


def test_other_sites_are_refused(server, _isolated_jev_home):
    port, token = server
    good = {"X-Jev-Token": token}
    # a page on another site, even with the token somehow in hand
    assert _req(port, "POST", "/control", {"state": "PAUSED"}, {**good, "Origin": "https://evil.example"})[0] == 403
    # DNS rebinding: another name pointed at 127.0.0.1
    assert _req(port, "POST", "/control", {"state": "PAUSED"}, {**good, "Host": f"evil.example:{port}"})[0] == 403
    assert _req(port, "GET", "/", headers={"Host": f"evil.example:{port}"})[0] == 403
    # no CORS preflight is answered, and GET can't change anything
    status, h, _ = _req(port, "OPTIONS", "/control", headers={"Origin": "https://evil.example"})
    assert status >= 400 and not any(k.lower().startswith("access-control") for k in h)
    assert _req(port, "GET", "/control?state=PAUSED")[0] == 200
    assert _req(port, "POST", "/control", {"state": "KILL"}, good)[0] == 400
    assert not control.is_paused(_isolated_jev_home)


def test_dashboard_page_carries_the_token_and_the_buttons(server):
    port, token = server
    status, _, body = _req(port, "GET", "/")
    page = body.decode()
    assert status == 200 and token in page and "__JEV_CONTROL_TOKEN__" not in page
    assert 'id="ctlstart"' in page and 'id="ctlstop"' in page and "KILL" in page


def test_server_binds_loopback_only():
    import inspect

    src = inspect.getsource(serve.main)
    assert 'TCPServer(("127.0.0.1"' in src and "0.0.0.0" not in src
```



### 2.3: Pin Python and create the virtual environment

```bash
cd ~/.claude/skills/jev-loop
uv python install 3.12
uv venv --python 3.12 .venv
```

These three lines are the same on Windows (PowerShell and Git Bash both accept `cd ~/.claude/skills/jev-loop`; in cmd use `cd /d "%USERPROFILE%\.claude\skills\jev-loop"`). The venv lands in `.venv\Scripts` on Windows and `.venv/bin` on Mac / Linux. You don't need to activate it; `uv run` uses it.

Verify:
```bash
cd ~/.claude/skills/jev-loop && uv run python --version
```
Expect `Python 3.12.x`. If `uv python install 3.12` fails (rare, Astral's mirror briefly unreachable), retry once after 60 seconds. If it still fails, surface the exact `uv` stderr and ask the user to retry the prompt.

---

## Phase 3: Installation and self-test

### 3.1: Install dependencies

```bash
cd ~/.claude/skills/jev-loop
uv pip install -e ".[dev]"
```

This installs `requests`, `python-dotenv`, and `pytest`. If it fails, surface the exact `uv` stderr and stop, the common cause is no network. The idempotency in Phase 1.2 makes a re-run safe.

### 3.2: Run the test suite

```bash
cd ~/.claude/skills/jev-loop
uv run pytest -q
```

Expect all tests to pass (115 at the time this prompt was written; more may exist if this file has been updated since). These tests need no network and no keys, they cover the policy thresholds, the risk vetoes, the fallback ladder, the state snapshot's maths and token budget, the asset resolver, the notional order-sizing floor, the closed-market guard, the split guard, the mock decision client's shape, the Alpaca paper-URL guard, the three-gate live-trading check, and the fixes for bugs members reported (the Windows file lock on latest.json, real price history, VWAP counted once, drawdown against real equity, fills read back from Alpaca, KILL sending a real closing order, cancelling only this run's orders, calibration on the direction confidence, mock runs never ordering, a SELL closing the long and never opening a short, and `--bar` deciding once per bar close), and the dashboard's Start / Stop (a pause blocks every new order, Start resumes, and the control endpoint refuses anything without this install's token). If anything fails, surface the failure and stop; do not continue to Phase 4 with a broken scaffold.

### 3.3: Create the working `.env`

```bash
cp ~/.claude/skills/jev-loop/.env.example ~/.claude/skills/jev-loop/.env
```

Windows PowerShell: `Copy-Item "$HOME\.claude\skills\jev-loop\.env.example" "$HOME\.claude\skills\jev-loop\.env"`. Git Bash runs the `cp` line as written.

Print: `Created ~/.claude/skills/jev-loop/.env from the template. I'll open it for you at each step below.`

---

## Phase 4: Alpaca paper key (required)

The loop cannot run without a working Alpaca **paper** key. This is not optional: it is the only execution venue this install ever touches, paper by default, never live trading during this walkthrough.

1. Say: "Now I need an Alpaca paper trading key. This usually takes 2 to 5 minutes depending on whether you already have an account, and there's no cost, paper trading is free and never touches real money."
2. Open the Alpaca paper dashboard:
   - **Mac:** `open https://app.alpaca.markets/paper/dashboard/overview`
   - **Linux:** `xdg-open https://app.alpaca.markets/paper/dashboard/overview`
   - **Windows, PowerShell:** `Start-Process "https://app.alpaca.markets/paper/dashboard/overview"`
   - **Windows, Git Bash:** `cmd //c start "" "https://app.alpaca.markets/paper/dashboard/overview"`
3. Say: "Sign in or sign up if you need to. On the paper dashboard, look in the left sidebar for **Your API Keys**, then click **Generate New Keys**. Copy both the Key ID and the Secret, the secret is only shown once."
4. Open `.env` in their editor:
   - **Mac:** `open -e ~/.claude/skills/jev-loop/.env`
   - **Linux:** `${EDITOR:-nano} ~/.claude/skills/jev-loop/.env` (or `xdg-open` if that opens a GUI text editor on their system)
   - **Windows, PowerShell:** `notepad "$HOME\.claude\skills\jev-loop\.env"`
   - **Windows, Git Bash:** `notepad "$(cygpath -w ~/.claude/skills/jev-loop/.env)"`
5. Say: "Paste the Key ID after `ALPACA_API_KEY=` and the Secret after `ALPACA_SECRET_KEY=`, save, and tell me when you're done."
6. Wait for the user to confirm.
7. Verify with a real call:

```bash
cd ~/.claude/skills/jev-loop
set -a; source .env; set +a
curl -s -w "\nHTTP_STATUS:%{http_code}\n" https://paper-api.alpaca.markets/v2/account \
  -H "APCA-API-KEY-ID: $ALPACA_API_KEY" -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY"
```

   On Windows, don't `source` the file. In Git Bash, strip Notepad's line endings as you load it:

```bash
cd ~/.claude/skills/jev-loop
set -a; source <(tr -d '\r' < .env); set +a
curl -s -w "\nHTTP_STATUS:%{http_code}\n" https://paper-api.alpaca.markets/v2/account \
  -H "APCA-API-KEY-ID: $ALPACA_API_KEY" -H "APCA-API-SECRET-KEY: $ALPACA_SECRET_KEY"
```

   In PowerShell, read the keys out of `.env` and call `curl.exe` (not `curl`):

```powershell
cd ~/.claude/skills/jev-loop
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
    Set-Item -Path "env:$($Matches[1])" -Value $Matches[2].Trim().Trim('"').Trim("'")
  }
}
curl.exe -s -w "\nHTTP_STATUS:%{http_code}\n" https://paper-api.alpaca.markets/v2/account -H "APCA-API-KEY-ID: $env:ALPACA_API_KEY" -H "APCA-API-SECRET-KEY: $env:ALPACA_SECRET_KEY"
```

8. **On `HTTP_STATUS:200`:** parse the JSON, print `✓ Alpaca paper account verified, cash $<cash>, status <status>.` and continue to Phase 5.

9. **On `HTTP_STATUS:401`, or any other non-200 status: do not abort.** This almost always means one of: the key was copied from the **live** dashboard instead of the **paper** one (a paper key starts with `PK`), a character got clipped during paste, or the key was regenerated since. Handle it the same way every time, as many times as it takes:
   - Print exactly: "That key didn't verify (HTTP `<status>`). This is usually the live-dashboard key instead of the paper one, or a copy-paste slip. Let's try again, I'll reopen both pages."
   - Re-open the paper dashboard (step 2) and re-open `.env` (step 4).
   - Say: "Double check you're on `app.alpaca.markets/paper/dashboard/overview` (the URL must say `paper`), regenerate the key if you're not sure, paste both values again, save, and tell me when you're done."
   - Wait, then re-run the verification curl in step 7.
   - Repeat as many times as needed. Never move on with an unverified key, and never tell the user to give up.

---

## Phase 5: Jev decision model (the normal route works today, no waitlist)

Jev is optional. Without a working key here the loop runs on a clearly-labelled mock decision client, plausible, persistent, never presented as real, so nothing above is blocked by this step.

1. Say: "Now, optionally, a key for Jev, the decision model. The normal route is a Vercel AI Gateway key: it works today, no invite and no waitlist. One thing before we go there: Vercel needs a card on the team on file before the gateway will serve requests, even the free starting credits, so add one if the team doesn't have one yet. At this tick rate, a few dollars covers roughly a month. If you already have a direct TypeSafe key from being off their waitlist, that's a faster optional extra, one less network hop, but nobody needs it to follow along today. If you don't want to set up either right now, say so and I'll run everything on the mock. The loop and the dashboard both work fully on it."
2. For the normal route: open `https://vercel.com/dashboard` with the open command for this OS and shell from step 1.1 (`open`, `xdg-open`, `Start-Process` in PowerShell, `cmd //c start ""` in Git Bash) and say: "Pick your team, then in the left sidebar go to **AI Gateway**, then **API keys**, then create a key. If the team doesn't have a card on file yet, that's the one prerequisite: add it first under the team's billing settings, then come back and create the key."
3. If they mention they already have a direct TypeSafe key: say: "Paste that in when we get to the `.env` file instead, it skips the gateway's one extra hop." No need to open typesafe.ai or discuss the waitlist, this is only relevant to someone already past it.
4. Re-open `.env` (same command as Phase 4 step 4) and say: "Paste it after `AI_GATEWAY_API_KEY=` for the normal route, or `TYPESAFE_API_KEY=` if you already have a direct key. Save, and tell me when you're done. Or tell me to skip this and I'll run on the mock."
5. Wait for the user to confirm, or to say skip.
6. **If they skip:** print `Running on the mock decision client, no AI Gateway or TypeSafe key set. Mock runs are dry: real market data, no orders. You can add one later and re-run any jev-loop command.` and go to Phase 6.
7. **Otherwise, verify with one real decision call:**

```bash
cd ~/.claude/skills/jev-loop
set -a; source .env; set +a
uv run python -c "
import time
from jevloop.client import resolve_decision_client, GatewayVerificationRequired
from jevloop.battery import run_battery
from jevloop.state import build_snapshot, InventoryState

client = resolve_decision_client()
now = time.time()
inv = InventoryState(equity_usd=1000, high_water_mark_usd=1000)
snap = build_snapshot(as_of=now, mid=85800.0, microprice=85800.5, spread_bps=3.4,
    bid_depth=[(85795,0.5),(85790,0.4),(85780,0.3)],
    ask_depth=[(85805,0.4),(85810,0.3),(85820,0.2)],
    trade_prices=[(now-i,85800+(i%7)) for i in range(60)],
    trade_sides=[(now-i,'buy' if i%2 else 'sell') for i in range(30)],
    inv=inv, data_timestamp=now-0.2)
try:
    answers, meta = run_battery(client, snap, timeout=5.0)
    print(f'model={meta[\"model\"]} route={meta[\"route\"]} latency_ms={meta[\"latency_ms\"]}')
    for k, v in answers.items():
        print(f'  {k}: {v}')
except GatewayVerificationRequired as exc:
    print(f'GATEWAY_403: {exc}')
"
```

   On Windows (PowerShell or Git Bash) the quoting in that one-liner breaks. Instead, write the same Python code to a file `verify_jev.py` in `~/.claude/skills/jev-loop/`, with every `\"` changed to a plain `"`, then run it with the keys loaded from `.env`, then delete the file:

```powershell
cd ~/.claude/skills/jev-loop
uv run --env-file .env python verify_jev.py
Remove-Item verify_jev.py
```

   (Git Bash: the same `uv run --env-file .env python verify_jev.py`, then `rm verify_jev.py`.)

8. **On success:** print the seven answers, the latency, and the model exactly as the script prints them, then say one line naming the route used (the gateway, or a direct key, and that the gateway adds one hop) and continue to Phase 6.

9. **On `GATEWAY_403` (customer_verification_required):** print exactly: "The Vercel AI Gateway needs a card on file before it will serve requests. Add one at https://vercel.com/d?to=%2F%5Bteam%5D%2F%7E%2Fai%3Fmodal%3Dadd-credit-card, then re-run this verification. For now I'm continuing on the mock decision client so nothing is blocked." Then continue to Phase 6 on the mock. Do not treat this as a fatal error.

10. **On any other error** (bad key, network): print the exact error, offer to re-open `.env` and retry once, and if it still fails say: "I'll continue on the mock decision client. You can fix the key later and every `jev-loop` command will pick it up automatically."

---

## Phase 6: Choose an asset

1. If the user already picked a supported asset in Phase 0.1, use it and skip to step 3. Otherwise say in one line: "Two options: any crypto pair, which runs 24/7 (like BTC/USD, ETH/USD, or PAXG/USD for gold), or any US stock or ETF, which only trades during market hours (like AAPL, SPY, GLD, NVDA). Which do you want to watch, or say nothing and I'll default to BTC/USD since it never closes."
2. Wait for their answer. If they say nothing or say "default", use `BTC/USD`.
3. Validate whatever they typed:

```bash
cd ~/.claude/skills/jev-loop
uv run python -m jevloop validate-symbol "<THEIR_SYMBOL>"
```

4. **On success:** print the resolved spec exactly as the command prints it (asset class, session, minimum order size, precision, shorting, depth). Say one sentence plain-English translation, for example: "AAPL resolved, a US stock, so the loop only trades while the market is open and the risk limits scale to a per-share price instead of a coin price."
5. **On failure** (`UnknownSymbolError`, printed as a plain message naming valid forms): say the message back in one sentence, then re-ask step 1. Never guess a symbol on the user's behalf.
6. Open `.env` (same command as Phase 4 step 4) and say: "I'm setting `DEFAULT_SYMBOL` to `<resolved symbol>` so every command defaults to it. Save if you want to change it later." Then write or update the `DEFAULT_SYMBOL=` line in `.env` yourself (do not require the user to type it):

```bash
cd ~/.claude/skills/jev-loop
python3 - <<'PYEOF'
import pathlib
p = pathlib.Path(".env")
lines = [l for l in p.read_text().splitlines() if not l.startswith("DEFAULT_SYMBOL=")]
lines.append("DEFAULT_SYMBOL=<RESOLVED_SYMBOL>")
p.write_text("\n".join(lines) + "\n")
PYEOF
```

On Windows, `python3` and the `<<'PYEOF'` heredoc are the problem. Git Bash keeps the heredoc but swaps `python3 -` for `uv run python -`. PowerShell pipes the same code in:

```powershell
cd ~/.claude/skills/jev-loop
@'
import pathlib
p = pathlib.Path(".env")
lines = [l for l in p.read_text().splitlines() if not l.startswith("DEFAULT_SYMBOL=")]
lines.append("DEFAULT_SYMBOL=<RESOLVED_SYMBOL>")
p.write_text("\n".join(lines) + "\n")
'@ | uv run python -
```

Replace `<RESOLVED_SYMBOL>` with the actual resolved symbol before running this. Confirm by printing the line back from `.env`.

7. If the resolved asset is a US equity, mention once: "Since the market can be closed, the demo run in a few minutes might just show HOLD lines if it's outside market hours right now, that's the loop refusing to trade on a frozen price, not a bug. Crypto never has that problem."

---

## Phase 7: First run: 30 ticks in paper mode

Run the loop so the user sees it work. This is the load-bearing demo moment. Use the symbol resolved and saved in Phase 6 (read `DEFAULT_SYMBOL` from `.env`, or pass `--symbol` explicitly with that value):

```bash
cd ~/.claude/skills/jev-loop
set -a; source .env; set +a
uv run python -m jevloop run --paper --ticks 30 --symbol "$DEFAULT_SYMBOL"
```

On Windows (PowerShell or Git Bash), let uv load `.env`. `--symbol` then defaults to `DEFAULT_SYMBOL` from the file, so leave it off:

```powershell
cd ~/.claude/skills/jev-loop
uv run --env-file .env python -m jevloop run --paper --ticks 30
```

If the user asked for a bar timeframe in Phase 0.1 (e.g. 30m), still do this first 30-tick run on the default 2-second cadence so they see it work in a minute, not fifteen hours. Then, for the continuous run below, add `--bar 30m` (or their timeframe). In bar mode each tick is one bar close, so 30 ticks of `--bar 30m` takes 15 hours.

Let the tick lines print to the terminal as they happen, one line per tick, e.g.:

```
tick 41 | mid 85,808.2 | regime mean_reverting 86% | tox 0.36 | env 2.1 | xh 2.6 | 370 ms | QUOTE_WIDE skew +0.0 | filled buy 0.0001 @ 85,807.90
```

If a tick shows `late` or `HOLD (late)`, that is the block-deadline rule working as designed. Say so in one sentence and do not treat it as an error. If a tick shows `market is closed`, that is the equity market-hours guard: it is expected outside trading hours and never places an order. If a tick shows `order error`, that is a real Alpaca-side rejection (for example a minimum-notional or short-selling rule on a two-sided quote) being caught and logged rather than crashing the loop. Say so in one sentence if it comes up, and keep going: the loop is designed to survive individual order rejections.

When it finishes:

```bash
cd ~/.claude/skills/jev-loop
uv run python -m jevloop serve --port 8765 &
```

On Windows, Git Bash can use the same `&` line (or your own run-in-background feature). In PowerShell, `&` at the end of a line doesn't background anything; start it as its own process instead:

```powershell
Start-Process uv -ArgumentList "run", "python", "-m", "jevloop", "serve", "--port", "8765" -WorkingDirectory "$HOME\.claude\skills\jev-loop" -WindowStyle Hidden -PassThru
```

Note the `Id` it prints; `Stop-Process -Id <Id>` stops the dashboard server later.

Wait one second, then open the dashboard:

- **Mac:** `open http://127.0.0.1:8765/index.html`
- **Linux:** `xdg-open http://127.0.0.1:8765/index.html`
- **Windows, PowerShell:** `Start-Process "http://127.0.0.1:8765/index.html"`
- **Windows, Git Bash:** `cmd //c start "" "http://127.0.0.1:8765/index.html"`

Say: "That's the live dashboard, reading the real log from the run that just finished, nothing on it is simulated. There's a dark variant too at `/wall.html` if you want it for a different look. Top right are Start and Stop: Stop pauses new orders but keeps the data and this page updating, and it does not close a position. The KILL switch (the hard risk limits) does that, and still works while paused. Start picks up again from the next tick. It remembers which one you pressed, even after a refresh." If port 8765 is already taken on this machine, retry once on 8899 and use that port in both commands above.

Then ask once: "Want me to keep this running continuously in the background instead of stopping at 30 ticks? It'll keep trading paper until you stop it." Wait for a yes or no.

**If no:** say "Understood, it stays stopped at the 30-tick run above. You can start it again any time with `jev-loop run --paper --forever`." and continue to Phase 8.

**If yes:** start it unbounded, in the background, on the same symbol. If they asked for a bar timeframe, add `--bar <timeframe>` (e.g. `--bar 30m`) to the run command, on every OS:

```bash
cd ~/.claude/skills/jev-loop
set -a; source .env; set +a
mkdir -p ~/.jev-loop
nohup uv run python -m jevloop run --paper --forever --symbol "$DEFAULT_SYMBOL" \
  > ~/.jev-loop/continuous.log 2>&1 &
echo $! > ~/.jev-loop/continuous.pid
```

Confirm it is actually running (`cat ~/.jev-loop/continuous.pid`, then check the process exists), then say: "It's running continuously in the background now, paper only. The dashboard you already have open keeps reading it live. To stop it: `kill $(cat ~/.jev-loop/continuous.pid)`, that's a clean shutdown, it cancels the resting orders it placed (nothing else on your account) before it exits. Its own output is logged at `~/.jev-loop/continuous.log` if you want to check on it later." Then continue to Phase 8.

**On Windows**, `nohup` and `kill` are the parts that change, and the stop matters: the loop's clean shutdown (cancelling the orders it placed) runs on Ctrl+C. A forced kill on Windows skips it.

- **Git Bash:** the same `cd`, `mkdir -p` and `echo $!` lines, but start it without `nohup` and with uv loading `.env`:

  ```bash
  cd ~/.claude/skills/jev-loop
  mkdir -p ~/.jev-loop
  uv run --env-file .env python -m jevloop run --paper --forever > ~/.jev-loop/continuous.log 2>&1 &
  echo $! > ~/.jev-loop/continuous.pid
  ```

- **PowerShell:** open it in its own minimised window, so there is a window to press Ctrl+C in later:

  ```powershell
  New-Item -ItemType Directory -Force -Path "$HOME\.jev-loop" | Out-Null
  $p = Start-Process powershell -WindowStyle Minimized -WorkingDirectory "$HOME\.claude\skills\jev-loop" -ArgumentList "-NoExit", "-Command", "uv run --env-file .env python -m jevloop run --paper --forever" -PassThru
  $p.Id | Set-Content "$HOME\.jev-loop\continuous.pid"
  ```

  Check it's alive with `Get-Process -Id (Get-Content "$HOME\.jev-loop\continuous.pid")`. The ticks print in that window and log to `~/.jev-loop/log.jsonl`.

On Windows, replace the stop instruction you give the user with: "To stop it cleanly, open the minimised jev-loop window from the taskbar and press Ctrl+C. That cancels the resting orders it placed (nothing else on your account) before it exits. `Stop-Process -Id (Get-Content $HOME\.jev-loop\continuous.pid)` also stops it, but it's a hard stop, so check the Alpaca paper dashboard for any jev-loop orders still open and cancel them there." (Git Bash: `kill $(cat ~/.jev-loop/continuous.pid)` is also a hard stop on Windows, same caveat.)

---

## Phase 8: Confirmation and how to use it

First, print the split table again, this time with file names, by running it rather than retyping it:

```bash
cd ~/.claude/skills/jev-loop
uv run python -m jevloop explain-split
```

Print its output exactly as it prints. Then print a final summary. Match this format and wording:

```
================================================================
 ✓ jev-loop skill installed at ~/.claude/skills/jev-loop/

 Installed:
   • Any asset (assets.py): <RESOLVED_SYMBOL> resolved as <crypto | a US
     equity>, <24/7 | market hours only>
   • Deterministic state engine (state.py), under ~400 tokens, strict
     timestamp discipline, session VWAP, honest depth degradation
   • The split, enforced (split.py): every battery question is checked
     against an allow-list and refused if it looks like arithmetic
   • Seven-question Jev battery (battery.py): regime, direction, toxic
     flow, liquidity stress, quote environment, inventory pressure,
     execution health
   • Decision client: <Vercel AI Gateway | TypeSafe direct | MOCK>
   • Your strategy lives in strategy.py: seven tunable thresholds behind
     compose_action(), plus a hook to override or veto any action.
     Shipped default changes nothing until you edit it
   • Avellaneda-Stoikov pricing (pricing.py), code, never the model
   • Risk engine (risk.py): nine hard limits in dollars, checked before
     every order, never raised by a strategy or by going live
   • Fallback ladder (ladder.py): RUN / REDUCE / HOLD_LATE / RULES_ONLY / KILL
   • Alpaca execution (execution/alpaca.py), paper by default; live
     trading exists only behind a deliberately awkward three-gate
     opt-in (--live, an environment variable, and a typed confirmation,
     all three), and refuses to trade a closed equity market either way
   • Live dashboard at dashboard/index.html and dashboard/wall.html
   • Start / Stop on the dashboard: Stop pauses new orders, keeps positions (KILL closes them)
   • A full test suite, all passing, no network required

 First run: 30 ticks in paper mode on <RESOLVED_SYMBOL>, complete.
 <Now running continuously in the background, PID <PID>, stop with
 `kill <PID>` (Windows: Ctrl+C in its window) | Stopped after the 30-tick run, restart any time with
 `jev-loop run --paper --forever`.> Dashboard open.

 You can now ask Claude, in any Claude Code session, to:
   • run the jev-loop skill for 100 ticks on ETH/USD
   • run jev-loop on AAPL and tell me if the market's open
   • run jev-loop in mock mode so you can see the dashboard without a key
   • keep jev-loop running continuously in the background
   • calibrate the jev-loop and show me the Brier score
   • explain the split in jev-loop

 Or run it directly:
   cd ~/.claude/skills/jev-loop
   uv run python -m jevloop run --paper --ticks 200 --symbol BTC/USD
   uv run python -m jevloop run --paper --forever --symbol BTC/USD
   uv run python -m jevloop validate-symbol AAPL
   uv run python -m jevloop explain-split
   uv run python -m jevloop calibrate
   uv run python -m jevloop serve

 Your strategy's tunable thresholds are in jevloop/strategy.py, the file
 built for you to edit, alongside a hook that can override or veto any
 action. The hard risk caps stay separate, in jevloop/limits.py, and a
 strategy can never raise them. Change a number, restart the loop, see
 different behaviour, no prompt to edit, no model to retrain.

 Framework: Roan (@RohOnChain), original article author.
 Installed as a Claude Code skill by Lewis Jackson.

 Paper by default, everywhere. Live trading exists only behind the
 three-gate opt-in documented in SKILL.md and README.md. This does not
 claim a profit and it is not investment advice. Jev makes seven
 judgments cheap and fast, edge is still yours, and it lives in
 strategy.py.
================================================================
```

Fill in the decision-client line with whichever of Vercel AI Gateway / TypeSafe direct / MOCK actually won in Phase 5, `<RESOLVED_SYMBOL>` with whatever was resolved and saved in Phase 6, and the continuous-run line with whichever branch of Phase 7's question actually happened (including the real PID if it is running in the background). On Windows, write the "Or run it directly" lines as `uv run --env-file .env python -m jevloop ...` so the keys in `.env` are loaded.

End. Do not continue past Phase 8. Do not suggest next steps the user did not ask for.
