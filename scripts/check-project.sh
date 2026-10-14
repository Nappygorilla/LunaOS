#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
bash -n build-lunaos.sh
find packaging scripts -type f \( -name '*.sh' -o -path '*/usr/local/bin/lunaos-*' \) -print0 | while IFS= read -r -d '' file; do bash -n "$file"; done
python -m py_compile apps/control-center/lunaos-control-center.py apps/control-center/lunaos-profile-apply apps/control-center/lunaos-game-run scripts/test-profiles.py scripts/test-control-center.py
python scripts/test-profiles.py
python scripts/test-control-center.py
test -s assets/lunaos-wallpaper.svg
test -s config/modules.toml
echo "Project checks passed."
