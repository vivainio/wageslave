FROM alpine:3.21

RUN apk add --no-cache \
    git \
    openssh-client \
    github-cli \
    bash \
    openssl

RUN mkdir -p /home/user/.ssh /home/user/.config/gh /home/user/.wageslave-creds \
    && chmod 777 /home/user /home/user/.ssh /home/user/.config /home/user/.config/gh /home/user/.wageslave-creds

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
