#!/usr/bin/env python3
"""Validate profile data without applying privileged settings."""
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_MODULES = {"security", "privacy", "performance", "gaming", "coding", "creator"}
SYSCTL = {"vm.swappiness": (0, 100), "kernel.kptr_restrict": (0, 2), "kernel.dmesg_restrict": (0, 1)}
POWER = {"power-saver", "balanced", "performance"}
paths = sorted((ROOT / "config/profiles").glob("*.toml"))
assert len(paths) >= 7
seen = set()
for path in paths:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    meta = data.get("profile", {})
    ident = meta.get("id")
    assert ident == path.stem and ident not in seen
    seen.add(ident)
    assert meta.get("name") and meta.get("description")
    modules = data.get("modules", {})
    assert modules and set(modules) <= ALLOWED_MODULES
    assert all(type(value) is bool for value in modules.values())
    settings = data.get("settings", {})
    assert settings.get("power_profile", "balanced") in POWER
    assert type(settings.get("swappiness", 60)) is int and 0 <= settings.get("swappiness", 60) <= 100
    for key, value in data.get("sysctl", {}).items():
        assert key in SYSCTL and type(value) is int and SYSCTL[key][0] <= value <= SYSCTL[key][1]
print(f"PASS: {len(paths)} profiles validated")
