# Demo walkthrough

A small, repeatable example for the demo video: a Go package with one bug, two
task contracts and a policy file. The commands are for Windows PowerShell and
are run from the repository root.

`task/` is the workspace the agents work on. `Mean` in `task/stats.go` divides
two integers before converting, so `go test ./...` fails. The contracts and the
policy file stay outside the workspace on purpose: the agents never see them,
only the completion gate and its reviewer do.

| File | Purpose |
|---|---|
| `task/` | Workspace: `stats.go` (bug in `Mean`), `stats_test.go`, `CHANGELOG.md` |
| `contract-basic.json` | Goal, acceptance criteria, `go test ./...` as the verify command, review on |
| `contract-changelog.json` | Same, plus one criterion the prompt does not mention: a CHANGELOG entry |
| `policy.json` | Lets `go test` run without an approval prompt |

## One-time setup

Needs Go 1.26+, Git, and API keys for two providers (developer and reviewer).

```powershell
go build -o bin\xcode.exe .\cmd\xcode
```

Put the model configuration in the global config file,
`C:\Users\<you>\.xcode\config`. If the repository already has a working
`.xcode\config`, copy it:

```powershell
New-Item -ItemType Directory -Force $HOME\.xcode | Out-Null
Copy-Item .xcode\config $HOME\.xcode\config
```

It must name two different model slots, for example:

```ini
developer=deepseek
reviewer=glm
model.deepseek.key=sk-...
model.deepseek.base-url=https://api.deepseek.com
model.deepseek.id=deepseek-flash
model.glm.key=...
model.glm.base-url=https://open.bigmodel.cn/api/paas/v4
model.glm.id=glm-4.6
```

Define two helpers in the PowerShell session used for recording:

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

`Reset-Demo` gives every run a fresh copy of the buggy workspace and leaves the
shell inside it.

## Reading the output

- Lines without indentation belong to the orchestrator or the framework.
- `[agent] sub-N <role> spawned / returned` marks the life of one sub-agent.
- Indented `[sub-N <role>]` lines are that sub-agent's own steps.
- `[step N] exec [gate] ...` and `[step N] delegate [gate] reviewer review` are
  issued by the completion gate, not by a model.
- `[gate] blocked: ...` / `[gate] passed ...` is the gate's decision.

## Run 1: pipeline (planner, developer, reviewer)

```powershell
Reset-Demo
go test ./...        # show the failing test first
& $xcode --orchestrate pipeline --max-steps 12 --timeout 10m `
    --contract "$repo\demo\contract-basic.json" --policy "$repo\demo\policy.json" `
    "Mean in stats.go returns wrong results for some inputs. Fix it."
git diff
go test ./...
```

What to point out:

1. The orchestrator's only actions are `delegate` calls. It cannot edit files:
   in pipeline mode it is offered `delegate` and `git_diff` only.
2. `sub-1 planner` reads and may run the tests, then returns a short diagnosis.
   It has no edit tool.
3. `sub-2 developer` receives the task plus that diagnosis, edits `stats.go`
   (a `[checkpoint]` line precedes the write) and runs the tests.
4. When the orchestrator says it is done, the gate runs `go test ./...` itself
   and spawns `sub-3 reviewer` on the second model with a fresh context.
5. `[gate] passed` ends the run.

## Run 2: the reviewer rejects a completion claim

Same bug, single agent plus review, and a contract with a criterion the prompt
does not mention (a CHANGELOG entry). The working agent is never told about it;
the reviewer checks the contract and should send the work back.

```powershell
Reset-Demo
& $xcode --orchestrate single-review --max-steps 20 --timeout 10m `
    --contract "$repo\demo\contract-changelog.json" --policy "$repo\demo\policy.json" `
    "Mean in stats.go returns wrong results for some inputs. Fix it."
git diff
```

What to point out:

1. The agent fixes the code, the tests pass, and it claims completion.
2. The gate's own test run passes, then the reviewer returns
   `GATE-VERDICT: ISSUES: ...` because `CHANGELOG.md` has no entry.
3. `[gate] blocked: reviewer found issues: ...` The reason is appended to the
   conversation as a message and the loop continues.
4. The agent adds the entry. The workspace fingerprint changed, so the gate
   runs the tests and the review again before `[gate] passed`.

Models are not deterministic. If the reviewer passes the first claim, or the
agent happens to add a CHANGELOG entry on its own, reset and run again.

## Run 3: single-agent baseline and the event log

```powershell
Reset-Demo
& $xcode --orchestrate single --max-steps 20 --timeout 10m `
    --policy "$repo\demo\policy.json" `
    "Mean in stats.go returns wrong results for some inputs. Fix it."
```

No sub-agents, no gate: the run ends as soon as the model says it is done.

Every run writes a JSONL event log; each event carries the `agent_id` of the
agent that produced it. After Run 1 or Run 2:

```powershell
$log = Get-ChildItem .xcode-state\logs\*.jsonl | Sort-Object LastWriteTime | Select-Object -Last 1
Get-Content $log | ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.kind -in 'agent.spawned','agent.completed','tool.started','completion.gate.blocked','completion.gate.passed' } |
    Format-Table time, agent_id, kind, tool -AutoSize
```

Pre-write snapshots can be listed and restored:

```powershell
& $xcode checkpoints
& $xcode restore --id <checkpoint id from the list>
```

## Notes for recording

- Any command other than `go test` triggers an approval prompt
  (`y` once, `s` for the session, `N` deny). That is the default
  `workspace-write` mode and is worth showing once.
- The default run timeout is two minutes, which three agents with a thinking
  model can exceed; keep `--timeout 10m`.
- Do one full rehearsal before recording. Wording, step counts and timing
  depend on the models.
