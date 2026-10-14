#!/usr/bin/env bash
# Runs as an Archinstall post-install command inside the target system.
set -euo pipefail
MODE="$1"
APPLY_SETTINGS="$2"
PROFILE_ID="$3"
SOURCE_REV="$4"
case "$MODE" in personal|guest) ;; *) echo "Invalid LunaOS account mode." >&2; exit 2 ;; esac
case "$APPLY_SETTINGS" in yes|no) ;; *) echo "Invalid desktop settings choice." >&2; exit 2 ;; esac
case "$PROFILE_ID" in balanced|gaming|coding|creator|privacy|secure|battery-saver) ;; *) echo "Invalid default profile." >&2; exit 2 ;; esac
[[ "$SOURCE_REV" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid pinned LunaOS source revision." >&2; exit 2; }
BASE_URL="https://raw.githubusercontent.com/Nappygorilla/LunaOS/$SOURCE_REV"
TMP_DIR="$(mktemp -d /tmp/lunaos-target-setup.XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT
fetch() {
  local repo_path="$1" output_path="$2" mode="$3"
  curl -fsSL --proto '=https' --tlsv1.2 "$BASE_URL/$repo_path" -o "$TMP_DIR/payload"
  install -D -m "$mode" "$TMP_DIR/payload" "$output_path"
}
install -d /usr/share/lunaos/profiles /usr/share/lunaos/package-modules /usr/lib/lunaos /usr/local/bin /usr/share/backgrounds/lunaos /usr/share/applications /usr/share/polkit-1/actions /usr/share/lunaos/installer
for name in balanced gaming coding creator privacy secure battery-saver; do
  fetch "config/profiles/$name.toml" "/usr/share/lunaos/profiles/$name.toml" 0644
done
for name in base desktop security privacy performance gaming coding creator; do
  fetch "config/packages/$name.packages" "/usr/share/lunaos/package-modules/$name.packages" 0644
done
fetch "config/modules.toml" /usr/share/lunaos/modules.toml 0644
fetch "config/build-modules.default.json" /usr/share/lunaos/build-modules.json 0644
fetch "assets/lunaos-wallpaper.svg" /usr/share/backgrounds/lunaos/lunaos-wallpaper.svg 0644
fetch "apps/control-center/lunaos-control-center.py" /usr/lib/lunaos/lunaos-control-center.py 0755
fetch "apps/control-center/lunaos-profile-apply" /usr/lib/lunaos/lunaos-profile-apply 0755
fetch "apps/control-center/lunaos-game-run" /usr/local/bin/lunaos-game-run 0755
fetch "apps/setup/lunaos-firstboot-setup.py" /usr/lib/lunaos/lunaos-firstboot-setup.py 0755
fetch "apps/setup/lunaos-setup-user-helper" /usr/lib/lunaos/lunaos-setup-user-helper 0755
fetch "packaging/archiso/overlay/airootfs/usr/share/polkit-1/actions/org.lunaos.setup-user.policy" /usr/share/polkit-1/actions/org.lunaos.setup-user.policy 0644
fetch "packaging/archiso/overlay/airootfs/usr/share/polkit-1/actions/org.lunaos.controlcenter.policy" /usr/share/polkit-1/actions/org.lunaos.controlcenter.policy 0644
fetch "packaging/archiso/overlay/airootfs/usr/share/applications/lunaos-control-center.desktop" /usr/share/applications/lunaos-control-center.desktop 0644
fetch "packaging/archiso/overlay/airootfs/usr/share/applications/lunaos-firstboot-setup.desktop" /usr/share/applications/lunaos-firstboot-setup.desktop 0644
fetch "packaging/archiso/overlay/airootfs/usr/local/bin/lunaos-control-center" /usr/local/bin/lunaos-control-center 0755
fetch "packaging/archiso/overlay/airootfs/usr/local/bin/lunaos-firstboot-setup" /usr/local/bin/lunaos-firstboot-setup 0755

# Never grant the restricted guest account admin group membership.
if [[ "$MODE" == "guest" ]]; then
  if ! id luna-guest >/dev/null 2>&1; then
    echo "The requested guest account was not created by Archinstall." >&2
    exit 1
  fi
  if id -nG luna-guest | tr ' ' '\n' | grep -qx wheel; then
    echo "Refusing to continue: luna-guest is unexpectedly in wheel." >&2
    exit 1
  fi
  install -d /etc/sddm.conf.d /home/luna-guest/.config/autostart /etc/lunaos
  cat > /etc/sddm.conf.d/20-lunaos-guest-autologin.conf <<'SDDM'
[Autologin]
User=luna-guest
Session=plasma.desktop
Relogin=false
SDDM
  chown root:root /etc/sddm.conf.d/20-lunaos-guest-autologin.conf
  chmod 0644 /etc/sddm.conf.d/20-lunaos-guest-autologin.conf
  fetch "packaging/archiso/overlay/airootfs/usr/share/applications/lunaos-firstboot-setup.desktop" /home/luna-guest/.config/autostart/lunaos-firstboot-setup.desktop 0644
  chown -R luna-guest:luna-guest /home/luna-guest/.config
else
  rm -f /etc/sddm.conf.d/20-lunaos-guest-autologin.conf
fi

if [[ "$APPLY_SETTINGS" == "yes" ]]; then
  fetch "packaging/archiso/overlay/airootfs/etc/skel/.config/kdeglobals" /etc/skel/.config/kdeglobals 0644
  fetch "packaging/archiso/overlay/airootfs/etc/skel/.config/kwinrc" /etc/skel/.config/kwinrc 0644
  install -d /etc/lunaos
  printf '%s\n' "$PROFILE_ID" > /etc/lunaos/default-profile
  chmod 0644 /etc/lunaos/default-profile
  for home in /home/*; do
    [[ -d "$home" ]] || continue
    [[ -e "$home/.config/kdeglobals" ]] || install -D -m 0644 /etc/skel/.config/kdeglobals "$home/.config/kdeglobals"
    [[ -e "$home/.config/kwinrc" ]] || install -D -m 0644 /etc/skel/.config/kwinrc "$home/.config/kwinrc"
    [[ -e "$home/.config/autostart/lunaos-first-login.desktop" ]] || fetch "packaging/archiso/overlay/airootfs/etc/skel/.config/autostart/lunaos-first-login.desktop" "$home/.config/autostart/lunaos-first-login.desktop" 0644
    owner="$(stat -c '%U:%G' "$home")"
    chown "$owner" "$home/.config/kdeglobals" "$home/.config/kwinrc" "$home/.config/autostart/lunaos-first-login.desktop" 2>/dev/null || true
  done
fi

cat > /usr/share/lunaos/lunaos-release <<'RELEASE'
LunaOS 0.1.0
Base: Arch Linux
Desktop: KDE Plasma
Status: experimental developer preview
RELEASE
printf '%s\n' "$SOURCE_REV" > /usr/share/lunaos/source-revision
echo "LunaOS first-boot integration installed. Account mode: $MODE; desktop personalization: $APPLY_SETTINGS."
