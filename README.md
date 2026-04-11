# wageslave

Many companies restrict using personal GitHub accounts alongside corporate ones on company machines. Wageslave lets you use your personal GitHub safely by isolating your credentials inside a Podman container — your personal SSH keys and tokens never touch the host.

## How it works

Credentials are stored encrypted on disk. The encryption key is split in two:
- One half is baked into the Podman image
- The other half is derived from your passphrase at `unlock` time

Both parts are needed to decrypt. On disk, only an opaque encrypted blob is visible.

## Prerequisites

- Python 3.11+
- Podman

## Install

```bash
uv tool install wageslave
```

## Setup

```bash
wageslave setup            # asks for passphrase, generates SSH key
wageslave gh auth login    # authenticate GitHub CLI
wageslave install-skill    # optional: Claude Code skill
```

Setup will:
1. Ask for an encryption passphrase
2. Generate a fresh SSH key pair — add the printed public key to https://github.com/settings/ssh/new
3. Pick up git identity from global config
4. Encrypt everything into `~/.config/wageslave/credentials.enc`
5. Build the Podman image with the other half of the encryption key

## Daily use

Each session (or after reboot), unlock first:

```bash
wageslave unlock    # asks for passphrase
```

Then work normally:

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

Lock when done:

```bash
wageslave lock
```

### Commands

| Command | Container? | Description |
|---------|-----------|-------------|
| `wageslave unlock` | No | Unlock credentials for this session |
| `wageslave lock` | No | Lock credentials |
| `wageslave pull` | No | Git pull via HTTPS on host |
| `wageslave fetch` | No | Git fetch via HTTPS on host |
| `wageslave push` | Yes | Git push (needs SSH key) |
| `wageslave git <args>` | Yes | Any git command |
| `wageslave gh <args>` | Yes | Any GitHub CLI command |
| `wageslave shell` | Yes | Interactive bash |

## Configuration

All config lives in `~/.config/wageslave/`:

| Path | Purpose |
|------|---------|
| `credentials.enc` | Encrypted SSH key, gh token, git config |
| `image.key` | Half of the encryption key (other half in Podman image) |
