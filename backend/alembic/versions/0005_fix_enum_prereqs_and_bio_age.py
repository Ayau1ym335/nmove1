"""0005_fix_enum_prereqs_and_bio_age

This migration fixes three issues found during the post-hackathon audit:

1.  Pre-creates the PostgreSQL ENUM types that migrations 0001–0003 assumed
    existed (via create_type=False) but never created.  Uses IF NOT EXISTS
    so re-running this on a clean DB is safe.

2.  Adds the ``bio_age`` column to ``users`` if it is missing
    (the SQLAlchemy model has it, the 0001 DDL did not).

3.  Fixes the ``interpretation_status`` ENUM so its values match what
    ``process_session.py`` and ``interpretation_service.py`` actually write
    (normal / attention / concern) rather than the original stale values
    (normal / needs_attention / improving).

    Strategy: change the column type to ``TEXT`` to avoid a hard PostgreSQL
    ENUM rename, drop the old ENUM type, then re-create with correct values
    AND switch back to an ENUM column.  All existing rows that had
    ``needs_attention`` → ``attention``; ``improving`` → ``concern``.

Revision ID: 0005
Revises: 0004
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Ensure ENUM types that 0001/0003 used with create_type=False
    #       actually exist.  Safe to call even if they were already created.
    # ──────────────────────────────────────────────────────────────────────────
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE user_role AS ENUM ('patient', 'doctor'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE exercise_difficulty AS ENUM ('easy', 'medium', 'hard'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE session_status AS ENUM "
        "    ('ingested', 'processing', 'done', 'error'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    # ── 2. Add bio_age to users if missing ────────────────────────────────────
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='users' AND column_name='bio_age'"
    ))
    if result.fetchone() is None:
        op.add_column("users", sa.Column("bio_age", sa.Integer(), nullable=True))

    # ── 3. Fix interpretation_status enum values ──────────────────────────────
    # Step 3a: Cast column to TEXT (drops implicit enum constraint)
    op.execute(
        "ALTER TABLE metrics_snapshots "
        "ALTER COLUMN interpretation_status TYPE TEXT "
        "USING interpretation_status::TEXT"
    )

    # Step 3b: Rename old stale values that might be present in the DB
    op.execute(
        "UPDATE metrics_snapshots "
        "SET interpretation_status = 'attention' "
        "WHERE interpretation_status = 'needs_attention'"
    )
    op.execute(
        "UPDATE metrics_snapshots "
        "SET interpretation_status = 'concern' "
        "WHERE interpretation_status = 'improving'"
    )

    # Step 3c: Drop the old ENUM type
    op.execute("DROP TYPE IF EXISTS interpretation_status")

    # Step 3d: Re-create ENUM with correct values
    op.execute(
        "CREATE TYPE interpretation_status AS ENUM ('normal', 'attention', 'concern')"
    )

    # Step 3e: Convert column back to the fixed ENUM type
    op.execute(
        "ALTER TABLE metrics_snapshots "
        "ALTER COLUMN interpretation_status TYPE interpretation_status "
        "USING interpretation_status::interpretation_status"
    )


def downgrade() -> None:
    # Revert interpretation_status to old values (best-effort)
    op.execute(
        "ALTER TABLE metrics_snapshots "
        "ALTER COLUMN interpretation_status TYPE TEXT "
        "USING interpretation_status::TEXT"
    )
    op.execute(
        "UPDATE metrics_snapshots "
        "SET interpretation_status = 'needs_attention' "
        "WHERE interpretation_status = 'attention'"
    )
    op.execute(
        "UPDATE metrics_snapshots "
        "SET interpretation_status = 'improving' "
        "WHERE interpretation_status = 'concern'"
    )
    op.execute("DROP TYPE IF EXISTS interpretation_status")
    op.execute(
        "CREATE TYPE interpretation_status AS ENUM "
        "('normal', 'needs_attention', 'improving')"
    )
    op.execute(
        "ALTER TABLE metrics_snapshots "
        "ALTER COLUMN interpretation_status TYPE interpretation_status "
        "USING interpretation_status::interpretation_status"
    )

    # Drop bio_age from users
    op.drop_column("users", "bio_age")
