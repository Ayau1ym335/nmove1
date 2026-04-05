"""0001 — Initial schema: users, sessions, gait_sessions, metrics_snapshots, exercises.

Creates all tables in strict dependency order:
    users → sessions → gait_sessions → metrics_snapshots → exercises

Enums are created explicitly BEFORE any table that references them, and
dropped in reverse order in downgrade().

After creating gait_sessions, we call TimescaleDB's create_hypertable() to
partition the table on the ``started_at`` column (time-series optimisation).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_enum(name: str, *values: str) -> None:
    """Create a PostgreSQL ENUM type if it does not already exist."""
    enum_type = sa.Enum(*values, name=name)
    enum_type.create(op.get_bind(), checkfirst=True)


def _drop_enum(name: str) -> None:
    """Drop a PostgreSQL ENUM type if it exists."""
    op.execute(f"DROP TYPE IF EXISTS {name}")


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create ENUMs before the tables that use them.
    # ------------------------------------------------------------------
    _create_enum("user_role", "patient", "doctor")
    _create_enum("interpretation_status", "normal", "needs_attention", "improving")
    _create_enum("exercise_difficulty", "easy", "medium", "hard")

    # ------------------------------------------------------------------
    # 2. users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("patient", "doctor", name="user_role", create_type=False),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Trigger to auto-update updated_at on every row update
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    op.execute("""
        CREATE TRIGGER users_updated_at_trigger
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)

    # ------------------------------------------------------------------
    # 3. sessions (refresh token store)
    # ------------------------------------------------------------------
    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"], unique=True)

    # ------------------------------------------------------------------
    # 4. gait_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "gait_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("raw_data_path", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_gait_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_gait_sessions"),
    )
    op.create_index("ix_gait_sessions_user_id", "gait_sessions", ["user_id"])

    # Convert to TimescaleDB hypertable partitioned on started_at.
    # if_not_exists => TRUE prevents errors when running upgrade twice.
    op.execute(
        "SELECT create_hypertable('gait_sessions', 'started_at', if_not_exists => TRUE)"
    )

    # ------------------------------------------------------------------
    # 5. metrics_snapshots
    # ------------------------------------------------------------------
    op.create_table(
        "metrics_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("gait_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cadence", sa.Float(), nullable=False),
        sa.Column("symmetry_score", sa.Float(), nullable=False),
        sa.Column("stability_score", sa.Float(), nullable=False),
        sa.Column("movement_age", sa.Float(), nullable=True),
        sa.Column("bio_age", sa.Integer(), nullable=True),
        sa.Column("movement_age_delta", sa.Float(), nullable=True),
        sa.Column(
            "interpretation_status",
            sa.Enum(
                "normal",
                "needs_attention",
                "improving",
                name="interpretation_status",
                create_type=False,  # already created above
            ),
            nullable=False,
        ),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["gait_session_id"],
            ["gait_sessions.id"],
            name="fk_metrics_snapshots_gait_session_id_gait_sessions",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_metrics_snapshots"),
    )
    op.create_index(
        "ix_metrics_snapshots_gait_session_id",
        "metrics_snapshots",
        ["gait_session_id"],
    )

    # ------------------------------------------------------------------
    # 6. exercises
    # ------------------------------------------------------------------
    op.create_table(
        "exercises",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("metrics_snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum(
                "easy", "medium", "hard",
                name="exercise_difficulty",
                create_type=False,  # already created above
            ),
            nullable=True,
        ),
        sa.Column("video_url", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["metrics_snapshot_id"],
            ["metrics_snapshots.id"],
            name="fk_exercises_metrics_snapshot_id_metrics_snapshots",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_exercises"),
    )
    op.create_index(
        "ix_exercises_metrics_snapshot_id",
        "exercises",
        ["metrics_snapshot_id"],
    )


# ---------------------------------------------------------------------------
# downgrade — reverse order; drop tables first, then enums
# ---------------------------------------------------------------------------

def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index("ix_exercises_metrics_snapshot_id", table_name="exercises")
    op.drop_table("exercises")

    op.drop_index(
        "ix_metrics_snapshots_gait_session_id", table_name="metrics_snapshots"
    )
    op.drop_table("metrics_snapshots")

    op.drop_index("ix_gait_sessions_user_id", table_name="gait_sessions")
    op.drop_table("gait_sessions")

    op.drop_index("ix_sessions_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    # Drop trigger and function before users table
    op.execute("DROP TRIGGER IF EXISTS users_updated_at_trigger ON users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # Drop ENUMs after all tables referencing them are gone
    _drop_enum("exercise_difficulty")
    _drop_enum("interpretation_status")
    _drop_enum("user_role")
