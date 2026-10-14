# Security model

The GUI runs as a normal user and requests elevation through PolicyKit. The helper accepts a known profile ID and four on/off overrides, then reads only packaged profiles from /usr/share/lunaos/profiles.

Current allowlists:
- Service: firewalld.service only.
- Sysctl: vm.swappiness (0–100), kernel.kptr_restrict (0–2), kernel.dmesg_restrict (0–1).
- Power profile: power-saver, balanced, performance.
- Firefox policy keys: DisableTelemetry, DisableFirefoxStudies, DisablePocket.

All subprocess calls use argument arrays and timeouts. Do not add shell=True, bash -c, arbitrary systemctl names, arbitrary sysctl keys, remote commands, or shell snippets in profile files.

The helper records original values in /var/lib/lunaos/control-center-state.json. Its managed sysctl file is /etc/sysctl.d/99-lunaos-profile.conf; if that path exists and is not marked as LunaOS-owned, the helper refuses to overwrite it. This is a development baseline, not a full system backup or a security audit. Add and test transactional rollback before a stable release.
