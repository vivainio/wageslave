"""Container management for wageslave (Podman)."""

import hashlib
import secrets
import subprocess
import sys
import tempfile
from importlib.resources import files
from pathlib import Path

from wageslave import config

IMAGE_NAME = "wageslave"
RUNTIME = "podman"

SESSION_KEY_PATH = Path("/tmp/wageslave.key")


def _image_key_path() -> Path:
    return config.config_dir() / "image.key"


def _combined_key() -> str:
    """Derive the encryption key from image key + session key."""
    image_key = _image_key_path().read_text()
    if not SESSION_KEY_PATH.exists():
        raise SystemExit("wageslave: locked — run 'wageslave unlock' first")
    session_key = SESSION_KEY_PATH.read_text()
    return hashlib.sha256((image_key + session_key).encode()).hexdigest()


def image_exists() -> bool:
    result = subprocess.run(
        [RUNTIME, "image", "inspect", IMAGE_NAME],
        capture_output=True,
    )
    return result.returncode == 0


def build_image() -> None:
    """Build image with a random encryption key baked in."""
    key = secrets.token_hex(32)
    key_path = _image_key_path()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(key)
    key_path.chmod(0o600)

    dockerfile = files("wageslave").joinpath("Dockerfile")
    pkg_dir = str(dockerfile.parent)

    with tempfile.TemporaryDirectory(prefix="wageslave-build-") as tmp:
        tmp_path = Path(tmp)
        df = tmp_path / "Dockerfile"
        df.write_text(
            (Path(pkg_dir) / "Dockerfile").read_text()
            + f'\nRUN mkdir -p /etc/wageslave && echo -n "{key}" > /etc/wageslave/key'
            + "\nRUN chmod 644 /etc/wageslave/key\n"
        )
        subprocess.run(
            [RUNTIME, "build", "-t", IMAGE_NAME, "-f", str(df), pkg_dir],
            check=True,
        )


def ensure_image() -> None:
    if not image_exists():
        print("wageslave: building container image...", file=sys.stderr)
        build_image()


def encrypt_credentials(source_dir: Path, passphrase: str) -> None:
    """Tar and encrypt credentials using image key + passphrase."""
    image_key = _image_key_path().read_text()
    session_key = hashlib.sha256(passphrase.encode()).hexdigest()
    combined = hashlib.sha256((image_key + session_key).encode()).hexdigest()

    enc_path = config.config_dir() / "credentials.enc"
    tar = subprocess.run(
        ["tar", "cf", "-", "-C", str(source_dir), "."],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-pbkdf2",
            "-pass",
            f"pass:{combined}",
            "-out",
            str(enc_path),
        ],
        input=tar.stdout,
        check=True,
    )
    enc_path.chmod(0o600)


def decrypt_credentials(dest_dir: Path) -> None:
    """Decrypt credentials.enc using combined key."""
    combined = _combined_key()
    enc_path = config.config_dir() / "credentials.enc"
    if not enc_path.exists():
        raise SystemExit("wageslave: no credentials found — run 'wageslave setup' first")

    dec = subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-d",
            "-pbkdf2",
            "-pass",
            f"pass:{combined}",
            "-in",
            str(enc_path),
        ],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["tar", "xf", "-", "-C", str(dest_dir)],
        input=dec.stdout,
        check=True,
    )


def unlock(passphrase: str) -> None:
    """Write session key derived from passphrase to /tmp."""
    session_key = hashlib.sha256(passphrase.encode()).hexdigest()
    SESSION_KEY_PATH.write_text(session_key)
    SESSION_KEY_PATH.chmod(0o600)


def lock() -> None:
    """Remove session key."""
    if SESSION_KEY_PATH.exists():
        SESSION_KEY_PATH.unlink()


def is_unlocked() -> bool:
    return SESSION_KEY_PATH.exists()


def credentials_exist() -> bool:
    return (config.config_dir() / "credentials.enc").exists()


def run(
    command: list[str],
    *,
    workdir: Path | None = None,
    interactive: bool = True,
    entrypoint: str | None = None,
) -> int:
    """Run a command inside the wageslave container."""
    if not is_unlocked():
        raise SystemExit("wageslave: locked — run 'wageslave unlock' first")

    work = workdir or Path.cwd()
    home = "/home/user"
    ssh_cmd = (
        f"ssh -i {home}/.wageslave-creds/ssh/id_ed25519 -o IdentitiesOnly=yes"
        f" -o UserKnownHostsFile={home}/.wageslave-creds/ssh/known_hosts"
    )
    enc_path = config.config_dir() / "credentials.enc"

    args: list[str] = [
        RUNTIME,
        "run",
        "--rm",
        "--userns=keep-id",
        "--env",
        f"HOME={home}",
        "--env",
        f"GIT_SSH_COMMAND={ssh_cmd}",
        "--env",
        "BROWSER=echo",
    ]

    if interactive and sys.stdin.isatty():
        args += ["-it"]

    # Mount encrypted credentials + session key
    args += ["-v", f"{enc_path}:/creds/credentials.enc:ro"]
    args += ["-v", f"{SESSION_KEY_PATH}:/creds/session.key:ro"]
    args += ["-v", f"{work}:/workspace"]
    args += ["--workdir", "/workspace"]

    if entrypoint is not None:
        args += ["--entrypoint", entrypoint]

    args.append(IMAGE_NAME)
    args.extend(command)

    result = subprocess.run(args)
    return result.returncode


def run_with_writable_creds(command: list[str], interactive: bool = True) -> int:
    """Run a command that needs to write credentials (e.g. gh auth login)."""
    with tempfile.TemporaryDirectory(prefix="wageslave-creds-") as tmp:
        tmp_path = Path(tmp)
        decrypt_credentials(tmp_path)

        home = "/home/user"
        ssh_dir = tmp_path / "ssh"
        gh_dir = tmp_path / "gh"
        gitconfig = tmp_path / "gitconfig"
        gh_dir.mkdir(exist_ok=True)

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
            "--env",
            "BROWSER=echo",
            "--entrypoint",
            "",
        ]

        if interactive and sys.stdin.isatty():
            args += ["-it"]

        args += ["-v", f"{ssh_dir}:{home}/.ssh:ro"]
        args += ["-v", f"{gh_dir}:{home}/.config/gh:rw"]
        if gitconfig.exists():
            args += ["-v", f"{gitconfig}:{home}/.gitconfig:rw"]
        args += ["--workdir", "/workspace"]

        args.append(IMAGE_NAME)
        args.extend(command)

        result = subprocess.run(args)

        # Re-encrypt with the current combined key
        _encrypt_with_combined_key(tmp_path)

        return result.returncode


def _encrypt_with_combined_key(source_dir: Path) -> None:
    """Re-encrypt credentials using the current combined key (both parts available)."""
    combined = _combined_key()
    enc_path = config.config_dir() / "credentials.enc"
    tar = subprocess.run(
        ["tar", "cf", "-", "-C", str(source_dir), "."],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "openssl",
            "enc",
            "-aes-256-cbc",
            "-pbkdf2",
            "-pass",
            f"pass:{combined}",
            "-out",
            str(enc_path),
        ],
        input=tar.stdout,
        check=True,
    )
    enc_path.chmod(0o600)
