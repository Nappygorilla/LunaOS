# Profiles and modules

Seven TOML presets ship with LunaOS: Balanced, Gaming, Coding, Creator, Privacy-first, Secure workstation, and Battery saver.

- **Security:** firewalld and the allowlisted kernel.kptr_restrict / kernel.dmesg_restrict values. Turning Security off explicitly stops/disables firewalld and restores baseline values for managed keys.
- **Privacy:** Firefox DisableTelemetry, DisableFirefoxStudies, and DisablePocket policies. Unrelated keys are preserved; original managed values are restored when disabled.
- **Performance:** power-profiles-daemon (when installed) and vm.swappiness. Values are conservative and workload-dependent, not guaranteed FPS gains.
- **GameMode:** per-user switch; launch a game through lunaos-game-run COMMAND [ARGS...] to use gamemoderun.
- **Coding and Creator:** build-time software bundles, not run-time uninstallers.

Add a profile with a unique ID matching its filename, only supported keys, and a matching test. Never place commands or executable scripts in TOML profile data.
