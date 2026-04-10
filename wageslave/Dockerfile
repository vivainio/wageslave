FROM alpine:3.21

RUN apk add --no-cache \
    git \
    openssh-client \
    github-cli \
    bash \
    && mkdir -p /root/.ssh \
    && ssh-keyscan github.com >> /root/.ssh/known_hosts 2>/dev/null \
    && git config --global --add safe.directory /workspace

# Git defaults — overridable via env vars
ENV GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519 -o IdentitiesOnly=yes"

WORKDIR /workspace
