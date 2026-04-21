#!/bin/sh
set -eu

if [ "${1:-}" = 'mcp' ]; then
    exec bitpanda-mcp
fi

exec "$@"
