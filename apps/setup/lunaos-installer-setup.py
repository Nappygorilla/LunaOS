#!/usr/bin/env python3
"""Optional LunaOS installer setup. Disk selection always remains manual."""
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout

REVISION_FILE = Path("/usr/share/lunaos/source-revision")
MODULES_FILE = Path("/usr/share/lunaos/build-modules.json")
PACKAGE_DIR = Path("/usr/share/lunaos/package-modules")
WORK_DIR = Path("/run/lunaos-installer")
PROFILE_CHOICES = {
    "Balanced": "balanced", "Gaming": "gaming", "Coding": "coding",
    "Creator": "creator", "Privacy-first": "privacy",
    "Secure workstation": "secure", "Battery saver": "battery-saver",
}
MODULE_IDS = {"security", "privacy", "performance", "gaming", "coding", "creator"}


def password_hash(password: str) -> str:
    result = subprocess.run(
        ["/usr/bin/openssl", "passwd", "-6", "-stdin"],
        input=(password + "\n").encode(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=10,
    )
    value = result.stdout.decode("ascii", "strict").strip()
    if result.returncode != 0 or not value.startswith("$6$"):
        raise RuntimeError("Could not securely hash the account credential.")
    return value


def package_modules():
    try:
        manifest = json.loads(MODULES_FILE.read_text(encoding="utf-8"))
        included = set(manifest.get("included_modules", []))
    except (OSError, ValueError):
        included = {"base", "desktop"}
    package_names = set()
    for module in sorted(included):
        if module not in ({"base", "desktop"} | MODULE_IDS):
            continue
        path = PACKAGE_DIR / (module + ".packages")
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            name = line.strip()
            if name and not name.startswith("#"):
                package_names.add(name)
    package_names.discard("archinstall")
    return sorted(package_names), sorted(included)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LunaOS Setup")
    app.setStyleSheet("""
      QWidget { background:#0b1020; color:#edf3ff; font:13px 'Segoe UI'; }
      QLabel#heading { font-size:24px; font-weight:700; }
      QLabel#muted { color:#a7b8d3; }
      QGroupBox { border:1px solid #283b56; border-radius:12px; margin-top:10px; padding:12px; font-weight:600; }
      QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; }
      QLineEdit, QComboBox { padding:9px; border:1px solid #304968; border-radius:7px; background:#080d19; }
      QCheckBox { padding:6px; }
      QPushButton { padding:10px 15px; border-radius:8px; }
    """)
    dialog = QDialog()
    dialog.setWindowTitle("Welcome to LunaOS")
    dialog.setMinimumWidth(620)
    outer = QVBoxLayout(dialog)
    title = QLabel("Set up LunaOS your way")
    title.setObjectName("heading")
    outer.addWidget(title)
    intro = QLabel("You can skip personalization. LunaOS will still ask you to select the target disk and confirm installation. No drive is selected or erased automatically.")
    intro.setWordWrap(True)
    intro.setObjectName("muted")
    outer.addWidget(intro)

    setting_group = QGroupBox("Optional desktop settings")
    setting_layout = QVBoxLayout(setting_group)
    use_settings = QCheckBox("Use LunaOS desktop defaults (dark theme and Luna wallpaper)")
    use_settings.setChecked(True)
    setting_layout.addWidget(use_settings)
    profile = QComboBox()
    profile.addItems(PROFILE_CHOICES.keys())
    profile.setCurrentText("Balanced")
    setting_form = QFormLayout()
    setting_form.addRow("Starting Control Center profile", profile)
    setting_layout.addLayout(setting_form)
    note = QLabel("Uncheck this to skip personalization; you can change desktop appearance later.")
    note.setObjectName("muted")
    note.setWordWrap(True)
    setting_layout.addWidget(note)
    outer.addWidget(setting_group)

    account_group = QGroupBox("Optional personal account")
    account_layout = QVBoxLayout(account_group)
    create_account = QCheckBox("Create my personal account during installation")
    create_account.setChecked(True)
    account_layout.addWidget(create_account)
    account_form = QFormLayout()
    username = QLineEdit()
    username.setPlaceholderText("e.g. lunauser")
    password = QLineEdit()
    password.setEchoMode(QLineEdit.EchoMode.Password)
    password.setPlaceholderText("Use a strong password")
    confirm = QLineEdit()
    confirm.setEchoMode(QLineEdit.EchoMode.Password)
    confirm.setPlaceholderText("Re-enter password")
    admin = QCheckBox("Grant this account administrator permissions")
    admin.setChecked(True)
    admin.setToolTip("When checked, this account can administer the installed system. Uncheck it for a standard, non-admin account.")
    account_form.addRow("Username", username)
    account_form.addRow("Password", password)
    account_form.addRow("Confirm password", confirm)
    account_layout.addLayout(account_form)
    account_layout.addWidget(admin)
    restriction_note = QLabel("If you skip account creation, LunaOS installs a restricted luna-guest account for desktop access. It is not in the administrator group and cannot use sudo. You can create a personal account later from the first-run setup screen.")
    restriction_note.setWordWrap(True)
    restriction_note.setObjectName("muted")
    account_layout.addWidget(restriction_note)
    outer.addWidget(account_group)

    def set_enabled(enabled):
        for widget in (username, password, confirm, admin):
            widget.setEnabled(enabled)
    create_account.toggled.connect(set_enabled)
    set_enabled(True)
    buttons = QDialogButtonBox()
    buttons.addButton("Continue to disk selection", QDialogButtonBox.ButtonRole.AcceptRole)
    buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
    outer.addWidget(buttons)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return 0

    wants_account = create_account.isChecked()
    account_name = username.text().strip()
    account_password = password.text()
    if wants_account:
        if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,30}\$?", account_name):
            QMessageBox.warning(dialog, "Check username", "Use 1–31 lowercase letters, digits, underscores, or hyphens; the first character must be a letter or underscore.")
            return main()
        if account_name in {"root", "nobody", "luna", "luna-guest", "bin", "daemon", "adm", "mail", "ftp", "http"}:
            QMessageBox.warning(dialog, "Unavailable username", "That username is reserved. Choose another name.")
            return main()
        if len(account_password) < 12:
            QMessageBox.warning(dialog, "Password too short", "Use at least 12 characters for the account password.")
            return main()
        if "\n" in account_password or ":" in account_password or account_password != confirm.text():
            QMessageBox.warning(dialog, "Check password", "The passwords must match and cannot contain a colon or newline.")
            return main()

    try:
        revision = REVISION_FILE.read_text(encoding="ascii").strip()
    except OSError:
        QMessageBox.critical(dialog, "Installer source missing", "The LunaOS source revision file is missing. Rebuild the ISO from a complete repository checkout.")
        return 1
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        QMessageBox.critical(dialog, "Invalid source revision", "The pinned LunaOS source revision is invalid.")
        return 1
    packages, included = package_modules()
    if not packages:
        QMessageBox.critical(dialog, "Package modules missing", "No package modules were found in the live image.")
        return 1

    WORK_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(WORK_DIR, 0o700)
    profile_id = PROFILE_CHOICES[profile.currentText()] if use_settings.isChecked() else "balanced"
    custom_mode = "personal" if wants_account else "guest"
    apply_settings = "yes" if use_settings.isChecked() else "no"
    install_command = (
        "curl -fsSL --proto '=https' --tlsv1.2 "
        f"https://raw.githubusercontent.com/Nappygorilla/LunaOS/{revision}/scripts/install-target-firstboot.sh "
        "-o /tmp/lunaos-install-target-firstboot.sh && "
        f"/bin/bash /tmp/lunaos-install-target-firstboot.sh {custom_mode} {apply_settings} {profile_id} {revision}"
    )
    config = {
        "archinstall-language": "English",
        "audio_config": {"audio": "pipewire"},
        "bootloader_config": {"bootloader": "Systemd-boot", "uki": False, "removable": False},
        "hostname": "lunaos",
        "kernels": ["linux"],
        "locale_config": {"kb_layout": "us", "sys_enc": "UTF-8", "sys_lang": "en_US.UTF-8"},
        "network_config": {"type": "nm"},
        "ntp": True,
        "packages": packages,
        "profile_config": {"gfx_driver": "All open-source", "greeter": "sddm", "profile": {"details": ["KDE Plasma"], "main": "Desktop"}},
        "script": "guided",
        "services": ["NetworkManager", "bluetooth", "sddm"],
        "swap": {"enabled": True, "algorithm": "zstd"},
        "timezone": "UTC",
        "custom_commands": [install_command],
    }
    if wants_account:
        users = [{"username": account_name, "sudo": admin.isChecked(), "enc_password": password_hash(account_password)}]
    else:
        guest_password = secrets.token_urlsafe(32)
        users = [{"username": "luna-guest", "sudo": False, "enc_password": password_hash(guest_password)}]
    credentials = {
        "users": users,
        "root_enc_password": password_hash(secrets.token_urlsafe(40)),
    }
    config_path = WORK_DIR / "config.json"
    creds_path = WORK_DIR / "creds.json"
    runner_path = WORK_DIR / "run-installer.sh"
    for path, data in ((config_path, config), (creds_path, credentials)):
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.chmod(path, 0o600)
    runner_path.write_text(
        "#!/usr/bin/env bash\nset +e\n"
        f"sudo /usr/bin/archinstall --config {str(config_path)!r} --creds {str(creds_path)!r}\n"
        "status=$?\nrm -f " + repr(str(config_path)) + " " + repr(str(creds_path)) + " " + repr(str(runner_path)) + "\n"
        "echo\nif [ \"$status\" -eq 0 ]; then echo 'Archinstall has finished. Review its final status before rebooting.'; else echo 'Archinstall exited with an error. Review the output above.'; fi\n"
        "read -r -p 'Press Enter to close this installer window...' _\nexit \"$status\"\n",
        encoding="utf-8",
    )
    os.chmod(runner_path, 0o700)
    message = (
        "A personal account will be created with " + ("administrator" if admin.isChecked() else "standard non-admin") + " privileges."
        if wants_account else
        "Personal account creation was skipped. The installed system will use a restricted luna-guest account with no sudo rights."
    )
    QMessageBox.information(dialog, "Ready for installation", message + "\n\nThe installer will still require you to choose and confirm the target disk. Disk partitions are not preselected.")
    try:
        return subprocess.call(["konsole", "--hold", "-e", "/usr/bin/bash", str(runner_path)])
    except OSError as exc:
        QMessageBox.critical(dialog, "Could not launch installer terminal", str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
