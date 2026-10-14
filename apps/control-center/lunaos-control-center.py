#!/usr/bin/env python3
"""LunaOS Control Center: profiles, power, cooling, snapshots, and developer tools."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import tomllib

from PySide6.QtCore import Qt, QDateTime, QTime, QProcess, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateTimeEdit, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QProgressBar, QScrollArea, QTabWidget, QTextEdit, QTimeEdit, QVBoxLayout, QWidget
)

SYSTEM_PROFILES = Path("/usr/share/lunaos/profiles")
LOCAL_ROOT = Path(__file__).resolve().parents[2]
LOCAL_PROFILES = LOCAL_ROOT / "config" / "profiles"
SYSTEM_MANIFEST = Path("/usr/share/lunaos/build-modules.json")
LOCAL_MANIFEST = LOCAL_ROOT / "config/build-modules.default.json"
PROFILE_HELPER = Path("/usr/lib/lunaos/lunaos-profile-apply")
TOOLS_HELPER = Path("/usr/lib/lunaos/lunaos-system-tools")
UPDATE_SETTINGS = Path.home() / ".config/lunaos/update-settings.json"
SUPPORT_ISSUES_URL = "https://github.com/Nappygorilla/LunaOS/issues/new"
APP_ARGS = set(sys.argv[1:])
USER_STATE = Path.home() / ".config/lunaos/active.json"
FEATURES = ("security", "privacy", "performance", "gaming")

DEV_BUNDLES = [
    ("ide-geany", "Geany — lightweight IDE"),
    ("ide-kdevelop", "KDevelop — C/C++ and language plugins"),
    ("ide-qtcreator", "Qt Creator — C++ / Qt IDE"),
    ("ide-gnome-builder", "GNOME Builder — GNOME application IDE"),
    ("toolchain-python", "Python — interpreter, pip, virtualenv, pytest"),
    ("toolchain-node", "Node.js and npm"),
    ("toolchain-rust", "Rust toolchain"),
    ("toolchain-go", "Go toolchain"),
    ("toolchain-cpp", "C/C++ — compiler, build tools, CMake, debugger"),
    ("docker", "Docker Engine + Compose + Buildx"),
]


def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def run_command(argv, timeout=180, elevated=False):
    command = list(argv)
    if elevated:
        command.insert(0, "pkexec")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()
        return result.returncode, output, error
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def tool_action(action, args=(), timeout=240):
    return run_command([str(TOOLS_HELPER), action, *args], timeout=timeout, elevated=True)


def show_result(parent, title, result, success_text=None):
    code, output, error = result
    details = output or error or ("Completed successfully." if code == 0 else "The operation failed without further details.")
    if code == 0:
        QMessageBox.information(parent, title, success_text or details[-8000:])
    else:
        QMessageBox.warning(parent, title, details[-8000:])
    return code == 0, details


def main():
    profile_dir = SYSTEM_PROFILES if SYSTEM_PROFILES.is_dir() else LOCAL_PROFILES
    manifest_path = SYSTEM_MANIFEST if SYSTEM_MANIFEST.is_file() else LOCAL_MANIFEST
    manifest = read_json(manifest_path, {})
    included = set(manifest.get("included_modules", ["base", "desktop", *FEATURES, "coding", "creator"]))
    profiles = {}
    for path in sorted(profile_dir.glob("*.toml")):
        try:
            with path.open("rb") as stream:
                data = tomllib.load(stream)
            if data.get("profile", {}).get("id") == path.stem:
                profiles[path.stem] = data
        except (OSError, ValueError, tomllib.TOMLDecodeError):
            continue
    if not profiles:
        raise RuntimeError("No LunaOS profiles found.")

    app = QApplication([sys.argv[0]])
    app.setApplicationName("LunaOS Control Center")
    app.setStyleSheet("""
      QWidget { background:#0b1020; color:#edf3ff; font:13px 'Segoe UI'; }
      QLabel#title { font-size:27px; font-weight:700; }
      QLabel#sub { color:#a7b8d3; }
      QLabel#section { font-size:17px; font-weight:650; }
      QTabWidget::pane { border:1px solid #263752; border-radius:10px; top:-1px; }
      QTabBar::tab { background:#111b30; color:#b8c9e5; padding:12px 18px; margin-right:4px; border-top-left-radius:8px; border-top-right-radius:8px; }
      QTabBar::tab:selected { background:#1d3d6e; color:#ffffff; }
      QListWidget, QTextEdit, QLineEdit, QComboBox { background:#080d19; border:1px solid #263752; border-radius:9px; padding:8px; }
      QListWidget { min-width:190px; }
      QListWidget::item { padding:10px; border-radius:7px; }
      QListWidget::item:selected { background:#16345d; color:white; }
      QCheckBox { padding:8px; border:1px solid #283b56; border-radius:8px; }
      QPushButton { background:#1c2c45; border:1px solid #2a4161; border-radius:9px; padding:11px 16px; font-weight:600; }
      QPushButton#primary { background:#347fff; color:white; border-color:#347fff; }
      QPushButton:disabled { color:#697b96; background:#111827; }
    """)

    window = QWidget()
    window.setWindowTitle("LunaOS Control Center")
    window.resize(1120, 800)
    outer = QVBoxLayout(window)
    heading = QLabel("LunaOS Control Center")
    heading.setObjectName("title")
    outer.addWidget(heading)
    intro = QLabel("Tune your system, protect your work, and add the tools you need.")
    intro.setObjectName("sub")
    outer.addWidget(intro)
    tabs = QTabWidget()
    outer.addWidget(tabs, 1)

    # Profile presets
    profile_tab = QWidget()
    profile_outer = QHBoxLayout(profile_tab)
    listing = QListWidget()
    for ident, data in profiles.items():
        meta = data["profile"]
        item = QListWidgetItem(f'{meta.get("name", ident)}\n{meta.get("category", "Profile")}')
        item.setData(Qt.ItemDataRole.UserRole, ident)
        listing.addItem(item)
    profile_outer.addWidget(listing)
    profile_panel = QVBoxLayout()
    profile_status = QLabel("Select a preset, review switches, and apply.")
    profile_status.setObjectName("sub")
    profile_panel.addWidget(profile_status)
    profile_description = QLabel()
    profile_description.setWordWrap(True)
    profile_description.setMinimumHeight(66)
    profile_panel.addWidget(profile_description)
    descriptions = {
        "security": "Security — firewall and kernel information restrictions",
        "privacy": "Privacy — managed Firefox privacy policies",
        "performance": "Performance — power profile and reversible VM tuning",
        "gaming": "GameMode — per-user game launch integration",
    }
    switches = {}
    for key in FEATURES:
        box = QCheckBox(descriptions[key])
        box.setEnabled(key in included)
        if key not in included:
            box.setToolTip("Not included in this ISO build.")
        switches[key] = box
        profile_panel.addWidget(box)
    profile_summary = QLabel()
    profile_summary.setWordWrap(True)
    profile_summary.setObjectName("sub")
    profile_panel.addWidget(profile_summary)
    profile_panel.addStretch(1)
    profile_actions = QHBoxLayout()
    profile_reset = QPushButton("Reset switches")
    profile_apply = QPushButton("Apply profile")
    profile_apply.setObjectName("primary")
    profile_actions.addWidget(profile_reset)
    profile_actions.addStretch(1)
    profile_actions.addWidget(profile_apply)
    profile_panel.addLayout(profile_actions)
    profile_outer.addLayout(profile_panel, 1)
    profile_state = {"profile": "balanced"}

    def selected_profile():
        item = listing.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else profile_state["profile"]

    def select_profile(item=None):
        ident = item.data(Qt.ItemDataRole.UserRole) if item is not None else selected_profile()
        if ident not in profiles:
            ident = next(iter(profiles))
        profile_state["profile"] = ident
        data = profiles[ident]
        profile_description.setText(data["profile"].get("description", ""))
        for key, box in switches.items():
            built = key in included
            box.blockSignals(True)
            box.setEnabled(built)
            box.setChecked(built and bool(data.get("modules", {}).get(key, False)))
            box.blockSignals(False)
        enabled = [key.title() for key, value in data.get("modules", {}).items()
                   if value and (key not in FEATURES or key in included)]
        missing = sorted(key for key in ("security", "privacy", "performance", "gaming", "coding", "creator")
                         if key not in included)
        suffix = (" · not in this build: " + ", ".join(missing)) if missing else ""
        profile_summary.setText("Preset modules: " + (", ".join(enabled) or "no optional modules") + suffix)
        profile_status.setText("Preset selected · " + data["profile"].get("category", "Profile"))

    def apply_profile():
        ident = selected_profile()
        flags = {key: (box.isChecked() if key in included else False) for key, box in switches.items()}
        if not flags["security"]:
            reply = QMessageBox.warning(
                window, "Disable security?",
                "This stops and disables the firewall. Continue only if you understand the risk.",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Cancel
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        reply = QMessageBox.question(
            window, "Apply LunaOS profile",
            "Apply this preset and its selected switches? Administrator authentication may be required.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Apply,
            QMessageBox.StandardButton.Apply
        )
        if reply != QMessageBox.StandardButton.Apply:
            return
        args = ["pkexec", str(PROFILE_HELPER), ident]
        args.extend("--" + key + "=" + ("on" if value else "off") for key, value in flags.items())
        profile_apply.setEnabled(False)
        profile_status.setText("Applying changes…")
        app.processEvents()
        code, output, error = run_command(args, timeout=180)
        profile_apply.setEnabled(True)
        if code:
            profile_status.setText("Apply failed")
            QMessageBox.warning(window, "Profile not applied", (error or output or "Helper failed")[-8000:])
            return
        USER_STATE.parent.mkdir(parents=True, exist_ok=True)
        saved = {
            "profile": ident,
            "modules": dict(profiles[ident].get("modules", {})),
            "settings": profiles[ident].get("settings", {}),
        }
        saved["modules"].update(flags)
        temporary = USER_STATE.with_suffix(".tmp")
        temporary.write_text(json.dumps(saved, indent=2) + "\n", encoding="utf-8")
        os.chmod(temporary, 0o600)
        temporary.replace(USER_STATE)
        profile_status.setText("Profile applied successfully")
        QMessageBox.information(window, "LunaOS configured", (output or "Profile applied.")[-8000:])

    listing.currentItemChanged.connect(lambda item, _old: select_profile(item) if item else None)
    profile_reset.clicked.connect(lambda: select_profile())
    profile_apply.clicked.connect(apply_profile)
    preferred = read_json(USER_STATE, {}).get("profile")
    if not preferred:
        preferred = read_json(Path.home() / ".config/lunaos/preferences.json", {}).get("preferred_profile")
    if not preferred:
        try:
            preferred = Path("/etc/lunaos/default-profile").read_text(encoding="utf-8").strip()
        except OSError:
            preferred = None
    row = next((i for i in range(listing.count())
                if listing.item(i).data(Qt.ItemDataRole.UserRole) == preferred), 0)
    listing.setCurrentRow(row)
    tabs.addTab(profile_tab, "Profiles")

    # Power profiles
    power_tab = QWidget()
    power_layout = QVBoxLayout(power_tab)
    power_title = QLabel("Power modes")
    power_title.setObjectName("section")
    power_layout.addWidget(power_title)
    power_layout.addWidget(QLabel("Switch between performance, balanced, and power-saving modes. Actual modes depend on your hardware and firmware."))
    power_form = QFormLayout()
    power_combo = QComboBox()
    for label, value in (
        ("Power saver · longer battery life", "power-saver"),
        ("Balanced · everyday use", "balanced"),
        ("Performance · prioritize responsiveness", "performance"),
    ):
        power_combo.addItem(label, value)
    power_form.addRow("Preferred mode", power_combo)
    power_layout.addLayout(power_form)
    power_status = QLabel("Checking power-profile support…")
    power_status.setWordWrap(True)
    power_status.setObjectName("sub")
    power_layout.addWidget(power_status)
    power_actions = QHBoxLayout()
    power_refresh = QPushButton("Refresh status")
    power_install = QPushButton("Install power + sensor support")
    power_apply = QPushButton("Apply power mode")
    power_apply.setObjectName("primary")
    power_actions.addWidget(power_refresh)
    power_actions.addWidget(power_install)
    power_actions.addStretch(1)
    power_actions.addWidget(power_apply)
    power_layout.addLayout(power_actions)
    power_layout.addStretch(1)

    def refresh_power():
        code, output, error = run_command([str(TOOLS_HELPER), "power-status"])
        if code:
            power_status.setText("Power profile status unavailable: " + (error or output))
            return
        try:
            info = json.loads(output)
        except ValueError:
            power_status.setText(output or "Power profile status unavailable.")
            return
        if not info.get("installed"):
            power_status.setText("Power profile support is not installed. Install it to enable these modes.")
            return
        active = info.get("active") or "unknown"
        available = info.get("available", [])
        power_status.setText(
            "Current mode: " + active + "\nAvailable on this machine: " +
            (", ".join(available) if available else "daemon is unavailable or no modes were reported") +
            "\nPerformance mode may be absent on some laptops. LunaOS will not fake a mode your hardware does not expose."
        )
        index = power_combo.findData(active)
        if index >= 0:
            power_combo.setCurrentIndex(index)

    def set_power():
        mode = power_combo.currentData()
        okay, details = show_result(window, "Power mode", tool_action("power-set", [str(mode)], timeout=90))
        power_status.setText(details[-4000:])
        refresh_power()

    def install_power():
        okay, details = show_result(
            window, "Power and sensor support",
            tool_action("install", ["--bundle", "power"], timeout=1800),
            "Power profile and hardware sensor components installed."
        )
        power_status.setText(details[-4000:])
        refresh_power()

    power_refresh.clicked.connect(refresh_power)
    power_install.clicked.connect(install_power)
    power_apply.clicked.connect(set_power)
    tabs.addTab(power_tab, "Power")

    # Cooling / fan controller
    fan_tab = QWidget()
    fan_layout = QVBoxLayout(fan_tab)
    fan_title = QLabel("Cooling and fan control")
    fan_title.setObjectName("section")
    fan_layout.addWidget(fan_title)
    fan_layout.addWidget(QLabel(
        "LunaOS detects sensors and provides a guided fan-curve setup where the hardware supports it. "
        "Many laptops and some desktops only expose fan control through firmware."
    ))
    fan_warning = QLabel(
        "Safety: incorrect PWM settings can overheat or damage hardware. Keep firmware/automatic cooling enabled "
        "unless the fan controller is detected and you understand the prompts."
    )
    fan_warning.setWordWrap(True)
    fan_warning.setObjectName("sub")
    fan_layout.addWidget(fan_warning)
    fan_status = QLabel("Reading temperatures and fan-control support…")
    fan_status.setWordWrap(True)
    fan_layout.addWidget(fan_status)
    fan_readings = QTextEdit()
    fan_readings.setReadOnly(True)
    fan_readings.setPlaceholderText("Temperature and fan RPM readings will appear here.")
    fan_layout.addWidget(fan_readings, 1)
    fan_actions = QHBoxLayout()
    fan_refresh = QPushButton("Refresh readings")
    fan_install = QPushButton("Install sensor support")
    fan_configure = QPushButton("Guided fan-curve setup")
    fan_start = QPushButton("Use configured fan curve")
    fan_stop = QPushButton("Return to firmware / automatic cooling")
    fan_actions.addWidget(fan_refresh)
    fan_actions.addWidget(fan_install)
    fan_actions.addWidget(fan_configure)
    fan_actions.addWidget(fan_start)
    fan_actions.addWidget(fan_stop)
    fan_layout.addLayout(fan_actions)

    def refresh_fans():
        code, output, error = run_command([str(TOOLS_HELPER), "fan-status"])
        if code:
            fan_status.setText("Fan status unavailable: " + (error or output))
            return
        try:
            info = json.loads(output)
        except ValueError:
            fan_status.setText(output or "Fan status unavailable.")
            return
        fan_status.setText(
            "lm_sensors: " + ("available" if info.get("sensors_installed") else "not installed") +
            " · PWM outputs detected: " + ("yes" if info.get("pwm_detected") else "no") +
            " · fancontrol config: " + ("ready" if info.get("configured") else "not configured") +
            " · fancontrol service: " + ("active" if info.get("active") else "inactive")
        )
        readings = info.get("readings") or "No sensor output is available on this machine."
        fan_readings.setPlainText(readings)

    def install_sensors():
        okay, details = show_result(
            window, "Sensor support",
            tool_action("install", ["--bundle", "power"], timeout=1800),
            "Sensor and power-profile packages installed."
        )
        fan_readings.setPlainText(details[-8000:])
        refresh_fans()

    def configure_fans():
        if not shutil.which("konsole"):
            QMessageBox.warning(window, "Terminal not found", "Konsole is required for the guided fan-curve setup.")
            return
        reply = QMessageBox.warning(
            window, "Before configuring fans",
            "This opens lm_sensors pwmconfig. Follow its prompts carefully, do not guess at fan mappings, "
            "and stop if your CPU/GPU cooling behavior is unclear. Hardware may not support software control. Continue?",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            subprocess.Popen(["konsole", "-e", "pkexec", str(TOOLS_HELPER), "fan-configure"])
        except OSError as exc:
            QMessageBox.warning(window, "Could not open guided setup", str(exc))

    def start_fans():
        reply = QMessageBox.warning(
            window, "Enable software fan control?",
            "This activates the fancontrol service using /etc/fancontrol. Do this only after completing the guided "
            "configuration and confirming that the detected sensors and fans are correct.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        okay, details = show_result(window, "Fan control", tool_action("fan-start", timeout=90))
        fan_status.setText(details[-3000:])
        refresh_fans()

    def stop_fans():
        okay, details = show_result(
            window, "Fan control",
            tool_action("fan-stop", timeout=90),
            "Software fancontrol was stopped. Firmware control should resume where supported."
        )
        fan_status.setText(details[-3000:])
        refresh_fans()

    fan_refresh.clicked.connect(refresh_fans)
    fan_install.clicked.connect(install_sensors)
    fan_configure.clicked.connect(configure_fans)
    fan_start.clicked.connect(start_fans)
    fan_stop.clicked.connect(stop_fans)
    tabs.addTab(fan_tab, "Cooling")

    # Snapshots
    snapshot_tab = QWidget()
    snapshot_layout = QVBoxLayout(snapshot_tab)
    snapshot_title = QLabel("System snapshots")
    snapshot_title.setObjectName("section")
    snapshot_layout.addWidget(snapshot_title)
    snapshot_layout.addWidget(QLabel(
        "Timeshift can create restore points before risky updates, and its full manager handles schedules and restores. "
        "A usable backup destination and compatible filesystem layout are still required."
    ))
    snapshot_layout.addWidget(QLabel(
        "Creating a snapshot does not replace a separate backup of personal files. Restore can revert system changes "
        "and may require a reboot, so review the selected snapshot in Timeshift before restoring."
    ))
    snapshot_form = QFormLayout()
    snapshot_comment = QLineEdit("LunaOS restore point")
    snapshot_comment.setMaxLength(80)
    snapshot_form.addRow("Snapshot description", snapshot_comment)
    snapshot_layout.addLayout(snapshot_form)
    snapshot_output = QTextEdit()
    snapshot_output.setReadOnly(True)
    snapshot_output.setPlaceholderText("Click Refresh to list snapshots, or create a restore point.")
    snapshot_layout.addWidget(snapshot_output, 1)
    snapshot_actions = QHBoxLayout()
    snapshot_refresh = QPushButton("Refresh snapshots")
    snapshot_install = QPushButton("Install Timeshift")
    snapshot_create = QPushButton("Create snapshot")
    snapshot_create.setObjectName("primary")
    snapshot_open = QPushButton("Open Timeshift · schedule / restore")
    snapshot_actions.addWidget(snapshot_refresh)
    snapshot_actions.addWidget(snapshot_install)
    snapshot_actions.addWidget(snapshot_create)
    snapshot_actions.addWidget(snapshot_open)
    snapshot_layout.addLayout(snapshot_actions)

    def refresh_snapshots():
        okay, details = show_result(
            window, "Snapshot list", tool_action("snapshot-list", timeout=180),
            "Snapshot list refreshed."
        )
        snapshot_output.setPlainText(details[-12000:])

    def install_timeshift():
        okay, details = show_result(
            window, "Install Timeshift",
            tool_action("install", ["--bundle", "snapshots"], timeout=1800),
            "Timeshift and its scheduling service have been installed."
        )
        snapshot_output.setPlainText(details[-10000:])

    def create_snapshot():
        comment = snapshot_comment.text().strip()
        if not comment:
            QMessageBox.warning(window, "Description required", "Enter a short description for the snapshot.")
            return
        reply = QMessageBox.question(
            window, "Create system snapshot",
            "Create a Timeshift snapshot now? This can use significant disk space and may take a while.",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        okay, details = show_result(
            window, "Create snapshot",
            tool_action("snapshot-create", [comment], timeout=1800)
        )
        snapshot_output.setPlainText(details[-12000:])

    def open_timeshift():
        if not shutil.which("timeshift-gtk"):
            QMessageBox.warning(window, "Timeshift not installed", "Use Install Timeshift first.")
            return
        try:
            subprocess.Popen(["timeshift-gtk"])
        except OSError as exc:
            QMessageBox.warning(window, "Could not open Timeshift", str(exc))

    snapshot_refresh.clicked.connect(refresh_snapshots)
    snapshot_install.clicked.connect(install_timeshift)
    snapshot_create.clicked.connect(create_snapshot)
    snapshot_open.clicked.connect(open_timeshift)
    tabs.addTab(snapshot_tab, "Snapshots")

    # Developer tools
    dev_tab = QWidget()
    dev_layout = QVBoxLayout(dev_tab)
    dev_title = QLabel("Developer tools")
    dev_title.setObjectName("section")
    dev_layout.addWidget(dev_title)
    dev_layout.addWidget(QLabel(
        "Choose the IDEs, language toolchains, and container tools you need. LunaOS installs only from the official "
        "Arch repositories here; it does not run arbitrary install scripts or install AUR packages for you."
    ))
    dev_scroll = QScrollArea()
    dev_scroll.setWidgetResizable(True)
    dev_items = QWidget()
    dev_items_layout = QVBoxLayout(dev_items)
    dev_checks = {}
    for key, label in DEV_BUNDLES:
        checkbox = QCheckBox(label)
        checkbox.setProperty("bundle", key)
        dev_checks[key] = checkbox
        dev_items_layout.addWidget(checkbox)
    dev_items_layout.addStretch(1)
    dev_scroll.setWidget(dev_items)
    dev_layout.addWidget(dev_scroll, 1)
    docker_note = QLabel(
        "Docker note: the service can be enabled without granting ordinary users root-equivalent Docker-group access. "
        "LunaOS does not add your account to the docker group automatically."
    )
    docker_note.setWordWrap(True)
    docker_note.setObjectName("sub")
    dev_layout.addWidget(docker_note)
    dev_actions = QHBoxLayout()
    dev_select_all = QPushButton("Select all")
    dev_clear = QPushButton("Clear")
    dev_install = QPushButton("Install selected")
    dev_install.setObjectName("primary")
    dev_actions.addWidget(dev_select_all)
    dev_actions.addWidget(dev_clear)
    dev_actions.addStretch(1)
    dev_actions.addWidget(dev_install)
    dev_layout.addLayout(dev_actions)
    dev_output = QTextEdit()
    dev_output.setReadOnly(True)
    dev_output.setMaximumHeight(120)
    dev_output.setPlaceholderText("Installation results will appear here.")
    dev_layout.addWidget(dev_output)

    def install_selected():
        selected = [key for key, checkbox in dev_checks.items() if checkbox.isChecked()]
        if not selected:
            QMessageBox.information(window, "No tools selected", "Select at least one IDE, toolchain, or Docker.")
            return
        explanation = "Install the selected tools using pacman. Arch requires a full system upgrade alongside installs. "
        if "docker" in selected:
            explanation += "The Docker service will be enabled, but your user will NOT be added to the root-equivalent docker group. "
        explanation += "This may download large packages. Continue?"
        reply = QMessageBox.question(
            window, "Install developer tools", explanation,
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Cancel
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        args = []
        for key in selected:
            args.extend(["--bundle", key])
        dev_install.setEnabled(False)
        dev_output.setPlainText("Installing selected packages and applying required service setup…\nThis may take several minutes.")
        app.processEvents()
        result = tool_action("install", args, timeout=2400)
        dev_install.setEnabled(True)
        code, output, error = result
        details = output or error or ("Installation completed." if code == 0 else "No details were returned.")
        dev_output.setPlainText(details[-16000:])
        if code == 0:
            QMessageBox.information(window, "Developer tools ready", "Package installation finished.\n\n" + details[-4000:])
        else:
            QMessageBox.warning(window, "Installation did not finish", details[-5000:])

    dev_select_all.clicked.connect(lambda: [item.setChecked(True) for item in dev_checks.values()])
    dev_clear.clicked.connect(lambda: [item.setChecked(False) for item in dev_checks.values()])
    dev_install.clicked.connect(install_selected)
    tabs.addTab(dev_tab, "Developer tools")


    # System updates
    updates_tab = QWidget()
    updates_layout = QVBoxLayout(updates_tab)
    updates_title = QLabel("System updates")
    updates_title.setObjectName("section")
    updates_layout.addWidget(updates_title)
    updates_layout.addWidget(QLabel(
        "Review individual package versions and available changelogs before applying a full Arch Linux system upgrade. "
        "LunaOS highlights security and operating-system updates because they can affect app compatibility, drivers, boot, or core libraries."
    ))

    updates_split = QHBoxLayout()
    update_list = QListWidget()
    update_list.setMinimumWidth(360)
    update_list.setToolTip("Select an update to inspect its versions, category, description, and release notes.")
    updates_split.addWidget(update_list, 1)
    update_detail = QTextEdit()
    update_detail.setReadOnly(True)
    update_detail.setPlaceholderText("Select an update to see version changes, package details, and any available changelog.")
    updates_split.addWidget(update_detail, 2)
    updates_layout.addLayout(updates_split, 1)

    update_status = QLabel("Update status has not been checked yet.")
    update_status.setWordWrap(True)
    update_status.setObjectName("sub")
    updates_layout.addWidget(update_status)
    update_progress = QProgressBar()
    update_progress.setRange(0, 100)
    update_progress.setValue(0)
    update_progress.setFormat("Idle")
    updates_layout.addWidget(update_progress)

    update_actions = QHBoxLayout()
    update_check_btn = QPushButton("Check for updates")
    update_download_btn = QPushButton("Download updates")
    update_install_btn = QPushButton("Install all updates")
    update_install_btn.setObjectName("primary")
    update_copy_btn = QPushButton("Copy update report")
    update_report_btn = QPushButton("Report a problem")
    update_actions.addWidget(update_check_btn)
    update_actions.addWidget(update_download_btn)
    update_actions.addWidget(update_install_btn)
    update_actions.addWidget(update_copy_btn)
    update_actions.addWidget(update_report_btn)
    updates_layout.addLayout(update_actions)

    update_logs = QTextEdit()
    update_logs.setReadOnly(True)
    update_logs.setMaximumHeight(120)
    update_logs.setPlaceholderText("Download and installation progress will be shown here.")
    updates_layout.addWidget(update_logs)

    # Background-notification and scheduling controls
    settings_title = QLabel("Automation and notifications")
    settings_title.setObjectName("section")
    updates_layout.addWidget(settings_title)
    update_settings = read_json(UPDATE_SETTINGS, {})
    notifications_check = QCheckBox("Show desktop notifications when downloaded updates are ready")
    notifications_check.setChecked(update_settings.get("notifications_enabled", True) is True)
    background_downloads_check = QCheckBox("Download updates automatically in the background")
    background_downloads_check.setChecked(update_settings.get("background_downloads_enabled", False) is True)
    updates_layout.addWidget(notifications_check)
    updates_layout.addWidget(background_downloads_check)

    schedule_form = QFormLayout()
    download_time_edit = QTimeEdit()
    download_time_edit.setDisplayFormat("HH:mm")
    download_time_edit.setTime(QTime.fromString(update_settings.get("download_time", "09:00"), "HH:mm"))
    schedule_form.addRow("Daily background download time", download_time_edit)

    schedule_install_check = QCheckBox("Schedule an update review and installation prompt")
    install_dt = QDateTimeEdit()
    install_dt.setCalendarPopup(True)
    install_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
    install_dt.setDateTime(QDateTime.currentDateTime().addDays(1))
    scheduled_install_value = update_settings.get("schedule_install_at")
    if isinstance(scheduled_install_value, str) and scheduled_install_value:
        parsed = QDateTime.fromString(scheduled_install_value, Qt.DateFormat.ISODate)
        if parsed.isValid():
            schedule_install_check.setChecked(True)
            install_dt.setDateTime(parsed)
    schedule_form.addRow(schedule_install_check, install_dt)

    reboot_schedule_check = QCheckBox("Schedule an automatic reboot (save work before the selected time)")
    reboot_dt = QDateTimeEdit()
    reboot_dt.setCalendarPopup(True)
    reboot_dt.setDisplayFormat("yyyy-MM-dd HH:mm")
    reboot_dt.setDateTime(QDateTime.currentDateTime().addDays(1))
    reboot_status_code, reboot_status_output, _reboot_status_error = run_command([str(TOOLS_HELPER), "reboot-schedule-status"], timeout=10)
    if reboot_status_code == 0:
        try:
            reboot_state = json.loads(reboot_status_output)
            if reboot_state.get("scheduled"):
                parsed = QDateTime.fromString(reboot_state.get("when", ""), "yyyy-MM-dd HH:mm")
                if parsed.isValid():
                    reboot_schedule_check.setChecked(True)
                    reboot_dt.setDateTime(parsed)
        except ValueError:
            pass
    schedule_form.addRow(reboot_schedule_check, reboot_dt)
    updates_layout.addLayout(schedule_form)

    schedule_actions = QHBoxLayout()
    schedule_save_btn = QPushButton("Save update schedule and preferences")
    schedule_save_btn.setObjectName("primary")
    schedule_cancel_reboot_btn = QPushButton("Cancel scheduled reboot")
    schedule_actions.addWidget(schedule_save_btn)
    schedule_actions.addWidget(schedule_cancel_reboot_btn)
    updates_layout.addLayout(schedule_actions)

    update_entries = []
    update_operation = {"kind": "", "scheduled": False, "seen": set(), "last_chunk": ""}
    update_process = QProcess(window)
    update_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

    def append_update_log(text):
        existing = update_logs.toPlainText()
        combined = (existing + "\n" + text).strip()
        update_logs.setPlainText(combined[-30000:])
        cursor = update_logs.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        update_logs.setTextCursor(cursor)

    def selected_update():
        item = update_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def render_update_details(entry):
        if not entry:
            update_detail.clear()
            return
        update_detail.setPlainText("Loading package details…")
        app.processEvents()
        code, output, error = run_command(
            [str(TOOLS_HELPER), "updates-details", entry["name"], entry["old_version"], entry["new_version"]],
            timeout=45,
        )
        if code:
            update_detail.setPlainText(
                f'{entry["name"]}\n{entry["old_version"]} → {entry["new_version"]}\n\n'
                + (error or output or "Could not load package details.")
            )
            return
        try:
            details = json.loads(output)
        except ValueError:
            update_detail.setPlainText(output)
            return
        sections = [
            f'Package: {details.get("name", entry["name"])}',
            f'Version change: {details.get("old_version", entry["old_version"])} → {details.get("new_version", entry["new_version"])}',
            f'Category: {details.get("category", entry.get("category", "Applications & libraries"))}',
        ]
        if details.get("critical"):
            sections.append("IMPORTANT: " + (details.get("reason") or "This update may affect system stability or app compatibility."))
        if details.get("description"):
            sections.extend(["", "Package description:", details["description"]])
        sections.extend(["", "Release notes source: " + details.get("changelog_source", "Unknown"), "", "Changelog / release notes:", details.get("changelog", "No changelog is available.")])
        if details.get("url"):
            sections.extend(["", "Project/package website: " + details["url"]])
        sections.extend([
            "",
            "Note: Arch Linux package repositories do not guarantee a per-release changelog for every package. "
            "When one is missing, LunaOS identifies that gap rather than guessing at changes."
        ])
        update_detail.setPlainText("\n".join(sections))
        update_detail.setProperty("package_url", details.get("url", ""))

    def refresh_updates():
        if update_process.state() != QProcess.ProcessState.NotRunning:
            return
        update_status.setText("Checking installed packages against the current repository state…")
        update_progress.setRange(0, 0)
        update_progress.setFormat("Checking…")
        app.processEvents()
        code, output, error = run_command([str(TOOLS_HELPER), "updates-check"], timeout=300)
        update_progress.setRange(0, 100)
        update_progress.setValue(0)
        update_progress.setFormat("Idle")
        if code:
            update_status.setText("Could not check updates: " + (error or output or "Unknown error"))
            return
        try:
            payload = json.loads(output)
            update_entries[:] = payload.get("updates", [])
        except (ValueError, AttributeError):
            update_status.setText("Update check returned an unreadable response.")
            return
        update_list.clear()
        update_entries.sort(key=lambda entry: (not entry.get("critical", False), entry.get("name", "").casefold()))
        for entry in update_entries:
            label = "SECURITY" if entry.get("security") else ("SYSTEM" if entry.get("critical") else entry.get("category", "Application").upper())
            row = QListWidgetItem(
                f'{label}  ·  {entry["name"]}\n{entry["old_version"]}  →  {entry["new_version"]}'
            )
            row.setData(Qt.ItemDataRole.UserRole, entry)
            update_list.addItem(row)
        critical_count = sum(1 for entry in update_entries if entry.get("critical"))
        if not update_entries:
            update_status.setText("Your installed packages appear to be up to date.")
            update_detail.setPlainText("No updates were reported by checkupdates.")
        else:
            update_status.setText(
                f'{len(update_entries)} update(s) available · {critical_count} security / operating-system / driver update(s) flagged for a compatibility warning. '
                "Select an item to inspect its version change and changelog."
            )
            update_list.setCurrentRow(0)
        if update_operation.get("scheduled") and update_operation.get("kind") == "":
            update_operation["scheduled"] = False
            QTimer.singleShot(350, lambda: begin_install(prepared=False, scheduled=True))

    def start_update_process(kind, args=(), scheduled=False):
        if update_process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(window, "Update operation in progress", "Wait for the current update operation to finish.")
            return
        update_operation["kind"] = kind
        update_operation["scheduled"] = scheduled
        update_operation["seen"] = set()
        update_operation["last_chunk"] = ""
        update_logs.clear()
        update_progress.setRange(0, 0)
        update_progress.setFormat("Working…")
        update_status.setText({
            "download": "Downloading available packages…",
            "preflight": "Preparing packages so LunaOS can inspect any package-provided security changelog…",
            "install": "Applying the full system upgrade…",
        }.get(kind, "Working…"))
        update_check_btn.setEnabled(False)
        update_download_btn.setEnabled(False)
        update_install_btn.setEnabled(False)
        update_process.setProgram("pkexec")
        update_process.setArguments([str(TOOLS_HELPER), *args])
        update_process.start()

    def handle_update_output():
        raw = bytes(update_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if not raw:
            return
        append_update_log(raw)
        kind = update_operation.get("kind")
        joined = update_operation.get("last_chunk", "") + raw
        update_operation["last_chunk"] = joined[-8000:]
        if kind in {"install", "preflight", "download"}:
            if "LUNAOS_PHASE:PREPARING" in joined:
                update_progress.setRange(0, 100)
                update_progress.setValue(5)
                update_progress.setFormat("Preparing transaction…")
            patterns = re.findall(r"\b(?:upgrading|installing|reinstalling|downgrading)\s+([A-Za-z0-9@._+-]+)\s+\.\.\.", joined)
            for package in patterns:
                update_operation["seen"].add(package)
            if kind == "install" and update_operation["seen"]:
                total = max(1, len(update_entries))
                estimate = min(95, 5 + int(85 * len(update_operation["seen"]) / total))
                update_progress.setRange(0, 100)
                update_progress.setValue(estimate)
                update_progress.setFormat(f'Applying packages… {len(update_operation["seen"])} package action(s)')
            if "LUNAOS_PHASE:COMPLETE:100" in joined:
                update_progress.setRange(0, 100)
                update_progress.setValue(100)
                update_progress.setFormat("Complete")

    def finish_update_process(exit_code, _exit_status):
        kind = update_operation.get("kind")
        scheduled = update_operation.get("scheduled", False)
        update_operation["kind"] = ""
        update_operation["scheduled"] = False
        update_check_btn.setEnabled(True)
        update_download_btn.setEnabled(True)
        update_install_btn.setEnabled(True)
        output = update_logs.toPlainText()
        if exit_code != 0:
            update_progress.setRange(0, 100)
            update_progress.setFormat("Failed")
            update_status.setText("Update operation failed. Review the log before retrying.")
            QMessageBox.warning(window, "Update operation failed", (output[-5000:] or f"Process exit code: {exit_code}"))
            return
        update_progress.setRange(0, 100)
        update_progress.setValue(100)
        update_progress.setFormat("Complete")
        if kind == "install":
            update_status.setText("System upgrade completed. Check the log and reboot if required by the kernel or core system update.")
            QMessageBox.information(window, "LunaOS updates complete", "The system upgrade finished. Review the transaction log. A reboot may be necessary after kernel, graphics-driver, or core system updates.")
            refresh_updates()
        elif kind in {"preflight", "download"}:
            update_status.setText("Package downloads finished. Refreshing the update list and checking available changelogs…")
            refresh_updates()
            if kind == "preflight":
                QTimer.singleShot(250, lambda: begin_install(prepared=True, scheduled=scheduled))
        else:
            update_status.setText("Update operation completed.")
        update_operation["seen"] = set()

    def update_process_error(_error):
        if update_process.state() == QProcess.ProcessState.NotRunning and update_operation.get("kind"):
            update_check_btn.setEnabled(True)
            update_download_btn.setEnabled(True)
            update_install_btn.setEnabled(True)
            update_progress.setRange(0, 100)
            update_progress.setFormat("Failed to start")
            update_status.setText("Could not start the update helper. Check that PolicyKit and the LunaOS system-tools helper are installed.")
            update_operation["kind"] = ""

    update_process.readyReadStandardOutput.connect(handle_update_output)
    update_process.finished.connect(finish_update_process)
    update_process.errorOccurred.connect(update_process_error)

    def begin_install(prepared=False, scheduled=False):
        if not update_entries:
            refresh_updates()
            if not update_entries:
                if scheduled:
                    QMessageBox.information(window, "No updates", "There are no updates available to install.")
                return
        if not prepared:
            start_update_process("preflight", ["updates-download"], scheduled=scheduled)
            return
        critical = [entry for entry in update_entries if entry.get("critical")]
        if critical:
            names = "\n".join(
                f'• {entry["name"]}: {entry["old_version"]} → {entry["new_version"]} ({entry.get("category", "System")})'
                for entry in critical[:20]
            )
            if len(critical) > 20:
                names += f"\n…and {len(critical) - 20} more flagged updates."
            message = (
                "This update could break certain apps and features. If you experience any problem, please report the issue "
                "and the update/package name to LunaOS support.\n\n"
                "These updates affect the operating system, security, drivers, core libraries, or desktop foundation:\n"
                + names + "\n\n"
                + "Until the LunaOS website/Discord links are configured in this build, use the project's issue tracker:\n"
                + SUPPORT_ISSUES_URL + "\n\n"
                + "The transaction is a full system upgrade, as required by Arch Linux. Review the list and changelogs before continuing."
            )
            warning = QMessageBox(window)
            warning.setIcon(QMessageBox.Icon.Warning)
            warning.setWindowTitle("Important update compatibility warning")
            warning.setText(message)
            warning.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Apply)
            warning.setDefaultButton(QMessageBox.StandardButton.Cancel)
            if warning.exec() != QMessageBox.StandardButton.Apply:
                update_status.setText("Update installation cancelled. Downloaded packages remain cached.")
                return
        else:
            reply = QMessageBox.question(
                window, "Install system updates",
                f"Install {len(update_entries)} update(s) now? LunaOS will apply a full system upgrade to keep packages and libraries compatible.",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Apply,
                QMessageBox.StandardButton.Apply
            )
            if reply != QMessageBox.StandardButton.Apply:
                update_status.setText("Update installation cancelled. Downloaded packages remain cached.")
                return
        start_update_process("install", ["updates-install"], scheduled=scheduled)

    def download_updates():
        start_update_process("download", ["updates-download"])

    def report_problem():
        details = []
        for entry in update_entries:
            details.append(
                f'{entry.get("name", "unknown")}: {entry.get("old_version", "?")} -> {entry.get("new_version", "?")} '
                f'[{entry.get("category", "unknown")}]'
            )
        report = (
            "LunaOS update issue report\n"
            "Please describe what broke, the symptoms, and when it started.\n\n"
            "Updates shown at report time:\n" + ("\n".join(details) or "No pending updates were listed.") +
            "\n\nPlease include relevant lines from the Update Manager or /var/log/pacman.log."
        )
        QApplication.clipboard().setText(report)
        QDesktopServices.openUrl(QUrl(SUPPORT_ISSUES_URL))
        QMessageBox.information(window, "Update report prepared", "A list of update names and version changes has been copied to the clipboard. Paste it into the issue report and describe the problem.")

    def save_update_preferences():
        new_settings = {
            "schema": 1,
            "notifications_enabled": notifications_check.isChecked(),
            "background_downloads_enabled": background_downloads_check.isChecked(),
            "download_time": download_time_edit.time().toString("HH:mm"),
            "schedule_install_at": install_dt.dateTime().toString(Qt.DateFormat.ISODate) if schedule_install_check.isChecked() else None,
        }
        if schedule_install_check.isChecked() and install_dt.dateTime() <= QDateTime.currentDateTime().addSecs(60):
            QMessageBox.warning(window, "Invalid update schedule", "Choose an update time at least one minute in the future.")
            return
        if background_downloads_check.isChecked():
            if not QMessageBox.question(
                window, "Enable background downloads",
                "LunaOS will download repository update packages every day at the selected time. It will not install them automatically. "
                "Download notifications appear only when the notification setting is enabled. Continue?",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Yes
            ) == QMessageBox.StandardButton.Yes:
                return
            result = tool_action("download-schedule", [new_settings["download_time"]], timeout=120)
            okay, details = show_result(window, "Background update schedule", result)
            if not okay:
                new_settings["background_downloads_enabled"] = False
                background_downloads_check.setChecked(False)
                new_settings["background_downloads_enabled"] = False
                update_status.setText(details[-3000:])
                return
        else:
            timer_code, timer_output, _ = run_command(["/usr/bin/systemctl", "is-enabled", "lunaos-update-download.timer"], timeout=10)
            if timer_code == 0 or timer_output.strip() == "enabled":
                result = tool_action("download-schedule-disable", timeout=120)
                okay, details = show_result(window, "Background update schedule", result)
                if not okay:
                    update_status.setText(details[-3000:])
                    return

        UPDATE_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
        temp = UPDATE_SETTINGS.with_suffix(".tmp")
        temp.write_text(json.dumps(new_settings, indent=2) + "\n", encoding="utf-8")
        os.chmod(temp, 0o600)
        temp.replace(UPDATE_SETTINGS)

        if reboot_schedule_check.isChecked():
            warning = QMessageBox.warning(
                window, "Confirm automatic reboot",
                "This creates a system timer that will automatically restart LunaOS at the selected local time—even if apps are open. "
                "Save your work first. You can cancel this scheduled reboot from Control Center before it runs.",
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Cancel
            )
            if warning != QMessageBox.StandardButton.Yes:
                return
            when = reboot_dt.dateTime().toString("yyyy-MM-dd HH:mm")
            if reboot_dt.dateTime() <= QDateTime.currentDateTime().addSecs(120):
                QMessageBox.warning(window, "Invalid reboot schedule", "Choose a reboot time at least three minutes in the future.")
                return
            okay, details = show_result(window, "Reboot schedule", tool_action("reboot-schedule", [when], timeout=120))
            update_status.setText(details[-3000:])
            if not okay:
                return
        else:
            code, output, _ = run_command([str(TOOLS_HELPER), "reboot-schedule-status"], timeout=10)
            scheduled_reboot = False
            if code == 0:
                try:
                    scheduled_reboot = bool(json.loads(output).get("scheduled"))
                except ValueError:
                    pass
            if scheduled_reboot:
                okay, details = show_result(window, "Reboot schedule", tool_action("reboot-schedule-disable", timeout=120))
                if not okay:
                    update_status.setText(details[-3000:])
                    return
        update_status.setText(
            "Preferences saved. Background notifications " + ("enabled" if new_settings["notifications_enabled"] else "disabled") +
            "; background downloads " + ("scheduled daily at " + new_settings["download_time"] if new_settings["background_downloads_enabled"] else "disabled") + "."
        )

    def cancel_reboot_schedule():
        code, output, _ = run_command([str(TOOLS_HELPER), "reboot-schedule-status"], timeout=10)
        try:
            active = code == 0 and bool(json.loads(output).get("scheduled"))
        except ValueError:
            active = False
        if not active:
            QMessageBox.information(window, "No scheduled reboot", "There is no LunaOS-managed reboot timer to cancel.")
            reboot_schedule_check.setChecked(False)
            return
        reply = QMessageBox.question(
            window, "Cancel scheduled reboot",
            "Cancel the LunaOS-managed automatic reboot timer?",
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        okay, details = show_result(window, "Reboot schedule", tool_action("reboot-schedule-disable", timeout=120))
        if okay:
            reboot_schedule_check.setChecked(False)
            update_status.setText("Scheduled reboot cancelled.")
        else:
            update_status.setText(details[-3000:])

    update_list.currentItemChanged.connect(lambda item, _old: render_update_details(item.data(Qt.ItemDataRole.UserRole) if item else None))
    update_check_btn.clicked.connect(refresh_updates)
    update_download_btn.clicked.connect(download_updates)
    update_install_btn.clicked.connect(lambda: begin_install(prepared=False, scheduled=False))
    update_copy_btn.clicked.connect(report_problem)
    update_report_btn.clicked.connect(report_problem)
    schedule_save_btn.clicked.connect(save_update_preferences)
    schedule_cancel_reboot_btn.clicked.connect(cancel_reboot_schedule)
    tabs.addTab(updates_tab, "Updates")


    window.show()
    if "--updates" in APP_ARGS:
        tabs.setCurrentWidget(updates_tab)
    if "--scheduled-install" in APP_ARGS:
        update_operation["scheduled"] = True
        QTimer.singleShot(900, refresh_updates)
    else:
        QTimer.singleShot(900, refresh_updates)
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "LunaOS Control Center", str(exc))
        raise SystemExit(1)
