"""CLI entry point for wageslave."""

import sys

from wageslave import config, docker

USAGE = """\
Usage: wageslave <command> [args...]

Commands:
  setup          First-time setup (SSH key, git config, build image)
  git <args>     Run git with personal credentials
  gh <args>      Run GitHub CLI with personal credentials
  shell          Open an interactive shell in the container

Examples:
  wageslave setup
  wageslave git clone git@github.com:you/repo.git
  wageslave git push origin main
  wageslave gh repo create my-project --private
  wageslave gh pr create --title 'Fix bug'
"""


REMOTE_GIT_COMMANDS = {"push", "pull", "fetch", "clone", "ls-remote"}


def cmd_git(args: list[str]) -> int:
    if args and args[0] not in REMOTE_GIT_COMMANDS:
        print(
            f"wageslave: hint: 'git {args[0]}' is local — use plain git instead",
            file=sys.stderr,
        )
    config.check_setup()
    docker.ensure_image()
    return docker.run(
        ["git", *args],
        ssh_dir=config.ssh_dir(),
        gh_dir=config.gh_dir(),
        gitconfig=config.gitconfig(),
    )


def cmd_gh(args: list[str]) -> int:
    config.check_setup()
    docker.ensure_image()
    # gh auth commands need writable config
    writable = len(args) > 0 and args[0] == "auth"
    if writable:
        config.gh_dir().mkdir(parents=True, exist_ok=True)
    return docker.run(
        ["gh", *args],
        ssh_dir=config.ssh_dir(),
        gh_dir=config.gh_dir(),
        gitconfig=config.gitconfig(),
        writable_gh=writable,
    )


def cmd_shell() -> int:
    config.check_setup()
    docker.ensure_image()
    return docker.run(
        [],
        ssh_dir=config.ssh_dir(),
        gh_dir=config.gh_dir(),
        gitconfig=config.gitconfig(),
        entrypoint="/bin/bash",
    )


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
