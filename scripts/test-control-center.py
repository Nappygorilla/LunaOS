#!/usr/bin/env python3
"""Static safety checks for Control Center features; never run privileged actions."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ui_path = ROOT / "apps/control-center/lunaos-control-center.py"
tools_path = ROOT / "apps/control-center/lunaos-system-tools"
profile_path = ROOT / "apps/control-center/lunaos-profile-apply"
for path in (ui_path, tools_path, profile_path):
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))
    assert "shell=True" not in source and "bash -c" not in source and "os.system(" not in source

tools = tools_path.read_text(encoding="utf-8")
for token in (
    "BUNDLES", "POWER_MODES", "SERVICE_ALLOWLIST", "os.geteuid()", "pacman",
    "timeshift", "pwmconfig", "fancontrol.service", "power-profiles-daemon.service",
    "snapshot-create", "snapshot-list", "root-equivalent docker group",
):
    assert token in tools, "missing expected safety/feature guard: " + token
assert "subprocess.run(argv" in tools
assert re.search(r"pacman.*-Syu.*--needed.*--noconfirm", tools, re.S)
assert "os.execv(binary, [binary])" in tools

ui = ui_path.read_text(encoding="utf-8")
for token in (
    "Power modes", "Power saver", "performance", "Cooling and fan control",
    "Guided fan-curve setup", "System snapshots", "snapshot-create",
    "Open Timeshift", "Developer tools", "Install selected", "docker group",
    "pkexec", "Profiles",
):
    assert token.lower() in ui.lower(), "missing Control Center feature: " + token

policy = ROOT / "packaging/archiso/overlay/airootfs/usr/share/polkit-1/actions/org.lunaos.systemtools.policy"
policy_text = policy.read_text(encoding="utf-8")
assert "org.lunaos.systemtools" in policy_text
assert "/usr/lib/lunaos/lunaos-system-tools" in policy_text
assert "<allow_any>no</allow_any>" in policy_text
assert "NOPASSWD: ALL" not in (ROOT / "packaging/archiso/overlay/airootfs/etc/sudoers.d/10-lunaos-live").read_text(encoding="utf-8")

print("PASS: Control Center power, fan, snapshots, developer bundles, and privilege smoke checks")
