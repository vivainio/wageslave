#!/bin/bash
# Decrypt credentials and run the given command.
# The encryption key is baked into the image at /etc/wageslave/key.
# The encrypted tar is mounted at /creds/credentials.enc.
set -eu

HOME_DIR="/home/user"
KEY_FILE="/etc/wageslave/key"
CREDS_ENC="/creds/credentials.enc"
CREDS_DIR="$HOME_DIR/.wageslave-creds"

mkdir -p "$CREDS_DIR"

if [ -f "$CREDS_ENC" ] && [ -f "$KEY_FILE" ]; then
    openssl enc -aes-256-cbc -d -pbkdf2 \
        -in "$CREDS_ENC" -pass "file:$KEY_FILE" \
        | tar xf - -C "$CREDS_DIR" 2>/dev/null

    # Link credentials to expected locations
    mkdir -p "$HOME_DIR/.ssh" "$HOME_DIR/.config"
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
