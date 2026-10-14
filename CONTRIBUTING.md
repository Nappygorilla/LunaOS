# Contributing

- Keep package choices in config/packages and profile behavior in config/profiles.
- Never commit secrets, tokens, ISO outputs, or private machine configuration.
- Keep privileged operations in the allowlisted profile helper.
- Do not use shell=True, shell snippets, arbitrary services, or arbitrary sysctl names.
- Add schema tests and documentation for every new module or profile.
- Run scripts/check-project.sh and both Python test scripts before opening a PR.
- Build and test the ISO in a disposable VM; clearly label untested behavior.
