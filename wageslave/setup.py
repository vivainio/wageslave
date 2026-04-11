"""Setup for wageslave."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from wageslave import config, docker


def run_setup(passphrase: str | None = None) -> None:
    cfg = config.config_dir()
    cfg.mkdir(parents=True, exist_ok=True)

    if not passphrase:
        import getpass

        passphrase = getpass.getpass("Passphrase for credential encryption: ")
        if not passphrase:
            print("wageslave: passphrase cannot be empty", file=sys.stderr)
            sys.exit(1)

    # Build image first (generates encryption key)
    print("podman: building image...")
    docker.build_image()

    # Collect credentials in a temp dir, then encrypt
    with tempfile.TemporaryDirectory(prefix="wageslave-setup-") as tmp:
        tmp_path = Path(tmp)
        ssh = tmp_path / "ssh"
        gh = tmp_path / "gh"
        ssh.mkdir()
        ssh.chmod(0o700)
        gh.mkdir()

        # Generate a fresh SSH key
        dest_key = ssh / "id_ed25519"
        subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(dest_key)],
            check=True,
        )
        dest_key.chmod(0o600)
        pub_text = dest_key.with_suffix(".pub").read_text().strip()

        # GitHub known_hosts
        known_hosts = ssh / "known_hosts"
        subprocess.run(
            ["ssh-keyscan", "github.com"],
            stdout=open(known_hosts, "w"),
            stderr=subprocess.DEVNULL,
            check=True,
        )

        # Git identity
        gitcfg = tmp_path / "gitconfig"
        name = _git_config_global("user.name") or "wageslave"
        email = _git_config_global("user.email") or "wageslave@localhost"
        gitcfg.write_text(
            f"[user]\n    name = {name}\n    email = {email}\n[safe]\n    directory = /workspace\n"
        )
        print(f"git: {name} <{email}>")

        # Encrypt everything
        docker.encrypt_credentials(tmp_path, passphrase)
        print("credentials: encrypted")

    # Auto-unlock for this session
    docker.unlock(passphrase)
    print("session: unlocked")

    # Clean up any old plaintext credentials
    _remove_old_plaintext()

    print()
    print("Add this SSH key to https://github.com/settings/ssh/new")
    print()
    print(f"  {pub_text}")
    print()
    print("Then authenticate GitHub CLI:")
    print()
    print("  wageslave gh auth login")
    print()
    print("  It will show a code and a URL. Press Enter, then open")
    print("  the URL in your browser and enter the code.")


def _remove_old_plaintext() -> None:
    """Remove plaintext credentials from earlier wageslave versions."""
    cfg = config.config_dir()
    for name in ["ssh", "gh"]:
        d = cfg / name
        if d.is_dir():
            shutil.rmtree(d)
    f = cfg / "gitconfig"
    if f.is_file():
        f.unlink()


def _git_config_global(key: str) -> str | None:
    result = subprocess.run(
        ["git", "config", "--global", key],
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None
