"""Configuration paths for wageslave."""

import os
from pathlib import Path


def config_dir() -> Path:
    return Path(os.environ.get("WAGESLAVE_HOME", Path.home() / ".config" / "wageslave"))


def ssh_dir() -> Path:
    return config_dir() / "ssh"


def gh_dir() -> Path:
    return config_dir() / "gh"


def gitconfig() -> Path:
    return config_dir() / "gitconfig"


def check_setup() -> None:
    enc = config_dir() / "credentials.enc"
    if not enc.exists():
        raise SystemExit("wageslave: not configured — run 'wageslave setup' first")
