#!/usr/bin/env python3
"""LunaOS background update watcher; honors the user's notification preference."""
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

SETTINGS = Path.home() / ".config/lunaos/update-settings.json"
AGENT_STATE = Path.home() / ".config/lunaos/update-agent-state.json"
DOWNLOAD_STATE = Path("/var/lib/lunaos/update-download-state.json")
CONTROL_CENTER = "/usr/local/bin/lunaos-control-center"


def read_json(path, default):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else default
    except (OSError, ValueError):
        return default


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def open_updates(scheduled=False):
    args = [CONTROL_CENTER, "--updates"]
    if scheduled:
        args.append("--scheduled-install")
    try:
        subprocess.Popen(args, start_new_session=True)
    except OSError:
        pass


def main():
    app = QApplication([sys.argv[0]])
    app.setApplicationName("LunaOS Update Agent")
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return 0

    tray = QSystemTrayIcon(QIcon.fromTheme("system-software-update"))
    tray.setToolTip("LunaOS updates")
    menu = QMenu()
    open_action = QAction("Open Update Manager", menu)
    check_action = QAction("Check / review updates", menu)
    menu.addAction(open_action)
    menu.addAction(check_action)
    menu.addSeparator()
    exit_action = QAction("Stop update watcher", menu)
    menu.addAction(exit_action)
    tray.setContextMenu(menu)
    open_action.triggered.connect(lambda: open_updates(False))
    check_action.triggered.connect(lambda: open_updates(False))
    exit_action.triggered.connect(app.quit)
    tray.activated.connect(lambda reason: open_updates(False) if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    def poll():
        settings = read_json(SETTINGS, {"notifications_enabled": True})
        notifications = settings.get("notifications_enabled", True) is True
        now = int(time.time())

        # A scheduled install launches the manager to present the update-specific warning.
        scheduled_value = settings.get("schedule_install_at")
        if isinstance(scheduled_value, str) and scheduled_value:
            try:
                scheduled_time = datetime.fromisoformat(scheduled_value).timestamp()
            except ValueError:
                scheduled_time = None
            if scheduled_time is not None and now >= scheduled_time:
                settings["schedule_install_at"] = None
                settings["schedule_install_consumed_at"] = now
                atomic_json(SETTINGS, settings)
                open_updates(scheduled=True)

        downloaded = read_json(DOWNLOAD_STATE, {})
        agent_state = read_json(AGENT_STATE, {})
        downloaded_at = downloaded.get("updated_at", 0)
        last_notified = agent_state.get("last_notified_download_at", 0)
        if notifications and downloaded.get("ready") is True and isinstance(downloaded_at, int) and downloaded_at > last_notified:
            count = len(downloaded.get("packages", []))
            tray.showMessage(
                "LunaOS updates are ready",
                f"{count} update(s) have downloaded and are ready to review in the Update Manager.",
                QSystemTrayIcon.MessageIcon.Information,
                12000,
            )
            agent_state["last_notified_download_at"] = downloaded_at
            atomic_json(AGENT_STATE, agent_state)

    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(30_000)
    QTimer.singleShot(3000, poll)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
