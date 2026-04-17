# backend/alembic/versions/0002_gait_readings.py
"""0002 — gait_readings: raw IMU data hypertable for ESP32 ingest.

Adds the gait_readings table, converts it to a TimescaleDB hypertable
partitioned on the ``time`` column with 1-hour chunks, and creates two
composite indexes for the primary query patterns:
    (gait_session_id, time DESC) — fetch all readings for a session
    (device_id,       time DESC) — fetch readings by device

Composite PK (time, id) is required by TimescaleDB: the partition key
must be the first column in any unique constraint, and id ensures
uniqueness within a time bucket.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # gait_readings table                                                  #
    # ------------------------------------------------------------------ #
    op.create_table(
        "gait_readings",
        # --- Time dimension column (TimescaleDB partition key) ---
        # Must be NOT NULL and listed FIRST in the composite PK so that
        # TimescaleDB can enforce uniqueness within each chunk.
        sa.Column(
            "time",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        # --- Row identity ---
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),

        # --- Foreign key to owning gait session ---
        sa.Column(
            "gait_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        # --- Device metadata ---
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("leg_side", sa.String(10),  nullable=False),

        # --- Accelerometer axes (m/s²) ---
        sa.Column("ax", sa.Float(), nullable=False),
        sa.Column("ay", sa.Float(), nullable=False),
        sa.Column("az", sa.Float(), nullable=False),

        # --- Gyroscope axes (deg/s) ---
        sa.Column("gx", sa.Float(), nullable=False),
        sa.Column("gy", sa.Float(), nullable=False),
        sa.Column("gz", sa.Float(), nullable=False),

        # --- Optional sensors ---
        sa.Column("temperature",     sa.Float(),   nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=True),

        # --- Row creation timestamp ---
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        # --- Constraints ---
        # Composite PK: time must be first for TimescaleDB partitioning.
        sa.PrimaryKeyConstraint("time", "id", name="pk_gait_readings"),

        # FK with cascade delete — removing a session removes its readings.
        sa.ForeignKeyConstraint(
            ["gait_session_id"],
            ["gait_sessions.id"],
            name="fk_gait_readings_gait_session_id_gait_sessions",
            ondelete="CASCADE",
        ),
    )

    # Standard B-tree index for the FK column (lookup by session).
    op.create_index(
        "ix_gait_readings_gait_session_id",
        "gait_readings",
        ["gait_session_id"],
    )

    # ------------------------------------------------------------------ #
    # TimescaleDB hypertable                                              #
    # chunk_time_interval=1 hour — sensible for 100 Hz ESP32 streams.    #
    # ------------------------------------------------------------------ #
    # Enable the extension first (idempotent).
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    op.execute(
        """
        SELECT create_hypertable(
            'gait_readings',
            'time',
            chunk_time_interval => INTERVAL '1 hour',
            if_not_exists => TRUE
        )
        """
    )

    # ------------------------------------------------------------------ #
    # Composite indexes for the two primary query patterns.               #
    # Time DESC gives the most-recent-first ordering for free.            #
    # These are created AFTER create_hypertable so TimescaleDB can        #
    # replicate the index definition across all chunks automatically.     #
    # ------------------------------------------------------------------ #
    op.execute(
        "CREATE INDEX ON gait_readings (gait_session_id, time DESC)"
    )
    op.execute(
        "CREATE INDEX ON gait_readings (device_id, time DESC)"
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # The composite indexes created with raw SQL do not have explicit names,
    # so we drop them via PostgreSQL's meta-tables before dropping the table.
    # Dropping the table also automatically removes the hypertable and all
    # its chunks — no separate TimescaleDB cleanup required.

    op.drop_index("ix_gait_readings_gait_session_id", table_name="gait_readings")

    # Drop the unnamed composite indexes by querying pg_indexes.
    op.execute(
        """
        DO $$
        DECLARE
            idx TEXT;
        BEGIN
            FOR idx IN
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'gait_readings'
                  AND indexname != 'pk_gait_readings'
                  AND indexname != 'ix_gait_readings_gait_session_id'
            LOOP
                EXECUTE 'DROP INDEX IF EXISTS ' || idx;
            END LOOP;
        END;
        $$
        """
    )

    op.drop_table("gait_readings")
