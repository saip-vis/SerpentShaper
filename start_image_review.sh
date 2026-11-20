#!/bin/sh
set -eu
cd "$(dirname "$0")"
if python3 -c 'import PIL' >/dev/null 2>&1; then
  exec python3 ImageReview.py "$@"
fi
review_python="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [ -x "$review_python" ] && "$review_python" -c 'import PIL' >/dev/null 2>&1; then
  exec "$review_python" ImageReview.py "$@"
fi
echo 'Pillow is required for review previews. Install with: python3 -m pip install Pillow' >&2
exit 1
