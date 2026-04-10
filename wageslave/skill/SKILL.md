---
name: wageslave
description: Run git/gh commands with personal GitHub credentials inside a Podman container. Use when pushing to personal GitHub repos, running gh CLI for personal account, or cloning personal repos from a company machine.
---

# wageslave

CLI for using personal GitHub credentials safely from a company computer via Podman containers.

**wageslave is ONLY for public/personal GitHub repositories.** Never use it for company/work repositories — those use the normal git/gh workflow with corporate credentials.

## When to use wageslave

Only use `wageslave` for commands that talk to **personal** GitHub over the network:

```bash
wageslave git push
wageslave git pull
wageslave git fetch
wageslave git clone git@github.com:user/repo.git
wageslave gh repo list
wageslave gh pr create --title "..."
wageslave gh release create v0.1.0 --generate-notes
```

## When NOT to use wageslave

- **Company/work repositories** — use plain `git` and `gh` with corporate credentials
- **Local git commands** — do NOT need wageslave. Use plain `git` instead:

```bash
git add -A
git commit -m "message"
git status
git log
git diff
git branch
git checkout
git merge
git rebase
```

Running local commands through wageslave works but is slow and unnecessary — it spins up a container for nothing.

## Setup

If `wageslave` is not yet configured, run:

```bash
wageslave setup
wageslave gh auth login
```

## Typical workflow

```bash
# Local operations — plain git
git add -A
git commit -m "Add feature"

# Remote operations — wageslave
wageslave git push
wageslave gh pr create --title "Add feature"
```

## Security

- Never commit credentials, SSH keys, or tokens to repositories
- The `wageslave` config directory (`~/.config/wageslave/`) must never be committed
- Before pushing to a public repo, verify no internal/proprietary references are included
