#!/usr/bin/env python3
"""Sync the repo's Hermes config into a local Hermes install (Conde's PC).

hermes/config/ is the single source of truth. Railway copies it into the
container on every boot (start.sh). This script does the local equivalent:

  config.yaml  local file + repo config + hermes/local/overrides.yaml
               (repo wins over local; overrides win over both). Keys the repo
               does not set keep their local values.
  SOUL.md      repo SOUL.md with the ENVIRONMENT block replaced by
               hermes/local/SOUL.env.md
  prompts      the "REMOTE MACHINE (mypc)" tail of agent prompts is replaced
               by hermes/local/prompt.env.txt
  skins/       copied from the repo

Never touched: memories/, cron/, auth.json, .env, sessions.
A backup of every file it changes goes to $HERMES_HOME/backups/repo-sync-<time>/.

Usage:
  python hermes/sync-local.py --dry-run     # show what would change
  python hermes/sync-local.py               # apply, then restart the gateway
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required: python -m pip install pyyaml")

HERE = Path(__file__).resolve().parent
REPO_CONFIG = HERE / "config"
LOCAL_LAYER = HERE / "local"

PROMPT_MARKER = "\n\nREMOTE MACHINE (mypc)"
ENV_BLOCK = re.compile(r"<!-- ENVIRONMENT:BEGIN.*?-->.*?<!-- ENVIRONMENT:END -->", re.S)
SENSITIVE = re.compile(r"key|token|secret|password|auth|cookie|bearer", re.I)


def deep_merge(base, over):
    if not isinstance(base, dict) or not isinstance(over, dict):
        return over
    out = dict(base)
    for k, v in over.items():
        out[k] = deep_merge(base.get(k), v) if k in base else v
    return out


def localize_prompt(text, prompt_env):
    if not isinstance(text, str) or PROMPT_MARKER not in text:
        return text
    return text.split(PROMPT_MARKER, 1)[0] + "\n\n" + prompt_env.strip()


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    else:
        out[prefix] = d
    return out


def shown(key, value):
    if SENSITIVE.search(key) and value not in ("", None, True, False):
        return "<set>"
    s = repr(value)
    return s if len(s) <= 60 else s[:57] + "..."


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_config(local_cfg):
    repo_cfg = load_yaml(REPO_CONFIG / "config.yaml")
    overrides = load_yaml(LOCAL_LAYER / "overrides.yaml")
    prompt_env = (LOCAL_LAYER / "prompt.env.txt").read_text(encoding="utf-8")

    merged = deep_merge(deep_merge(local_cfg, repo_cfg), overrides)
    agent = merged.get("agent") or {}
    if "system_prompt" in agent:
        agent["system_prompt"] = localize_prompt(agent["system_prompt"], prompt_env)
    for name, text in (agent.get("personalities") or {}).items():
        agent["personalities"][name] = localize_prompt(text, prompt_env)
    return merged


def build_soul():
    soul = (REPO_CONFIG / "SOUL.md").read_text(encoding="utf-8")
    env = (LOCAL_LAYER / "SOUL.env.md").read_text(encoding="utf-8").strip()
    if len(ENV_BLOCK.findall(soul)) != 1:
        sys.exit("hermes/config/SOUL.md must contain exactly one ENVIRONMENT:BEGIN/END block")
    return ENV_BLOCK.sub(lambda _: env, soul)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hermes-home", default=os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes"))
    ap.add_argument("--dry-run", action="store_true", help="show changes without writing")
    args = ap.parse_args()

    home = Path(args.hermes_home).expanduser().resolve()
    if home.as_posix().startswith("/data/"):
        sys.exit(f"{home} looks like the Railway volume; start.sh manages that one")
    config_path = home / "config.yaml"
    if not config_path.exists():
        sys.exit(f"No Hermes config at {config_path} (set HERMES_HOME or pass --hermes-home)")

    old_cfg = load_yaml(config_path)
    new_cfg = build_config(old_cfg)
    new_soul = build_soul()
    old_soul = (home / "SOUL.md").read_text(encoding="utf-8") if (home / "SOUL.md").exists() else ""

    old_flat, new_flat = flatten(old_cfg), flatten(new_cfg)
    changed = sorted(k for k in set(old_flat) | set(new_flat) if old_flat.get(k, "<unset>") != new_flat.get(k, "<unset>"))
    print(f"Hermes home: {home}")
    print(f"config.yaml: {len(changed)} key(s) change")
    for k in changed:
        print(f"  {k}: {shown(k, old_flat.get(k, '<unset>'))} -> {shown(k, new_flat.get(k, '<unset>'))}")
    print(f"SOUL.md: {'changes' if new_soul != old_soul else 'unchanged'}")

    skins = sorted((REPO_CONFIG / "skins").glob("*.yaml"))
    skin_changes = [s for s in skins if not (home / "skins" / s.name).exists()
                    or (home / "skins" / s.name).read_bytes() != s.read_bytes()]
    print(f"skins: {', '.join(s.name for s in skin_changes) or 'unchanged'}")

    if args.dry_run:
        print("Dry run: nothing written.")
        return
    if not changed and new_soul == old_soul and not skin_changes:
        print("Already in sync.")
        return

    backup = home / "backups" / f"repo-sync-{datetime.now():%Y%m%d-%H%M%S}"
    (backup / "skins").mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, backup / "config.yaml")
    if old_soul:
        shutil.copy2(home / "SOUL.md", backup / "SOUL.md")
    for s in skin_changes:
        if (home / "skins" / s.name).exists():
            shutil.copy2(home / "skins" / s.name, backup / "skins" / s.name)

    tmp = config_path.with_suffix(".yaml.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(new_cfg, f, allow_unicode=True, sort_keys=False, width=10**6)
    os.replace(tmp, config_path)
    (home / "SOUL.md").write_text(new_soul, encoding="utf-8", newline="\n")
    (home / "skins").mkdir(exist_ok=True)
    for s in skin_changes:
        shutil.copy2(s, home / "skins" / s.name)

    print(f"Written. Backup: {backup}")
    print("Restart the Hermes gateway so it picks up the new config.")


if __name__ == "__main__":
    main()
