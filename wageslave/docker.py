"""Container management for wageslave (Podman)."""

import subprocess
import sys
from importlib.resources import files
from pathlib import Path

IMAGE_NAME = "wageslave"
RUNTIME = "podman"


def image_exists() -> bool:
    result = subprocess.run(
        [RUNTIME, "image", "inspect", IMAGE_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def build_image() -> None:
    dockerfile = files("wageslave").joinpath("Dockerfile")
    subprocess.run(
        [RUNTIME, "build", "-t", IMAGE_NAME, "-f", str(dockerfile), str(dockerfile.parent)],
        check=True,
    )


def ensure_image() -> None:
    if not image_exists():
        print("wageslave: building container image...", file=sys.stderr)
        build_image()


def run(
    command: list[str],
    *,
    ssh_dir: Path,
    gh_dir: Path | None = None,
    gitconfig: Path | None = None,
    workdir: Path | None = None,
    writable_gh: bool = False,
    writable_gitconfig: bool = False,
    interactive: bool = True,
    entrypoint: str | None = None,
) -> int:
    """Run a command inside the wageslave container."""
    work = workdir or Path.cwd()
    # --userns=keep-id maps host uid into container so mounted files are owned correctly.
    # We set HOME and GIT_SSH_COMMAND explicitly since the uid has no passwd entry.
    home = "/home/user"
    ssh_cmd = (
        f"ssh -i {home}/.ssh/id_ed25519 -o IdentitiesOnly=yes"
        f" -o UserKnownHostsFile={home}/.ssh/known_hosts"
    )
    args: list[str] = [
        RUNTIME,
        "run",
        "--rm",
        "--userns=keep-id",
        "--env",
        f"HOME={home}",
        "--env",
        f"GIT_SSH_COMMAND={ssh_cmd}",
    ]

    if interactive and sys.stdin.isatty():
        args += ["-it"]

    # Mounts
    args += ["-v", f"{ssh_dir}:{home}/.ssh:ro"]
    args += ["-v", f"{work}:/workspace"]

    if gh_dir and gh_dir.exists():
        mode = "rw" if writable_gh else "ro"
        args += ["-v", f"{gh_dir}:{home}/.config/gh:{mode}"]

    if gitconfig and gitconfig.exists():
        mode = "rw" if writable_gitconfig else "ro"
        args += ["-v", f"{gitconfig}:{home}/.gitconfig:{mode}"]

    args += ["--workdir", "/workspace"]

    if entrypoint is not None:
        args += ["--entrypoint", entrypoint]

    args.append(IMAGE_NAME)
    args.extend(command)

    result = subprocess.run(args)
    return result.returncode
