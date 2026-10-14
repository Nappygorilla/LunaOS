# LunaOS setup flow

The installer setup screen lets users skip desktop personalization and/or personal-account creation.

- If a personal account is created in the installer, administrator access is controlled by the explicit checkbox and Archinstall credential configuration.
- If account creation is skipped, the installed system receives luna-guest, configured for SDDM auto-login but not placed in wheel; its password is randomly generated and not shown. A random unknown root credential is used so there is no implicit root-login path.
- The first-run guest wizard can later create one personal account through a narrowly scoped PolicyKit helper. It accepts only a username, password, and administrator boolean; it never executes user-supplied commands. The helper refuses to create a second first account when a personal account or its lock marker exists.
- Skipping first-run account creation leaves the session as a standard non-admin guest. System-wide settings and package installation remain unavailable until an administrator account exists.
- Desktop personalization is user-scoped and optional. Disk selection always remains in Archinstall's interactive flow; no drive or partition layout is preselected by this project.

The guest setup authorization exists only to create the first account on a newly installed system. Review it in a clean VM before any public release.
