"""Command line: `python -m portflow serve | init-db | set-partner-status`."""

from __future__ import annotations

import argparse
import logging
import sqlite3

from . import db
from .config import Settings
from .server import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="portflow")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("serve", help="start the API and operations page")
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8080)
    sub.add_parser("init-db", help="create tables and reference data")
    status = sub.add_parser("set-partner-status", help="activate or suspend a partner (go-live step)")
    status.add_argument("partner_id")
    status.add_argument("status", choices=["ONBOARDING", "ACTIVE", "SUSPENDED"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
    settings = Settings.from_env()

    if args.command == "serve":
        serve(settings, args.host, args.port)
    elif args.command == "init-db":
        db.init_schema(settings.db_path)
        print(f"schema ready in {settings.db_path}")
    else:
        db.init_schema(settings.db_path)
        with sqlite3.connect(settings.db_path) as conn:
            changed = conn.execute(
                "UPDATE partner SET status = ? WHERE partner_id = ?", (args.status, args.partner_id)
            ).rowcount
        if not changed:
            raise SystemExit(f"partner {args.partner_id} not found")
        logging.getLogger("portflow").info("PARTNER_STATUS partner=%s status=%s", args.partner_id, args.status)


if __name__ == "__main__":
    main()
