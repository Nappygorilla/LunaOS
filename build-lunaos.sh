#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT_DIR/build"
if printenv LUNAOS_BUILD_DIR >/dev/null 2>&1; then BUILD_DIR="$(printenv LUNAOS_BUILD_DIR)"; fi
MODULES=""
if printenv LUNAOS_MODULES >/dev/null 2>&1; then MODULES="$(printenv LUNAOS_MODULES)"; fi
if [ -z "$MODULES" ]; then MODULES="security,privacy,performance,gaming,coding,creator"; fi
PROFILE="$BUILD_DIR/profile"
WORK_DIR="$BUILD_DIR/work"
OUT_DIR="$BUILD_DIR/out"

if [ "$(uname -m)" != "x86_64" ] || [ ! -f /etc/arch-release ]; then
  echo "Build on an x86_64 Arch Linux host or VM." >&2; exit 1
fi
if ! command -v mkarchiso >/dev/null 2>&1 || [ ! -d /usr/share/archiso/configs/releng ]; then
  echo "Install archiso first: sudo pacman -Syu --needed archiso" >&2; exit 1
fi
SELECTED="base desktop"
for module in $(printf "%s" "$MODULES" | tr ',' ' '); do
  [ -z "$module" ] && continue
  case "$module" in security|privacy|performance|gaming|coding|creator) ;; *) echo "Unknown module: $module" >&2; exit 2 ;; esac
  case " $SELECTED " in *" $module "*) ;; *) SELECTED="$SELECTED $module" ;; esac
done
mkdir -p "$BUILD_DIR" "$OUT_DIR"
rm -rf "$PROFILE" "$WORK_DIR"
cp -a /usr/share/archiso/configs/releng "$PROFILE"
sed -i -E \
  -e 's/^iso_name=.*/iso_name="lunaos"/' \
  -e 's/^iso_label=.*/iso_label="LUNAOS_010"/' \
  -e 's/^iso_publisher=.*/iso_publisher="LunaOS Project"/' \
  -e 's/^iso_application=.*/iso_application="LunaOS KDE desktop live image"/' \
  -e 's/^iso_version=.*/iso_version="0.1.0"/' \
  -e 's/^install_dir=.*/install_dir="lunaos"/' "$PROFILE/profiledef.sh"

PACKAGE_TMP="$BUILD_DIR/packages.tmp"
: > "$PACKAGE_TMP"
for module in $SELECTED; do
  file="$ROOT_DIR/config/packages/$module.packages"
  [ -f "$file" ] || { echo "Missing package file: $file" >&2; exit 1; }
  grep -v -E '^[[:space:]]*(#|$)' "$file" >> "$PACKAGE_TMP" || true
done
sort -u "$PACKAGE_TMP" -o "$PACKAGE_TMP"
while IFS= read -r package; do
  grep -Fxq "$package" "$PROFILE/packages.x86_64" || printf '%s\n' "$package" >> "$PROFILE/packages.x86_64"
done < "$PACKAGE_TMP"
rm -f "$PACKAGE_TMP"

