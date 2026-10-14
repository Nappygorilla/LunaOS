#!/usr/bin/env python3
"""Optional first-run wizard. Skipping account creation keeps guest access restricted."""
import json
import re
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QComboBox

HELPER = "/usr/lib/lunaos/lunaos-setup-user-helper"
WALLPAPER = "/usr/share/backgrounds/lunaos/lunaos-wallpaper.svg"
PROFILE_NAMES = {
    "Balanced": "balanced", "Gaming": "gaming", "Coding": "coding",
    "Creator": "creator", "Privacy-first": "privacy",
    "Secure workstation": "secure", "Battery saver": "battery-saver",
}
ACCOUNT_PATTERN = re.compile(r"[a-z_][a-z0-9_-]{0,30}\$?")


def setup_personalization(enabled):
    if not enabled:
        return "Desktop personalization skipped; existing settings were left unchanged."
    try:
        subprocess.run(["plasma-apply-colorscheme", "BreezeDark"], check=False, timeout=10, capture_output=True)
        if Path(WALLPAPER).is_file():
            subprocess.run(["plasma-apply-wallpaperimage", WALLPAPER], check=False, timeout=10, capture_output=True)
        return "Applied the LunaOS dark theme and wallpaper to this user."
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "Some desktop settings could not be applied: " + str(exc)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LunaOS First-run Setup")
    app.setStyleSheet("""
      QWidget { background:#0b1020; color:#edf3ff; font:13px 'Segoe UI'; }
      QLabel#heading { font-size:24px; font-weight:700; }
      QLabel#muted { color:#a7b8d3; }
      QGroupBox { border:1px solid #283b56; border-radius:12px; margin-top:10px; padding:12px; font-weight:600; }
      QGroupBox::title { subcontrol-origin:margin; left:12px; padding:0 6px; }
      QLineEdit { padding:9px; border:1px solid #304968; border-radius:7px; background:#080d19; }
      QCheckBox { padding:6px; }
    """)
    dialog = QDialog()
    dialog.setWindowTitle("Finish setting up LunaOS")
    dialog.setMinimumWidth(620)
    outer = QVBoxLayout(dialog)
    heading = QLabel("Welcome to LunaOS")
    heading.setObjectName("heading")
    outer.addWidget(heading)
    intro = QLabel("You can customize the desktop now or skip it. If you are using the restricted guest session, you can also skip creating a personal account and keep using LunaOS without administrator permissions.")
    intro.setWordWrap(True)
    intro.setObjectName("muted")
    outer.addWidget(intro)

    personalization = QGroupBox("Optional desktop personalization")
    personal_layout = QVBoxLayout(personalization)
    use_theme = QCheckBox("Apply LunaOS dark theme and wallpaper")
    use_theme.setChecked(True)
    personal_layout.addWidget(use_theme)
    profile = QComboBox()
    profile.addItems(PROFILE_NAMES.keys())
    profile.setCurrentText("Balanced")
    profile.setToolTip("Saves the preferred profile for Control Center; system-wide changes require administrator credentials.")
    personal_form = QFormLayout()
    personal_form.addRow("Preferred Control Center profile", profile)
    personal_layout.addLayout(personal_form)
    outer.addWidget(personalization)

    account = QGroupBox("Create a personal account (optional)")
    account_layout = QVBoxLayout(account)
    create_account = QCheckBox("Create a standard personal account now")
    account_layout.addWidget(create_account)
    fields = QFormLayout()
    username = QLineEdit()
    username.setPlaceholderText("e.g. lunauser")
    password = QLineEdit()
    password.setEchoMode(QLineEdit.EchoMode.Password)
    password.setPlaceholderText("At least 12 characters")
    confirmation = QLineEdit()
    confirmation.setEchoMode(QLineEdit.EchoMode.Password)
    confirmation.setPlaceholderText("Repeat password")
    fields.addRow("Username", username)
    fields.addRow("Password", password)
    fields.addRow("Confirm password", confirmation)
    account_layout.addLayout(fields)
    account_note = QLabel("A personal account created here is standard and does not receive administrator access. To create an administrator account, select account creation in the installer and explicitly enable its administrator option. Skipping account creation keeps the existing guest session restricted.")
    account_note.setWordWrap(True)
    account_note.setObjectName("muted")
    account_layout.addWidget(account_note)
    outer.addWidget(account)

    def set_account_fields(enabled):
        for item in (username, password, confirmation):
            item.setEnabled(enabled)
    create_account.toggled.connect(set_account_fields)
    set_account_fields(False)

    buttons = QDialogButtonBox()
    buttons.addButton("Finish setup", QDialogButtonBox.ButtonRole.AcceptRole)
    buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
    outer.addWidget(buttons)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return 0

    settings_message = setup_personalization(use_theme.isChecked())
    preferences = {"preferred_profile": PROFILE_NAMES[profile.currentText()], "desktop_personalization": use_theme.isChecked()}
    state_dir = Path.home() / ".config/lunaos"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "preferences.json").write_text(json.dumps(preferences, indent=2) + "\n", encoding="utf-8")
    autostart = Path.home() / ".config/autostart/lunaos-firstboot-setup.desktop"
    if not create_account.isChecked():
        autostart.unlink(missing_ok=True)
        QMessageBox.information(dialog, "Setup complete", settings_message + "\n\nAccount creation skipped. This session remains restricted: it is not an administrator and cannot use sudo. You can reopen LunaOS First-run Setup from the application menu later.")
        return 0

    account_name = username.text().strip()
    if not ACCOUNT_PATTERN.fullmatch(account_name) or account_name in {"root", "nobody", "luna", "luna-guest", "bin", "daemon", "adm", "mail", "ftp", "http"}:
        QMessageBox.warning(dialog, "Check username", "Choose a non-reserved username using lowercase letters, digits, underscores, and hyphens.")
        return 1
    secret = password.text()
    if len(secret) < 12 or secret != confirmation.text() or "\n" in secret or ":" in secret or "\r" in secret:
        QMessageBox.warning(dialog, "Check password", "Passwords must match, be at least 12 characters, and contain no colon or newline.")
        return 1
    payload = {"username": account_name, "password": secret}
    try:
        result = subprocess.run(["pkexec", HELPER], input=json.dumps(payload) + "\n", text=True, capture_output=True, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        QMessageBox.critical(dialog, "Could not create account", str(exc))
        return 1
    password.clear()
    confirmation.clear()
    if result.returncode:
        QMessageBox.warning(dialog, "Account not created", (result.stderr or result.stdout or "The first-user setup helper declined the request.").strip()[-1600:])
        return 1
    autostart.unlink(missing_ok=True)
    QMessageBox.information(dialog, "Personal account created", settings_message + "\n\nYour personal account has standard, non-administrator permissions. Sign out, then sign in with your new username.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
