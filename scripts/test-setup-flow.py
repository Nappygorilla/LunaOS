#!/usr/bin/env python3
"""Static checks for skip/guest account policy; performs no privileged operations."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
installer = ROOT / "apps/setup/lunaos-installer-setup.py"
firstboot = ROOT / "apps/setup/lunaos-firstboot-setup.py"
helper = ROOT / "apps/setup/lunaos-setup-user-helper"
target = ROOT / "scripts/install-target-firstboot.sh"
live_setup = ROOT / "packaging/archiso/overlay/airootfs/usr/local/bin/lunaos-live-setup"
sudoers = ROOT / "packaging/archiso/overlay/airootfs/etc/sudoers.d/10-lunaos-live"
policy = ROOT / "packaging/archiso/overlay/airootfs/usr/share/polkit-1/actions/org.lunaos.setup-user.policy"

for path in (installer, firstboot, helper):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    source = path.read_text(encoding="utf-8")
    assert "shell=True" not in source and "os.system(" not in source

install_text = installer.read_text(encoding="utf-8")
assert '"username": "luna-guest", "sudo": False' in install_text
assert '"sudo": admin.isChecked()' in install_text
assert '"disk_config"' not in install_text and '"harddrives"' not in install_text

helper_text = helper.read_text(encoding="utf-8")
assert "existing_personal_users" in helper_text
assert "LOCK_FILE.exists()" in helper_text
assert "usermod" not in helper_text and "wheel" not in helper_text
assert "sudoers" not in helper_text

target_text = target.read_text(encoding="utf-8")
assert 'case "$MODE" in personal|guest)' in target_text
assert 'if [[ "$MODE" == "guest" ]]' in target_text
assert 'id -nG luna-guest' in target_text
assert "20-lunaos-guest-autologin.conf" in target_text

assert "wheel" not in live_setup.read_text(encoding="utf-8")
sudoers_text = sudoers.read_text(encoding="utf-8")
assert "NOPASSWD: /usr/bin/archinstall" in sudoers_text
assert "NOPASSWD: ALL" not in sudoers_text
assert "allow_active>yes</allow_active>" in policy.read_text(encoding="utf-8")

print("PASS: skip settings, guest restrictions, non-admin account helper, and no automatic admin grant")
