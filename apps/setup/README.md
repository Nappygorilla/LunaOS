# LunaOS setup flow

- Optional desktop personalization and optional personal-account creation are separate choices.
- If a personal account is created during installation, sudo access is controlled by the explicit administrator checkbox.
- If account creation is skipped, the installed system receives a restricted luna-guest account, with an undisclosed random credential and no wheel/sudo privileges.
- The first-run wizard can create one standard personal account later, but that helper can never grant administrator rights. To get admin access, the user must explicitly choose account creation and administrator access during installation.
- Skipping first-run personalization leaves the current desktop settings unchanged.
- Disk selection stays interactive. No drive or partition layout is preselected.
