# Demo recording script

A script for the demo video: a short tour of the code, then two real runs on a
small Go package with one bug. Target length 6 to 8 minutes (the limit is 10).
Cut the waiting time while the models work; each run takes about two minutes.

Commands are for Windows PowerShell, run from the repository root. Line numbers
refer to this branch and may drift if the code changes.

| File | Purpose |
|---|---|
| `task/` | Workspace for the runs: `stats.go` (bug in `Mean`), `stats_test.go`, `CHANGELOG.md` |
| `contract-basic.json` | Goal, acceptance criteria, `go test ./...` as the verify command, review on |
| `contract-changelog.json` | Same, plus one criterion the prompt does not mention: a CHANGELOG entry |
| `policy.json` | Lets `go test` run without an approval prompt |

The contracts and the policy stay outside the workspace on purpose: the agents
never see them, only the completion gate and its reviewer do.

## Before recording

Needs Go 1.26+, Git, and API keys for two models (developer and reviewer).

```powershell
go build -o bin\xcode.exe .\cmd\xcode
```

Put the model configuration in `C:\Users\<you>\.xcode\config`, outside the
repository, with two different model slots:

```ini
developer=deepseek
reviewer=glm
model.deepseek.key=sk-...
model.deepseek.base-url=https://api.deepseek.com
model.deepseek.id=deepseek-v4-flash
model.glm.key=...
model.glm.base-url=https://open.bigmodel.cn/api/paas/v4
model.glm.id=glm-5.3
```

In the PowerShell window used for recording:

```powershell
$repo  = (Get-Location).Path
$xcode = "$repo\bin\xcode.exe"
$ws    = "$env:TEMP\xcode-demo"

function Reset-Demo {
    Set-Location $repo
    Remove-Item -Recurse -Force $ws -ErrorAction SilentlyContinue
    Copy-Item -Recurse "$repo\demo\task" $ws
    Set-Location $ws
    git init -q
    git add -A
    git commit -q -m "baseline"
}
```

`Reset-Demo` gives every run a fresh copy of the buggy workspace. Do one full
rehearsal first: wording and step counts depend on the models.

## 1. What it is (about 30 seconds)

Show the top of `README.md`.

> XCode is a command-line coding assistant written in Go. You describe a task,
> and a team of agents reads the code, edits it and runs the tests. The run may
> only end when the tests and an independent reviewer agree.

## 2. Code tour (about 3 minutes)

Open the repository in an editor (in VS Code, Ctrl+G jumps to a line). One stop
per mechanism; say one or two sentences at each.

| Stop | Where | Point at | Say |
|---|---|---|---|
| Agent loop | `internal/harness/agent.go:169` | the `for step` loop; line 365, a reply without tool calls; line 375, the contract check | Every agent is this loop: the model asks for tools, the results go back into the conversation. A reply without tool calls is a completion claim, and with a contract it goes to the gate first. |
| Delegation | `internal/harness/delegate.go:97` | `Execute`; line 124, the stage-order error; line 219, `RoleTools` | `delegate` starts a new agent with an empty history and returns only its final answer. The developer is refused until the planner has run, and each role gets its own tool set. |
| Wiring | `cmd/xcode/main.go:444` | the narrowed registry; then `internal/harness/run_options.go:68` | Each sub-agent runs on a registry with only its role's tools. In pipeline mode the orchestrator is offered just `delegate` and `git_diff`. |
| Completion gate | `internal/harness/contract.go:62` | `runCompletionGate`; line 251, the required verdict line | When a model says it is done, the framework runs the verify commands itself, then sends a fresh reviewer that must end with PASS or ISSUES. |
| Tool pipeline | `internal/executor/executor.go:93` | the numbered steps in `Execute` | Every tool call from every agent passes the same steps: declare intent, policy, approval, snapshot, execute, journal. |

## 3. Run 1: pipeline (about 2 minutes)

```powershell
Reset-Demo
go test ./...        # show the failing test first
& $xcode --non-interactive --orchestrate pipeline --max-steps 12 --timeout 10m `
    --contract "$repo\demo\contract-basic.json" --policy "$repo\demo\policy.json" `
    "Mean in stats.go returns wrong results for some inputs. Fix it."
git diff
go test ./...
```

Point out, as the lines appear:

1. The orchestrator's only actions are `delegate` calls.
2. `[agent] sub-1 planner` reads the code and returns a diagnosis. Its own steps
   are indented and tagged.
3. `sub-2 developer` receives the task plus the diagnosis, edits `stats.go`
   (a `[checkpoint]` line comes first) and runs the tests.
4. `[step N] exec [gate] ...` and `delegate [gate] reviewer review`: the gate,
   not a model, runs the tests and sends `sub-3 reviewer` on the second model.
5. `[gate] passed` ends the run.

## 4. Run 2: the reviewer sends work back (about 2 minutes)

The contract asks for a CHANGELOG entry; the prompt does not mention it, and the
working agent never sees the contract.

```powershell
Reset-Demo
& $xcode --non-interactive --orchestrate single-review --max-steps 20 --timeout 10m `
    --contract "$repo\demo\contract-changelog.json" --policy "$repo\demo\policy.json" `
    "Mean in stats.go returns wrong results for some inputs. Fix it."
git diff
```

Point out:

1. The agent fixes the code, its tests pass, and it claims completion.
2. The gate's own test run passes, then `sub-1 reviewer` reads `CHANGELOG.md`
   and returns `ISSUES`.
3. `[gate] blocked: reviewer found issues: ...` The reason goes back to the
   agent as a message and the loop continues.
4. The agent adds the entry. The workspace changed, so the gate tests and
   reviews again before `[gate] passed`.

If the reviewer passes the first claim, or the agent adds the entry on its own,
run `Reset-Demo` and record again.

## 5. Optional extras (about 1 minute)

Every event carries the id of the agent that produced it:

```powershell
$log = Get-ChildItem .xcode-state\logs\*.jsonl | Sort-Object LastWriteTime | Select-Object -Last 1
Get-Content $log | ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.kind -in 'agent.spawned','agent.completed','completion.gate.blocked','completion.gate.passed' } |
    Format-Table time, agent_id, kind -AutoSize
```

Snapshots taken before each write can be listed and restored:

```powershell
& $xcode checkpoints
& $xcode restore --id <checkpoint id from the list>
```

To show an approval prompt, run any task without `--non-interactive`: a command
other than `go test` then asks `y` (once), `s` (session) or `N` (deny).

## Reading the output

- Lines without indentation belong to the orchestrator or the framework.
- `[agent] sub-N <role> spawned / returned` marks the life of one sub-agent.
- Indented `[sub-N <role>]` lines are that sub-agent's own steps.
- `[gate] blocked` / `[gate] passed` is the completion gate's decision.

`--non-interactive` keeps the recording smooth: a command that would need
approval is refused automatically and the agent carries on without it.