cp -a "$ROOT_DIR/packaging/archiso/overlay/airootfs/." "$PROFILE/airootfs/"
install -d "$PROFILE/airootfs/usr/share/lunaos/profiles" "$PROFILE/airootfs/usr/share/lunaos/package-modules" "$PROFILE/airootfs/usr/lib/lunaos" "$PROFILE/airootfs/usr/share/backgrounds/lunaos"
cp "$ROOT_DIR"/config/profiles/*.toml "$PROFILE/airootfs/usr/share/lunaos/profiles/"
install -m 0644 "$ROOT_DIR/config/modules.toml" "$PROFILE/airootfs/usr/share/lunaos/modules.toml"
install -m 0644 "$ROOT_DIR/config/source-revision.txt" "$PROFILE/airootfs/usr/share/lunaos/source-revision"
cp "$ROOT_DIR"/config/packages/*.packages "$PROFILE/airootfs/usr/share/lunaos/package-modules/"
{
  printf '{"included_modules":['
  separator=""
  for module in $SELECTED; do printf '%s"%s"' "$separator" "$module"; separator=","; done
  printf ']}\n'
} > "$PROFILE/airootfs/usr/share/lunaos/build-modules.json"
install -m 0755 "$ROOT_DIR/apps/control-center/lunaos-control-center.py" "$PROFILE/airootfs/usr/lib/lunaos/lunaos-control-center.py"
install -m 0755 "$ROOT_DIR/apps/control-center/lunaos-profile-apply" "$PROFILE/airootfs/usr/lib/lunaos/lunaos-profile-apply"
install -m 0755 "$ROOT_DIR/apps/setup/lunaos-installer-setup.py" "$PROFILE/airootfs/usr/lib/lunaos/lunaos-installer-setup.py"
install -m 0755 "$ROOT_DIR/apps/control-center/lunaos-game-run" "$PROFILE/airootfs/usr/local/bin/lunaos-game-run"
install -m 0644 "$ROOT_DIR/assets/lunaos-wallpaper.svg" "$PROFILE/airootfs/usr/share/backgrounds/lunaos/lunaos-wallpaper.svg"
cat >> "$PROFILE/profiledef.sh" <<'PERMISSIONS'

file_permissions["/usr/local/bin/lunaos-live-setup"]="0:0:755"
file_permissions["/usr/local/bin/lunaos-first-login"]="0:0:755"
file_permissions["/usr/local/bin/lunaos-installer-launcher"]="0:0:755"
file_permissions["/usr/local/bin/lunaos-control-center"]="0:0:755"
file_permissions["/usr/local/bin/lunaos-game-run"]="0:0:755"
file_permissions["/usr/lib/lunaos/lunaos-control-center.py"]="0:0:755"
file_permissions["/usr/lib/lunaos/lunaos-profile-apply"]="0:0:755"
file_permissions["/usr/lib/lunaos/lunaos-installer-setup.py"]="0:0:755"
file_permissions["/usr/local/bin/lunaos-firstboot-setup"]="0:0:755"
file_permissions["/etc/sudoers.d/10-lunaos-live"]="0:0:440"
file_permissions["/etc/skel/Desktop/LunaOS Control Center.desktop"]="0:0:755"
file_permissions["/etc/skel/Desktop/Install LunaOS.desktop"]="0:0:755"
file_permissions["/etc/skel/Desktop/LunaOS Welcome.desktop"]="0:0:755"
PERMISSIONS
SYSTEMD="$PROFILE/airootfs/etc/systemd/system"
mkdir -p "$SYSTEMD/multi-user.target.wants"
ln -sfn /usr/lib/systemd/system/graphical.target "$SYSTEMD/default.target"
ln -sfn /usr/lib/systemd/system/sddm.service "$SYSTEMD/display-manager.service"
ln -sfn ../lunaos-live-setup.service "$SYSTEMD/multi-user.target.wants/lunaos-live-setup.service"
ln -sfn /usr/lib/systemd/system/NetworkManager.service "$SYSTEMD/multi-user.target.wants/NetworkManager.service"
ln -sfn /usr/lib/systemd/system/bluetooth.service "$SYSTEMD/multi-user.target.wants/bluetooth.service"
case " $SELECTED " in *" security "*) ln -sfn /usr/lib/systemd/system/firewalld.service "$SYSTEMD/multi-user.target.wants/firewalld.service" ;; esac
echo "LunaOS modules: $SELECTED"
if printenv SUDO_USER >/dev/null 2>&1; then user="$(printenv SUDO_USER)"; uid="$(id -u "$user")"; gid="$(id -g "$user")"; else uid="$(id -u)"; gid="$(id -g)"; fi
sudo mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE"
sudo chown -R "$uid:$gid" "$OUT_DIR"
echo "ISO output: $OUT_DIR"
find "$OUT_DIR" -maxdepth 1 -type f -name '*.iso' -printf '%f (%s bytes)\n'
