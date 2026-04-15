#!/bin/sh
set -e

if [ "$1" = 'mcp' ]; then
    exec bitpanda-mcp
fi

exec "$@"
