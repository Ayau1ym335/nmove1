"""0001 — Initial schema: users, auth_sessions, gait_sessions, metrics_snapshots, exercises."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enums
    # ------------------------------------------------------------------
    user_role_enum = postgresql.ENUM("patient", "doctor", name="user_role_enum")
    user_role_enum.create(op.get_bind(), checkfirst=True)

    interpretation_status_enum = postgresql.ENUM(
        "normal", "needs_attention", "improving",
        name="interpretation_status_enum"
    )
    interpretation_status_enum.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # users
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
            sa.Enum("patient", "doctor", name="user_role_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # auth_sessions
    # ------------------------------------------------------------------
    op.create_table(
        "auth_sessions",
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)

    # ------------------------------------------------------------------
    # gait_sessions
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
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_id", sa.String(64), nullable=True),
        sa.Column("raw_data_path", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gait_sessions_user_id", "gait_sessions", ["user_id"])

    # ------------------------------------------------------------------
    # metrics_snapshots
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
        sa.Column(
            "interpretation_status",
            sa.Enum(
                "normal", "needs_attention", "improving",
                name="interpretation_status_enum",
                create_type=False,
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
            ["gait_session_id"], ["gait_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_metrics_snapshots_gait_session_id",
        "metrics_snapshots",
        ["gait_session_id"],
    )

    # ------------------------------------------------------------------
    # exercises
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
        sa.Column("video_url", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["metrics_snapshot_id"], ["metrics_snapshots.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_exercises_metrics_snapshot_id",
        "exercises",
        ["metrics_snapshot_id"],
    )


def downgrade() -> None:
    op.drop_table("exercises")
    op.drop_table("metrics_snapshots")
    op.drop_table("gait_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS interpretation_status_enum")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
