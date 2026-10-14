# First-boot setup and account permissions

## During installation

The LunaOS setup screen can skip desktop personalization and/or personal-account creation. The setup UI supplies a credential to Archinstall only if the user elects to create an account. Credentials are hashed before writing to a mode-0600 file under /run, and temporary files are removed after the installer exits.

If the account step is skipped, Archinstall receives a generated random credential for the luna-guest account, with sudo=false. It also receives an unknown random root credential, preventing an implicit root-login path. The post-install command enables SDDM autologin for luna-guest and verifies that it is not in wheel. This account is for limited desktop use, not system administration.

The installer never preselects disk_config or a drive. The user must still select and confirm partitioning inside Archinstall.

## First-run after installation

When account creation was skipped, the guest session launches LunaOS First-run Setup once. The user may apply the dark theme and wallpaper, or skip customization; this only changes that user's desktop config. They can also skip personal-account creation and continue using the restricted guest account.

The setup application can create one standard personal account through a narrow PolicyKit action. The helper accepts a validated username and password via standard input. It does not accept arbitrary shell commands, group lists, or an administrator flag. It never adds accounts to wheel and never edits sudoers. It refuses to create a personal account if one already exists and writes a lock marker after success.

To get administrator privileges, users must create a personal account during installation and explicitly enable the administrator option. If that step was skipped, the restricted guest and any later first-run personal account remain non-admin; system-wide changes and package installation are unavailable until the system is deliberately reconfigured by an administrator.

## Testing

Test both paths in a disposable QEMU VM:
1. Create a personal user in the installer and verify the administrator checkbox controls its sudo access.
2. Skip user creation; verify automatic guest login works and the guest is not in wheel.
3. Skip personalization and confirm the wizard leaves current desktop settings unchanged.
4. Create a first standard account from the guest wizard; verify it cannot use sudo and the helper refuses to create another first account.
5. Confirm Archinstall still asks for disk selection and the installer config contains no hardcoded drive.

This is experimental. The install post-command downloads files from a pinned LunaOS Git commit over HTTPS and must be tested end-to-end before release.
