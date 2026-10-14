#!/usr/bin/env python3
"""Static safety smoke checks; do not invoke pkexec or change system state."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = [ROOT / "apps/control-center/lunaos-control-center.py", ROOT / "apps/control-center/lunaos-profile-apply", ROOT / "apps/control-center/lunaos-game-run"]
for path in files:
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))
    assert "shell=True" not in source and "bash -c" not in source
helper = files[1].read_text(encoding="utf-8")
for token in ("SYSCTLS", "PROFILE_ID", "os.geteuid() != 0", "firewalld.service"):
    assert token in helper
ui = files[0].read_text(encoding="utf-8")
for token in ("QCheckBox", "pkexec", "Apply profile", "security", "privacy", "performance", "gaming"):
    assert token in ui
print("PASS: UI and privileged-helper smoke checks")
