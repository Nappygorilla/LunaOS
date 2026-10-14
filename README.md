# LunaOS

**A modular Arch Linux desktop with KDE Plasma and a Windows-familiar workflow.**

LunaOS aims to keep Linux approachable while letting users opt into security, privacy, performance, gaming, coding, and creator tools independently.

> **Development status:** experimental. The repository source has not yet been built into a verified release ISO. Test in a disposable virtual machine before installing on real hardware.

## Goals

- Modular package modules can be selected during ISO builds.
- A native desktop Control Center manages profiles and security, privacy, performance, and GameMode switches.
- One-click presets: Balanced, Gaming, Coding, Creator, Privacy-first, Secure workstation, and Battery saver.
- System changes are allowlisted and reversible. Profiles are declarative TOML, not executable scripts.

## Repository structure

    apps/control-center/       Qt Control Center and privileged helper
    assets/                    LunaOS wallpaper and visual assets
    config/packages/           Build-time package modules
    config/profiles/           Declarative TOML presets
    docs/                      Architecture, profiles, security, build guide
    packaging/archiso/overlay/ Live image config and launchers
    scripts/                   Checks, tests, optional installed-system setup
    build-lunaos.sh            ArchISO ISO build entry point

## Build on Arch Linux

Use an x86_64 Arch Linux PC or VM with internet, the official archiso package, about 20–30 GB free space, and 8 GB RAM recommended.

    sudo pacman -Syu --needed archiso
    bash scripts/check-project.sh
    ./build-lunaos.sh

The ISO is written to build/out/. The builder copies the installed official ArchISO releng profile, adds selected packages and the LunaOS overlay, and invokes mkarchiso. It does not flash USB drives or partition disks.

Choose optional package modules explicitly:

    LUNAOS_MODULES=security,privacy,performance,gaming,coding ./build-lunaos.sh
    LUNAOS_MODULES=security,privacy ./build-lunaos.sh

Base and desktop are always included. Optional module IDs are security, privacy, performance, gaming, coding, and creator. If an optional module is not built, Control Center marks its switch unavailable.

## Test before installing

    sudo pacman -S --needed qemu-desktop edk2-ovmf
    run_archiso -u -i build/out/lunaos-0.1.0-x86_64.iso

Check boot, SDDM, KDE Plasma, networking, sound, Control Center, profile switching, and missing-module messages. The installer shortcut opens guided Archinstall, not a custom one-click installer. Review every disk choice carefully.

## Control Center modules

- **Security:** firewalld and a small allowlisted set of kernel information-hardening sysctls.
- **Privacy:** managed Firefox telemetry, studies, and Pocket policies; unrelated policy keys are preserved.
- **Performance:** power-profiles-daemon, when installed, and conservative vm.swappiness tuning.
- **GameMode:** a per-user toggle for the lunaos-game-run wrapper, which invokes gamemoderun when enabled and available.

These settings are not guaranteed FPS increases. Kernel command-line changes are not silently applied; future boot-parameter changes must preview exact edits and require explicit reboot confirmation.

## Control Center tools

The Control Center also includes dedicated **Power**, **Cooling**, **Snapshots**, and **Developer tools** tabs:

- **Power:** choose power-saver, balanced, or performance where the hardware and power-profiles-daemon support it.
- **Cooling:** inspect lm_sensors readings, run the guided pwmconfig setup where supported, and enable/stop a configured fancontrol service. Hardware fan control is not available on every machine; default firmware cooling remains the fallback.
- **Snapshots:** install Timeshift, create and list restore points, or open its full manager to set schedules and review restores. Snapshot setup needs a compatible destination and filesystem layout.
- **Developer tools:** install Geany, KDevelop, Qt Creator, GNOME Builder, language toolchains, or Docker/Compose/Buildx from fixed official Arch package bundles. Package installation also performs the system upgrade required by Arch package management.

Docker is not silently granted root-equivalent group access. Software fan control, snapshot creation, and system package installation require administrator authentication. The ISO and hardware behavior still need VM and real-device testing before stable release.

## Development checks

    bash scripts/check-project.sh
    python scripts/test-profiles.py
    python scripts/test-control-center.py

Read docs/security-model.md before changing the privileged helper. LunaOS is an independent experimental project, not an official Arch Linux or KDE release.

References: https://wiki.archlinux.org/title/Archiso · https://doc.qt.io/qtforpython-6/ · https://www.freedesktop.org/software/polkit/docs/latest/


## Optional setup and account permissions

The LunaOS installer lets users skip desktop personalization and personal-account creation independently. Disk selection remains manual. If account creation is skipped, the installed machine uses an auto-login luna-guest account that is not in wheel and has no sudo privileges. A first-run screen can create a standard non-admin personal account later; it does not grant administrator access.

Administrator permission is opt-in during installation. If a user skips the account step, LunaOS does not create an administrator account behind their back. To have administrator access, select personal account creation in the installer and explicitly enable the administrator option.

Read docs/first-boot-and-accounts.md and docs/security-model.md before testing. This feature is experimental and needs an end-to-end Archinstall VM test.
