#!/bin/sh
set -eu
cd "$(dirname "$0")"
if python3 -c 'import pypdf' >/dev/null 2>&1; then
  exec python3 StudyServer.py "$@"
fi
study_python="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [ -x "$study_python" ] && "$study_python" -c 'import pypdf' >/dev/null 2>&1; then
  exec "$study_python" StudyServer.py "$@"
fi
echo 'PDF uploads require pypdf. Install it with: python3 -m pip install pypdf' >&2
exit 1
