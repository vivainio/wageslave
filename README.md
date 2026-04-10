# wageslave

Use your personal GitHub account from a company computer without installing personal SSH keys or tokens on the host. Everything runs inside a Podman container.

## How it works

```
Host machine                    Podman container
─────────────                   ─────────────────
~/.config/wageslave/ssh/  ──▶   ~/.ssh/ (read-only)
~/.config/wageslave/gh/   ──▶   ~/.config/gh/ (read-only)
~/.config/wageslave/gitconfig ▶ ~/.gitconfig (read-only)
$(pwd)                    ──▶   /workspace (read-write)
```

Your personal credentials never touch `~/.ssh` or `~/.gitconfig` on the host. They live in `~/.config/wageslave/` and are only mounted into short-lived containers.

## Prerequisites

- Python 3.11+
- Podman

## Install

```bash
uv tool install wageslave
```

## Setup

```bash
wageslave setup
wageslave gh auth login
```

Setup auto-detects existing credentials or creates new ones:

1. **SSH key** — if `~/.ssh/config` has a GitHub entry, copies that key. Otherwise generates a new key pair and prints the public key to add to https://github.com/settings/ssh/new
2. **Git identity** — reads `user.name` and `user.email` from global git config (uses placeholders if not set — edit `~/.config/wageslave/gitconfig`)
3. **known_hosts** — runs `ssh-keyscan github.com`
4. **Podman image** — builds the Alpine-based container with git, ssh, and gh

If you have multiple GitHub hosts in `~/.ssh/config`, setup will list them and ask you to pick one:

```bash
wageslave setup --host github-public
```

## Usage

A typical workflow only needs `pull`, `push`, and `gh`. Everything else is plain `git`:

```bash
wageslave gh repo clone youruser/project
cd project

# work...
git add -A
git commit -m "Add feature"

wageslave push
wageslave gh pr create --title "Add feature"
```

### Commands

| Command | Runs in container? | Notes |
|---------|-------------------|-------|
| `wageslave pull` | No | Fetches via HTTPS on host |
| `wageslave fetch` | No | Fetches via HTTPS on host |
| `wageslave push` | Yes | Needs SSH credentials |
| `wageslave gh <args>` | Yes | GitHub CLI (PRs, releases, etc.) |
| `wageslave git <args>` | Yes | Escape hatch for any git command |
| `wageslave shell` | Yes | Interactive bash in the container |

## Configuration

All config lives in `~/.config/wageslave/` (override with `WAGESLAVE_HOME` env var):

| Path | Purpose |
|------|---------|
| `ssh/id_ed25519` | Personal SSH private key |
| `ssh/id_ed25519.pub` | Personal SSH public key |
| `ssh/known_hosts` | GitHub host key |
| `gh/hosts.yml` | gh CLI auth token |
| `gitconfig` | Git user.name, user.email, safe.directory |
