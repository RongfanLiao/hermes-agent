#!/usr/bin/env python3
"""Change the dashboard's basic-auth password.

Prompts without echo and writes only the scrypt hash, so the plaintext never
lands in shell history, a config file, or a terminal transcript.

    python scripts/set-dashboard-password.py
    python scripts/set-dashboard-password.py --generate   # random 24-char
    python scripts/set-dashboard-password.py --username me

Restart the dashboard afterwards for it to take effect. Existing sessions
survive: they are signed with ``secret``, which this script never touches.
"""
from __future__ import annotations

import argparse
import getpass
import secrets
import string
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

MIN_LEN = 12
ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*-_=+"


def _read_password() -> str:
    for _ in range(3):
        pw = getpass.getpass("新密码（输入时不显示）: ")
        if len(pw) < MIN_LEN:
            print(f"  太短，至少 {MIN_LEN} 位\n", file=sys.stderr)
            continue
        if pw != getpass.getpass("再输一次确认: "):
            print("  两次不一致\n", file=sys.stderr)
            continue
        return pw
    raise SystemExit("重试次数用尽，未做任何修改")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--generate", action="store_true",
                    help="生成随机密码并打印一次（会进入终端回滚区，注意环境）")
    ap.add_argument("--username", help="同时修改用户名")
    args = ap.parse_args()

    from hermes_cli.config import load_config
    from plugins.dashboard_auth.basic import hash_password

    ba = ((load_config().get("dashboard") or {}).get("basic_auth")) or {}
    if not ba.get("username") and not args.username:
        raise SystemExit("config 里没有 dashboard.basic_auth.username，先配好再改密码")

    if args.generate:
        pw = "".join(secrets.choice(ALPHABET) for _ in range(24))
        print(f"\n  生成的密码: {pw}\n  ↑ 现在就存进密码管理器，之后无法找回\n")
    else:
        pw = _read_password()

    # Rewrite the two keys in place rather than round-tripping through
    # save_config(): that strips keys matching defaults, which would rewrite
    # most of a 600-line config as a side effect of changing a password.
    cfg_path = Path.home() / ".hermes" / "config.yaml"
    lines = cfg_path.read_text(encoding="utf-8").split("\n")

    start = next((i for i, l in enumerate(lines) if l.strip() == "basic_auth:"), None)
    if start is None:
        raise SystemExit("config.yaml 里找不到 basic_auth 块")
    indent = len(lines[start]) - len(lines[start].lstrip())

    edits = {"password_hash": hash_password(pw)}
    if args.username:
        edits["username"] = args.username

    seen = set()
    for i in range(start + 1, len(lines)):
        cur = lines[i]
        if cur.strip() and (len(cur) - len(cur.lstrip())) <= indent:
            break                       # left the basic_auth block
        key = cur.strip().split(":", 1)[0]
        if key in edits:
            pad = " " * (len(cur) - len(cur.lstrip()))
            lines[i] = f"{pad}{key}: '{edits[key]}'"
            seen.add(key)
        elif key == "password" and cur.split(":", 1)[1].strip() not in ("''", '""', ""):
            # A leftover plaintext password outranks the hash in the provider.
            pad = " " * (len(cur) - len(cur.lstrip()))
            lines[i] = f"{pad}password: ''"

    missing = set(edits) - seen
    if missing:
        raise SystemExit(f"basic_auth 块里没有这些键，未做修改: {sorted(missing)}")

    backup = cfg_path.with_suffix(f".yaml.bak-pw-{secrets.token_hex(3)}")
    backup.write_text(cfg_path.read_text(encoding="utf-8"), encoding="utf-8")
    cfg_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"✓ 已更新 dashboard.basic_auth（备份: {backup.name}）")
    print("  重启后生效：kill <pid> 然后重新启动 hermes dashboard")


if __name__ == "__main__":
    main()
