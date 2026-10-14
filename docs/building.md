# Build the ISO

Requirements: x86_64 Arch Linux host or VM, current archiso package, internet access, roughly 20–30 GB free space, and 8 GB RAM recommended.

    sudo pacman -Syu --needed archiso
    bash scripts/check-project.sh
    ./build-lunaos.sh

The builder copies the official releng profile, adds the LunaOS overlay and selected modules, then invokes mkarchiso. It never flashes USB media.

LUNAOS_MODULES is a comma-separated list of security, privacy, performance, gaming, coding, and creator. Base and desktop are always included. If unset, all optional modules are selected.

Test in a VM first:

    sudo pacman -S --needed qemu-desktop edk2-ovmf
    run_archiso -u -i build/out/lunaos-0.1.0-x86_64.iso

Check boot, display manager, sound, Wi-Fi, Control Center, profile behavior, and missing-module messages. The live installer is guided Archinstall; review the target disk carefully.


## Setup choices

The LunaOS installer launcher displays optional desktop personalization and account creation settings. Unchecking desktop defaults skips the Luna theme and wallpaper configuration; KDE Plasma itself is still installed. Unchecking account creation selects a generated, non-admin luna-guest account and random undisclosed credential, then enables SDDM guest autologin in the installed system. The setup script never preselects a target disk: Archinstall must still prompt for and confirm the disk layout.

A standard personal account can be created later from the guest first-run wizard, but administrator permissions cannot be granted from that guest helper. To create an administrator account, choose account creation during installation and explicitly enable the administrator option.

Run through the real install flow in a disposable VM before using the image on a physical drive. The post-install integration script is fetched from a pinned LunaOS commit over HTTPS; building the ISO requires a valid 40-character source revision in config/source-revision.txt.
