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
- An SSH key for GitHub in `~/.ssh/` with a matching entry in `~/.ssh/config`:

```
Host github-public
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
```

## Install

```bash
uv tool install wageslave
```

## Setup

```bash
wageslave setup
```

This auto-detects your existing credentials:

1. **SSH key** — finds the GitHub IdentityFile from `~/.ssh/config`
2. **Git identity** — reads `user.name` and `user.email` from global git config
3. **known_hosts** — runs `ssh-keyscan github.com`
4. **Podman image** — builds the Alpine-based container with git, ssh, and gh

If you have multiple GitHub hosts in `~/.ssh/config`, setup will list them and ask you to pick one:

```bash
wageslave setup --host github-public
```

Then authenticate the GitHub CLI (one-time, opens a browser flow):

```bash
wageslave gh auth login
```

## Usage

Only commands that talk to GitHub need wageslave. Local git commands (`add`, `commit`, `status`, etc.) should use plain `git`.

```bash
# Clone a personal repo
wageslave git clone git@github.com:youruser/project.git
cd project

# Push/pull (needs SSH credentials)
wageslave git push
wageslave git pull

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
| `ssh/known_hosts` | GitHub host key |
| `gh/hosts.yml` | gh CLI auth token |
| `gitconfig` | Git user.name, user.email, safe.directory |
