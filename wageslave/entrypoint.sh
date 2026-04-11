#!/bin/bash
# Decrypt credentials and run the given command.
# Two key parts are needed:
#   /etc/wageslave/key  — baked into the image at build time
#   /creds/session.key  — mounted at runtime (from unlock)
# The combined key is SHA256(image_key + session_key).
set -eu

HOME_DIR="/home/user"
IMAGE_KEY="/etc/wageslave/key"
SESSION_KEY="/creds/session.key"
CREDS_ENC="/creds/credentials.enc"
CREDS_DIR="$HOME_DIR/.wageslave-creds"

mkdir -p "$CREDS_DIR"

if [ -f "$CREDS_ENC" ] && [ -f "$IMAGE_KEY" ] && [ -f "$SESSION_KEY" ]; then
    # Combine both key parts
    COMBINED=$(cat "$IMAGE_KEY" "$SESSION_KEY" | openssl dgst -sha256 -r | cut -d' ' -f1)

    openssl enc -aes-256-cbc -d -pbkdf2 \
        -in "$CREDS_ENC" -pass "pass:$COMBINED" \
        | tar xf - -C "$CREDS_DIR" 2>/dev/null

    # Link credentials to expected locations
    if [ -d "$CREDS_DIR/ssh" ]; then
        rm -rf "$HOME_DIR/.ssh"
        ln -sf "$CREDS_DIR/ssh" "$HOME_DIR/.ssh"
    fi
    if [ -d "$CREDS_DIR/gh" ]; then
        mkdir -p "$HOME_DIR/.config"
        rm -rf "$HOME_DIR/.config/gh"
        ln -sf "$CREDS_DIR/gh" "$HOME_DIR/.config/gh"
    fi
    if [ -f "$CREDS_DIR/gitconfig" ]; then
        ln -sf "$CREDS_DIR/gitconfig" "$HOME_DIR/.gitconfig"
    fi
fi

exec "$@"
