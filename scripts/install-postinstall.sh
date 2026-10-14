#!/usr/bin/env bash
# Optional setup for an installed Arch system. Does not partition disks.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$(id -u)" != 0 ]; then echo "Run with sudo: sudo $0" >&2; exit 1; fi
if [ ! -f /etc/arch-release ] || [ -e /run/archiso/bootmnt ]; then
  echo "Run only on installed Arch Linux, not the live ISO." >&2; exit 1
fi
MODULES=""
if printenv LUNAOS_MODULES >/dev/null 2>&1; then MODULES="$(printenv LUNAOS_MODULES)"; fi
if [ -z "$MODULES" ]; then MODULES="security,privacy,performance,gaming,coding,creator"; fi
SELECTED="base desktop"
for module in $(printf "%s" "$MODULES" | tr ',' ' '); do
  case "$module" in security|privacy|performance|gaming|coding|creator) SELECTED="$SELECTED $module" ;; *) echo "Unknown module: $module" >&2; exit 2 ;; esac
done
echo "This installs packages and desktop settings. No partitions will be changed."
echo "Modules: $SELECTED"
read -r -p 'Type YES to continue: ' answer
[ "$answer" = YES ] || exit 0
mkdir -p "$ROOT_DIR/build"
PACKAGES="$ROOT_DIR/build/packages.install"
: > "$PACKAGES"
for module in $SELECTED; do grep -v -E '^[[:space:]]*(#|$)' "$ROOT_DIR/config/packages/$module.packages" >> "$PACKAGES" || true; done
sort -u "$PACKAGES" -o "$PACKAGES"
xargs -r pacman -Syu --needed < "$PACKAGES"
install -d /usr/share/lunaos/profiles /usr/share/backgrounds/lunaos /usr/share/applications /usr/share/polkit-1/actions /usr/lib/lunaos /usr/local/bin
cp "$ROOT_DIR"/config/profiles/*.toml /usr/share/lunaos/profiles/
install -m 0644 "$ROOT_DIR/config/modules.toml" /usr/share/lunaos/modules.toml
printf '{"included_modules":[' > /usr/share/lunaos/build-modules.json
separator=""
for module in $SELECTED; do printf '%s"%s"' "$separator" "$module" >> /usr/share/lunaos/build-modules.json; separator=","; done
printf ']}\n' >> /usr/share/lunaos/build-modules.json
install -m 0644 "$ROOT_DIR/assets/lunaos-wallpaper.svg" /usr/share/backgrounds/lunaos/lunaos-wallpaper.svg
install -m 0755 "$ROOT_DIR/apps/control-center/lunaos-control-center.py" /usr/lib/lunaos/lunaos-control-center.py
install -m 0755 "$ROOT_DIR/apps/control-center/lunaos-profile-apply" /usr/lib/lunaos/lunaos-profile-apply
install -m 0755 "$ROOT_DIR/apps/control-center/lunaos-game-run" /usr/local/bin/lunaos-game-run
install -m 0755 "$ROOT_DIR/packaging/archiso/overlay/airootfs/usr/local/bin/lunaos-control-center" /usr/local/bin/lunaos-control-center
install -m 0644 "$ROOT_DIR/packaging/archiso/overlay/airootfs/usr/share/applications/lunaos-control-center.desktop" /usr/share/applications/lunaos-control-center.desktop
install -m 0644 "$ROOT_DIR/packaging/archiso/overlay/airootfs/usr/share/polkit-1/actions/org.lunaos.controlcenter.policy" /usr/share/polkit-1/actions/org.lunaos.controlcenter.policy
install -m 0644 "$ROOT_DIR/packaging/archiso/overlay/airootfs/etc/sddm.conf.d/10-lunaos.conf" /etc/sddm.conf.d/10-lunaos.conf
systemctl enable NetworkManager.service sddm.service bluetooth.service
case " $SELECTED " in *" security "*) systemctl enable firewalld.service ;; esac
echo "LunaOS setup done. Reboot when ready; no partitions were modified."
