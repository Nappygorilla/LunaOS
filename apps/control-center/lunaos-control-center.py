#!/usr/bin/env python3
"""Native LunaOS Control Center; system changes go through the privileged helper."""
import json
import os
import subprocess
import sys
from pathlib import Path
import tomllib

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget

SYSTEM_PROFILES = Path("/usr/share/lunaos/profiles")
LOCAL_ROOT = Path(__file__).resolve().parents[2]
LOCAL_PROFILES = LOCAL_ROOT / "config" / "profiles"
SYSTEM_MANIFEST = Path("/usr/share/lunaos/build-modules.json")
LOCAL_MANIFEST = LOCAL_ROOT / "config/build-modules.default.json"
HELPER = Path("/usr/lib/lunaos/lunaos-profile-apply")
USER_STATE = Path.home() / ".config/lunaos/active.json"
FEATURES = ("security", "privacy", "performance", "gaming")


def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def main():
    profile_dir = SYSTEM_PROFILES if SYSTEM_PROFILES.is_dir() else LOCAL_PROFILES
    manifest_path = SYSTEM_MANIFEST if SYSTEM_MANIFEST.is_file() else LOCAL_MANIFEST
    manifest = read_json(manifest_path, {})
    included = set(manifest.get("included_modules", ["base", "desktop", *FEATURES, "coding", "creator"]))
    profiles = {}
    for path in sorted(profile_dir.glob("*.toml")):
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        if data.get("profile", {}).get("id") == path.stem:
            profiles[path.stem] = data
    if not profiles:
        raise RuntimeError("No LunaOS profiles found.")
    app = QApplication(sys.argv)
    app.setApplicationName("LunaOS Control Center")
    app.setStyleSheet("""
      QWidget { background:#0b1020; color:#edf3ff; font:13px 'Segoe UI'; }
      QLabel#title { font-size:28px; font-weight:700; }
      QLabel#sub { color:#a7b8d3; }
      QListWidget { background:#080d19; border:1px solid #263752; border-radius:12px; min-width:190px; padding:6px; }
      QListWidget::item { padding:11px; border-radius:8px; }
      QListWidget::item:selected { background:#16345d; color:white; }
      QCheckBox { padding:10px; border:1px solid #283b56; border-radius:9px; }
      QPushButton { border-radius:9px; padding:12px 18px; font-weight:600; }
      QPushButton#apply { background:#347fff; color:white; }
    """)
    window = QWidget()
    window.setWindowTitle("LunaOS Control Center")
    window.resize(1000, 680)
    outer = QHBoxLayout(window)
    listing = QListWidget()
    for ident, data in profiles.items():
        meta = data["profile"]
        item = QListWidgetItem(f'{meta["name"]}\n{meta.get("category", "Profile")}')
        item.setData(Qt.ItemDataRole.UserRole, ident)
        listing.addItem(item)
    outer.addWidget(listing)
    right = QVBoxLayout()
    title = QLabel("LunaOS Control Center")
    title.setObjectName("title")
    right.addWidget(title)
    status = QLabel("Select a profile, review switches, and apply.")
    status.setObjectName("sub")
    right.addWidget(status)
    description = QLabel()
    description.setWordWrap(True)
    description.setMinimumHeight(70)
    right.addWidget(description)
    details = {
        "security": "Security — firewall and kernel information restrictions",
        "privacy": "Privacy — managed Firefox telemetry and study opt-outs",
        "performance": "Performance — power mode and reversible VM tuning",
        "gaming": "GameMode — enable the lunaos-game-run integration",
    }
    switches = {}
    for key in FEATURES:
        box = QCheckBox(details[key])
        if key not in included:
            box.setEnabled(False)
            box.setToolTip("Excluded from this ISO build. Rebuild with this module included.")
        switches[key] = box
        right.addWidget(box)
    summary = QLabel()
    summary.setWordWrap(True)
    summary.setObjectName("sub")
    right.addWidget(summary)
    right.addStretch(1)
    actions = QHBoxLayout()
    reset = QPushButton("Reset switches to profile")
    apply = QPushButton("Apply profile")
    apply.setObjectName("apply")
    actions.addWidget(reset)
    actions.addStretch(1)
    actions.addWidget(apply)
    right.addLayout(actions)
    outer.addLayout(right, 1)
    state = {"profile": "balanced"}

    def selected_id():
        item = listing.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else state["profile"]

    def select_profile(item=None):
        ident = item.data(Qt.ItemDataRole.UserRole) if item is not None else selected_id()
        state["profile"] = ident
        data = profiles[ident]
        description.setText(data["profile"].get("description", ""))
        for key, box in switches.items():
            built = key in included
            box.blockSignals(True)
            box.setEnabled(built)
            box.setChecked(built and bool(data.get("modules", {}).get(key, False)))
            box.blockSignals(False)
        enabled = [key.title() for key, value in data.get("modules", {}).items() if value and (key not in FEATURES or key in included)]
        missing = sorted(key for key in ("security", "privacy", "performance", "gaming", "coding", "creator") if key not in included)
        suffix = ("; not built: " + ", ".join(missing)) if missing else ""
        summary.setText("Profile includes: " + (", ".join(enabled) or "no optional modules") + suffix)
        status.setText("Selected preset · " + data["profile"].get("category", "Profile"))

    def apply_profile():
        ident = selected_id()
        module_flags = {key: (box.isChecked() if key in included else False) for key, box in switches.items()}
        if not module_flags["security"]:
            reply = QMessageBox.warning(window, "Disable security?", "This stops and disables the firewall. Continue only if you understand the risk.", QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.Cancel)
            if reply != QMessageBox.StandardButton.Yes:
                return
        reply = QMessageBox.question(window, "Apply LunaOS profile", "Apply this profile and selected switches? Administrator authentication may be required.", QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Apply, QMessageBox.StandardButton.Apply)
        if reply != QMessageBox.StandardButton.Apply:
            return
        args = ["pkexec", str(HELPER), ident]
        args.extend("--" + key + "=" + ("on" if value else "off") for key, value in module_flags.items())
        apply.setEnabled(False)
        status.setText("Applying changes…")
        app.processEvents()
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            QMessageBox.critical(window, "Could not apply profile", str(exc))
            status.setText("Apply failed")
            apply.setEnabled(True)
            return
        apply.setEnabled(True)
        if result.returncode:
            QMessageBox.critical(window, "Profile not applied", (result.stderr or result.stdout or "Helper failed").strip()[-2000:])
            status.setText("Apply failed")
            return
        USER_STATE.parent.mkdir(parents=True, exist_ok=True)
        user_state = {"profile": ident, "modules": dict(profiles[ident].get("modules", {})), "settings": profiles[ident].get("settings", {})}
        user_state["modules"].update(module_flags)
        temporary = USER_STATE.with_suffix(".tmp")
        temporary.write_text(json.dumps(user_state, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(USER_STATE)
        status.setText("Profile applied successfully")
        QMessageBox.information(window, "LunaOS configured", (result.stdout or "Profile applied.").strip())

    listing.currentItemChanged.connect(lambda item, _old: select_profile(item) if item else None)
    reset.clicked.connect(lambda: select_profile())
    apply.clicked.connect(apply_profile)
    preferred = read_json(USER_STATE, {}).get("profile")
    if not preferred:
        preferred = read_json(Path.home() / ".config/lunaos/preferences.json", {}).get("preferred_profile")
    if not preferred:
        try:
            preferred = Path("/etc/lunaos/default-profile").read_text(encoding="utf-8").strip()
        except OSError:
            preferred = None
    start_row = 0
    for index in range(listing.count()):
        if listing.item(index).data(Qt.ItemDataRole.UserRole) == preferred:
            start_row = index
            break
    listing.setCurrentRow(start_row)
    window.show()
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "LunaOS Control Center", str(exc))
        raise SystemExit(1)
