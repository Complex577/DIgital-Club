#!/usr/bin/env python3
"""Bootstrap a fresh local database for Digital Club.

Why this exists
---------------
The Alembic revisions in ``migrations/versions/`` are incremental. The oldest
revision alters an existing ``user`` table; it does not create the base schema.
A brand-new empty SQLite/Postgres database therefore cannot run
``flask db upgrade`` successfully.

This script is the disciplined first-time setup for clones / new environments:

1. Create missing tables from the current SQLAlchemy models (``db.create_all``)
2. Mark Alembic as fully applied (``flask db stamp head``) without replaying
   historical alters that assume old tables already exist
3. Seed the development super-admin if missing

After this, use normal Flask-Migrate commands when *you* change models:

    flask db migrate -m "describe your change"
    flask db upgrade

Usage (from project root, venv active)::

    python scripts/bootstrap_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _table_names(db) -> set[str]:
    from sqlalchemy import inspect

    return set(inspect(db.engine).get_table_names())


def main() -> int:
    from flask_migrate import stamp

    from app import create_app, db
    from app.models import User

    app = create_app()
    with app.app_context():
        before = _table_names(db)
        has_user = "user" in before
        has_version = "alembic_version" in before

        if has_user and has_version:
            print("Database already looks bootstrapped (user + alembic_version present).")
            print("Nothing to do. If login still fails, check admin seed / Turnstile keys.")
            return 0

        print("Creating missing tables from current models…")
        db.create_all()
        after = _table_names(db)
        created = sorted(after - before)
        if created:
            print(f"  created/ensured {len(created)} table(s), including: {', '.join(created[:8])}"
                  + ("…" if len(created) > 8 else ""))
        else:
            print("  no new tables needed (models already present).")

        print("Stamping Alembic head (mark migrations applied without replaying)…")
        stamp(revision="head")
        print("  stamped to head.")

        admin_email = "admin@digitalclub.kiut.ac.tz"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                role="admin",
                is_approved=True,
                is_super_admin=True,
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Seeded development super-admin:")
            print(f"  email:    {admin_email}")
            print("  password: admin123")
            print("  WARNING: change this password before any real deployment.")
        else:
            print(f"Admin already exists: {admin_email}")

        print()
        print("Bootstrap complete. Next:")
        print("  python main.py")
        print("  then open http://localhost:5051/auth/login")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
