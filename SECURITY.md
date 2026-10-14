# Security policy

LunaOS is experimental and is not suitable for security-critical deployments yet. Report security-sensitive issues privately to the project maintainer rather than publishing exploit details in a public issue.

The Control Center privileged helper is security-sensitive. It must validate arguments, load only packaged TOML profiles, use argument arrays, and accept only predefined services, sysctl keys, and settings. Do not weaken PolicyKit authorization or add privileged operations without review.
