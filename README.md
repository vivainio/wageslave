# wageslave

Use your personal GitHub account from a company computer without installing personal SSH keys or tokens on the host. Everything runs inside a Docker container.

## How it works

```
Host machine                    Docker container
─────────────                   ─────────────────
~/.config/wageslave/ssh/  ──▶   /root/.ssh/ (read-only)
~/.config/wageslave/gh/   ──▶   /root/.config/gh/ (read-only)
~/.config/wageslave/gitconfig ▶ /root/.gitconfig (read-only)
$(pwd)                    ──▶   /workspace (read-write)
```

Your personal credentials never touch `~/.ssh` or `~/.gitconfig` on the host. They live in `~/.config/wageslave/` and are only mounted into short-lived containers.

## Install

```bash
# Requires: Python 3.11+, uv, Docker

git clone <this-repo> ~/tools/wageslave
cd ~/tools/wageslave
uv sync
```

## Setup

```bash
# First-time setup (generates SSH key, sets git identity, builds Docker image)
uv run wageslave setup

# Add the printed public key to GitHub → Settings → SSH keys

# Authenticate gh CLI
uv run wageslave gh auth login
```

Or install globally so `wageslave` is on your PATH:

```bash
uv tool install -e ~/tools/wageslave
wageslave setup
```

## Usage

```bash
# Clone a personal repo
wageslave git clone git@github.com:youruser/project.git
cd project

# Normal git workflow
wageslave git status
wageslave git add -A
wageslave git commit -m "fix: thing"
wageslave git push

# GitHub CLI
wageslave gh repo create my-project --private
wageslave gh pr create --title "Add feature"
wageslave gh pr list

# Interactive shell inside the container
wageslave shell
```

## Configuration

All config lives in `~/.config/wageslave/` (override with `WAGESLAVE_HOME` env var):

| Path | Purpose |
|------|---------|
| `ssh/id_ed25519` | Personal SSH private key |
| `ssh/id_ed25519.pub` | Personal SSH public key |
| `gh/` | gh CLI auth tokens |
| `gitconfig` | Git user.name and user.email |

## Requirements

- Python 3.11+
- Docker
