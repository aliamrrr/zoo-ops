#!/usr/bin/env sh
# Creates .venv and installs the dependencies. Run from anywhere: ./install.sh
set -eu
cd "$(dirname "$0")"

PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    PYTHON="$candidate"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "Python 3.11 or newer is required: https://www.python.org/downloads/" >&2
  exit 1
fi

[ -d .venv ] || "$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt --quiet

echo
echo "Zoo Ops is ready."
echo "  source .venv/bin/activate"
echo "  python -m zoo test"
echo "  python -m zoo play"
