"""CLI entry point for wageslave."""

import re
import subprocess
import sys
from pathlib import Path

from wageslave import config, docker

USAGE = """\
Usage: wageslave <command> [args...]

Commands:
  setup          First-time setup (SSH key, git config, build image)
  pull [args]    Git pull via HTTPS (no container needed)
  fetch [args]   Git fetch via HTTPS (no container needed)
  push [args]    Git push via container (needs SSH credentials)
  git <args>     Run any git command in the container
  gh <args>      Run GitHub CLI in the container
  shell          Open an interactive shell in the container
  install-skill  Install Claude Code skill to ~/.claude/skills/

Examples:
  wageslave setup
  wageslave push
  wageslave pull
  wageslave gh repo create my-project --private
  wageslave gh pr create --title 'Fix bug'
"""


REMOTE_GIT_COMMANDS = {"push", "pull", "fetch", "clone", "ls-remote"}


def _ssh_remote_to_https(remote: str = "origin") -> str | None:
    """Convert an SSH remote URL to HTTPS. Returns None if not an SSH URL."""
    result = subprocess.run(
        ["git", "remote", "get-url", remote],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    url = result.stdout.strip()
    # git@github.com:user/repo.git -> https://github.com/user/repo.git
    m = re.match(r"git@([^:]+):(.+)", url)
    if m:
        return f"https://{m.group(1)}/{m.group(2)}"
    return None


def cmd_pull_or_fetch(git_cmd: str, args: list[str]) -> int:
    """Run git pull/fetch using HTTPS URL directly on host (no container)."""
    https_url = _ssh_remote_to_https()
    if https_url:
        return subprocess.run(["git", git_cmd, https_url, *args]).returncode
    # Fallback to container if not an SSH remote
    return cmd_git([git_cmd, *args])


def cmd_push(args: list[str]) -> int:
    config.check_setup()
    docker.ensure_image()
    return docker.run(["git", "push", *args])


def cmd_git(args: list[str]) -> int:
    if args and args[0] not in REMOTE_GIT_COMMANDS:
        print(
            f"wageslave: hint: 'git {args[0]}' is local — use plain git instead",
            file=sys.stderr,
        )
    config.check_setup()
    docker.ensure_image()
    return docker.run(["git", *args])


def cmd_gh(args: list[str]) -> int:
    config.check_setup()
    docker.ensure_image()
    is_auth = len(args) > 0 and args[0] == "auth"
    gh_args = list(args)
    if len(args) >= 2 and args[0] == "auth" and args[1] == "login":
        if "--git-protocol" not in args:
            gh_args += ["--git-protocol", "ssh"]
        if "--skip-ssh-key" not in args:
            gh_args += ["--skip-ssh-key"]
    if is_auth:
        return docker.run_with_writable_creds(["gh", *gh_args])
    return docker.run(["gh", *gh_args])


def cmd_shell() -> int:
    config.check_setup()
    docker.ensure_image()
    return docker.run([], entrypoint="/bin/bash")


def cmd_install_skill() -> None:
    import shutil
    from importlib.resources import files

    src = files("wageslave").joinpath("skill")
    dest = Path.home() / ".claude" / "skills" / "wageslave"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(str(src), dest)
    print(f"Installed skill to {dest}")


def cmd_setup(args: list[str]) -> None:
    from wageslave.setup import run_setup

    host = None
    if len(args) >= 2 and args[0] == "--host":
        host = args[1]
    elif len(args) >= 1 and args[0].startswith("--host="):
        host = args[0].split("=", 1)[1]

    run_setup(host=host)


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    command, rest = args[0], args[1:]

    if command == "setup":
        cmd_setup(rest)
    elif command == "install-skill":
        cmd_install_skill()
    elif command == "pull":
        sys.exit(cmd_pull_or_fetch("pull", rest))
    elif command == "fetch":
        sys.exit(cmd_pull_or_fetch("fetch", rest))
    elif command == "push":
        sys.exit(cmd_push(rest))
    elif command == "git":
        sys.exit(cmd_git(rest))
    elif command == "gh":
        sys.exit(cmd_gh(rest))
    elif command == "shell":
        sys.exit(cmd_shell())
    else:
        print(f"wageslave: unknown command: {command}", file=sys.stderr)
        print("Try: setup, git, gh, shell", file=sys.stderr)
        sys.exit(1)
