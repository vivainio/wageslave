"""Auto-detect and copy credentials for wageslave."""

import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from wageslave import config, docker


@dataclass
class SshHostEntry:
    host: str
    hostname: str = ""
    identity_file: Path | None = None
    options: dict[str, str] = field(default_factory=dict)


def parse_github_hosts() -> list[SshHostEntry]:
    """Parse ~/.ssh/config and return all Host entries that point to github.com."""
    ssh_config = Path.home() / ".ssh" / "config"
    if not ssh_config.exists():
        return []

    entries: list[SshHostEntry] = []
    current: SshHostEntry | None = None

    for line in ssh_config.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.lower().startswith("host "):
            current = SshHostEntry(host=stripped.split(None, 1)[1])
            entries.append(current)
        elif current is None:
            continue
        elif stripped.lower().startswith("hostname"):
            current.hostname = stripped.split(None, 1)[1]
        elif stripped.lower().startswith("identityfile"):
            current.identity_file = Path(stripped.split(None, 1)[1]).expanduser()

    return [e for e in entries if "github.com" in e.hostname.lower()]


def run_setup(host: str | None = None) -> None:
    ssh = config.ssh_dir()
    gh = config.gh_dir()
    gitcfg = config.gitconfig()

    ssh.mkdir(parents=True, exist_ok=True)
    ssh.chmod(0o700)
    gh.mkdir(parents=True, exist_ok=True)

    # SSH key — find from ~/.ssh/config
    dest_key = ssh / "id_ed25519"
    if not dest_key.exists():
        github_hosts = parse_github_hosts()

        if not github_hosts:
            print("No github.com entries found in ~/.ssh/config", file=sys.stderr)
            sys.exit(1)

        if host:
            match = [e for e in github_hosts if e.host == host]
            if not match:
                names = ", ".join(e.host for e in github_hosts)
                print(f"Host '{host}' not found. Available: {names}", file=sys.stderr)
                sys.exit(1)
            entry = match[0]
        elif len(github_hosts) == 1:
            entry = github_hosts[0]
        else:
            print("Multiple GitHub hosts found in ~/.ssh/config:", file=sys.stderr)
            for e in github_hosts:
                key_name = e.identity_file.name if e.identity_file else "?"
                print(f"  {e.host:20s} → {key_name}", file=sys.stderr)
            print("\nRe-run with: wageslave setup --host <name>", file=sys.stderr)
            sys.exit(1)

        if not entry.identity_file or not entry.identity_file.exists():
            print(f"IdentityFile for '{entry.host}' not found", file=sys.stderr)
            sys.exit(1)

        src = entry.identity_file
        shutil.copy2(src, dest_key)
        dest_key.chmod(0o600)
        pub = src.with_suffix(".pub")
        if pub.exists():
            shutil.copy2(pub, dest_key.with_suffix(".pub"))
        print(f"ssh: copied {src.name} (from Host {entry.host})")

    # Git identity
    if not gitcfg.exists():
        name = _git_config_global("user.name")
        email = _git_config_global("user.email")
        if not name or not email:
            print("No git user.name/user.email in global config", file=sys.stderr)
            sys.exit(1)
        gitcfg.write_text(f"[user]\n    name = {name}\n    email = {email}\n")
        print(f"git: {name} <{email}>")

    # gh CLI auth — user must run `wageslave gh auth login` manually
    dest_hosts = gh / "hosts.yml"
    if not dest_hosts.exists():
        print("gh: run 'wageslave gh auth login' to authenticate")

    # Docker image
    print("docker: building image...")
    docker.build_image()

    print("ready")


def _git_config_global(key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--global", key],
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None
