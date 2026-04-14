FROM python:3.13-slim

ARG USER_NAME="bitpanda_mcp"
ARG USER_HOME="/usr/src/app"
ARG USER_ID=1000

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${USER_HOME}

RUN groupadd -g ${USER_ID} ${USER_NAME} && \
    useradd -l -u ${USER_ID} -g ${USER_ID} --create-home --home-dir ${USER_HOME} --shell /bin/bash ${USER_NAME}

COPY --chown=${USER_NAME}:${USER_NAME} pyproject.toml uv.lock .python-version ./

RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=${USER_NAME}:${USER_NAME} . ./

RUN uv sync --frozen --no-dev

ENV FASTMCP_TRANSPORT=streamable-http
ENV FASTMCP_HOST=0.0.0.0
ENV FASTMCP_PORT=8000
ENV FASTMCP_STATELESS_HTTP=true

EXPOSE 8000

USER ${USER_NAME}

ENTRYPOINT ["ci/docker/entrypoint.sh"]
CMD ["mcp"]
