# Security model

The GUI runs as a normal user and requests elevation through PolicyKit. The profile helper accepts a known profile ID and four on/off overrides, then reads only packaged profiles from /usr/share/lunaos/profiles. The separate system-tools helper uses fixed operation names and allowlists for package bundles, update transactions, download scheduling, and reboot scheduling.

Current allowlists:
- Profile service: firewalld.service.
- System-tools service names are hard-coded in individual actions: power-profiles-daemon.service, fancontrol.service, cronie.service, and docker.service.
- Package installs use fixed bundle IDs and package lists from official Arch repositories; arbitrary package names and shell commands are not accepted.
- Sysctl: vm.swappiness (0–100), kernel.kptr_restrict (0–2), kernel.dmesg_restrict (0–1).
- Power profile: power-saver, balanced, performance.
- Firefox policy keys: DisableTelemetry, DisableFirefoxStudies, DisablePocket.

All subprocess calls use argument arrays and timeouts. The separate system-tools helper accepts only fixed power modes, fixed package bundles, and named fan/snapshot actions. Do not add shell=True, bash -c, arbitrary systemctl names, arbitrary package names, remote commands, or shell snippets in profile files.

Fan control is hardware-dependent. LunaOS only enables fancontrol when an explicit configuration file exists and presents a warning before setup; incorrect PWM configuration can damage hardware. Timeshift snapshot creation requires an initialized snapshot destination. Restore and scheduling remain in the upstream Timeshift manager rather than being run unattended by LunaOS. Docker is not automatically granted to the ordinary user because membership in the docker group is root-equivalent.

The profile helper records original values in /var/lib/lunaos/control-center-state.json. The update downloader writes a non-secret summary to /var/lib/lunaos/update-download-state.json; the session watcher only displays desktop notifications when the user setting is enabled. Scheduled background downloads fetch packages but do not install them. Applying updates is a full pacman system-upgrade transaction and the update review flow shows the warning for detected security, OS, driver, core-library, and desktop-foundation changes. Package-provided changelogs are displayed when available; absent notes are not fabricated. Reboot scheduling uses fixed LunaOS-managed systemd unit names and validates the chosen local date/time. The UI asks for explicit consent before activating an automatic reboot timer. Its managed sysctl file is /etc/sysctl.d/99-lunaos-profile.conf; if that path exists and is not marked as LunaOS-owned, the helper refuses to overwrite it. This is a development baseline, not a full system backup or a security audit. Add and test transactional rollback before a stable release.


## Installer and guest account

The live installer account is not in the wheel group. Its sudoers allowance is limited to launching /usr/bin/archinstall; the live ISO is an installation environment, not a trusted multi-user security boundary. The installed guest account is separately created by Archinstall with sudo=false and is explicitly checked not to be in wheel before SDDM autologin is enabled.

If personal-account creation is skipped, no administrator account is created automatically. The first-run helper has one purpose: create one standard personal user from a bounded JSON request. It never accepts shell commands, arbitrary groups, an administrator flag, or sysctl/service settings. It never modifies wheel or sudoers. The PolicyKit action is intentionally able to create only a non-admin account; administrative account creation must be explicitly selected during installation.
