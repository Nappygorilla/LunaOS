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
