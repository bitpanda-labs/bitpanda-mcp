# --- builder ---
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/usr/src/app/.venv

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
COPY README.md LICENSE ./
RUN uv sync --frozen --no-dev

# --- runtime ---
FROM python:3.14-slim

LABEL org.opencontainers.image.title="bitpanda-mcp" \
      org.opencontainers.image.description="MCP server for Bitpanda" \
      org.opencontainers.image.source="https://github.com/bitpanda-labs/bitpanda-mcp" \
      org.opencontainers.image.licenses="Apache-2.0"

ARG USER_NAME="bitpanda_mcp"
ARG USER_HOME="/usr/src/app"
ARG USER_ID=1000

ENV PYTHONUNBUFFERED=1

WORKDIR ${USER_HOME}

RUN groupadd -g ${USER_ID} ${USER_NAME} && \
    useradd -l -u ${USER_ID} -g ${USER_ID} --create-home --home-dir ${USER_HOME} --shell /bin/bash ${USER_NAME}

COPY --from=builder --chown=${USER_NAME}:${USER_NAME} /usr/src/app/.venv ${USER_HOME}/.venv
COPY --chown=${USER_NAME}:${USER_NAME} ci/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PATH="${USER_HOME}/.venv/bin:${PATH}"
ENV FASTMCP_TRANSPORT=streamable-http
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8000
ENV FASTMCP_STATELESS_HTTP=true

EXPOSE 8000

USER ${USER_NAME}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["mcp"]
