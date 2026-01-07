#!/usr/bin/env sh

MARKER="${1:-unit}"

if [ "$MARKER" = "all" ]; then
  python -m pytest
  exit $?
fi

python -m pytest -m "$MARKER"
