# Architecture

LunaOS separates ISO building, package modules, declarative runtime profiles, and privileged actions.

    build-lunaos.sh
      config/packages/*.packages -> selected package modules
      config/profiles/*.toml     -> user-facing presets
      packaging/archiso/overlay  -> live-session setup and launchers

    KDE desktop
      LunaOS Control Center (PySide6)
        -> ordinary user process with profiles and module switches
        -> pkexec -> lunaos-profile-apply (profile allowlist)
        -> pkexec -> lunaos-system-tools (fixed bundles and bounded system actions)
        -> power profiles, detected fan sensors/configuration, Timeshift, pacman bundles

Build-time modules determine which software is included. Runtime toggles change supported behavior and do not uninstall apps. If a module was excluded at build time, the UI marks its switch unavailable.

Before a stable release, add transactional rollback for partial failures, a diff preview, a reset command, broader hardware tests, and independent review of privileged code.
