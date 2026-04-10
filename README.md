# wageslave

Many companies restrict using personal GitHub accounts alongside corporate ones on company machines. Wageslave lets you use your personal GitHub safely by isolating your credentials inside a Podman container — your personal SSH keys and tokens never touch the host.

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
wageslave install-skill   # optional: Claude Code skill
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

The two core commands run git and gh inside the container with your personal credentials:

```bash
wageslave git push origin main
wageslave gh pr create --title "Add feature"
```

For common operations there are shortcuts that avoid spinning up a container when possible:

| Command | Container? | Description |
|---------|-----------|-------------|
| `wageslave pull` | No | Git pull via HTTPS on host |
| `wageslave fetch` | No | Git fetch via HTTPS on host |
| `wageslave push` | Yes | Git push (needs SSH key) |
| `wageslave git <args>` | Yes | Any git command |
| `wageslave gh <args>` | Yes | Any GitHub CLI command |
| `wageslave shell` | Yes | Interactive bash |

### Typical workflow

```bash
wageslave gh repo clone youruser/project
cd project

# work locally with plain git
git add -A
git commit -m "Add feature"

# push and create PR through wageslave
wageslave push
wageslave gh pr create --title "Add feature"
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
