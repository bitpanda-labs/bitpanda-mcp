#!/usr/bin/env bash
set -e

if [ "$1" = 'mcp' ]; then
    exec uv run bitpanda-mcp
fi

exec "$@"
