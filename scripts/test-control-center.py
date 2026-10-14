#!/usr/bin/env python3
"""Static safety checks; do not invoke pkexec or change system state."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
file_map = {
    "ui": ROOT / "apps/control-center/lunaos-control-center.py",
    "profile": ROOT / "apps/control-center/lunaos-profile-apply",
    "tools": ROOT / "apps/control-center/lunaos-system-tools",
    "agent": ROOT / "apps/control-center/lunaos-update-agent.py",
    "runner": ROOT / "apps/control-center/lunaos-game-run",
}
for path in file_map.values():
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))
    assert "shell=True" not in source and "bash -c" not in source and "os.system(" not in source

tools = file_map["tools"].read_text(encoding="utf-8")
for token in (
    "BUNDLES", "POWER_MODES", "SERVICE_ALLOWLIST", "os.geteuid()", "pacman",
    "timeshift", "pwmconfig", "fancontrol.service", "power-profiles-daemon.service",
    "snapshot-create", "snapshot-list", "checkupdates", "updates-details", "updates-install",
    "download-schedule", "reboot-schedule", "SECURITY_CHANGE_RE", "CORE_SYSTEM_RE",
    "Persistent=false", "update-download-state.json",
):
    assert token in tools, "missing helper safety/feature token: " + token
assert "subprocess.run(argv" in tools
assert re.search(r"pacman.*-Syu.*--needed.*--noconfirm", tools, re.S)
assert "os.execv(binary, [binary])" in tools

ui = file_map["ui"].read_text(encoding="utf-8")
for token in (
    "Power modes", "Cooling and fan control", "System snapshots", "Personal file backups", "Quick launch", "Welcome to LunaOS", "Developer tools",
    "System updates", "Install all updates", "Important update compatibility warning",
    "QProgressBar", "SUPPORT_ISSUES_URL", "notifications_enabled", "download-schedule",
    "reboot-schedule", "changelog", "schedule_install_at",
):
    assert token.lower() in ui.lower(), "missing Control Center feature: " + token

agent = file_map["agent"].read_text(encoding="utf-8")
for token in (
    "notifications_enabled", "schedule_install_at", "showMessage",
    "update-download-state.json", "lunaos-control-center", "--scheduled-install",
):
    assert token in agent, "missing update-agent behavior: " + token

policy = ROOT / "packaging/archiso/overlay/airootfs/usr/share/polkit-1/actions/org.lunaos.systemtools.policy"
policy_text = policy.read_text(encoding="utf-8")
assert "org.lunaos.systemtools" in policy_text
assert "/usr/lib/lunaos/lunaos-system-tools" in policy_text
assert "<allow_any>no</allow_any>" in policy_text
sudoers = (ROOT / "packaging/archiso/overlay/airootfs/etc/sudoers.d/10-lunaos-live").read_text(encoding="utf-8")
assert "NOPASSWD: ALL" not in sudoers

autostart = ROOT / "packaging/archiso/overlay/airootfs/etc/xdg/autostart/lunaos-update-agent.desktop"
assert "lunaos-update-agent" in autostart.read_text(encoding="utf-8")
assert "pacman-contrib" in (ROOT / "config/packages/base.packages").read_text(encoding="utf-8")

print("PASS: Control Center feature, update safety, schedule, and notification smoke checks")

# Personal backup must reject path traversal and special files and restore into a new folder.
assert "PurePosixPath(member.name).is_absolute()" in file_map["ui"].read_text(encoding="utf-8")
assert "target.open(\"xb\")" in file_map["ui"].read_text(encoding="utf-8")
assert "archive.extractfile(member)" in file_map["ui"].read_text(encoding="utf-8")
