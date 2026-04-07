"""0004_extend_metrics_and_user_models — Add biomechanical columns to metrics_snapshots
and create the user_models table for ML training metadata.

Revision ID: 0004
Revises: 0003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─────────────────────────────────────────────────────────────────────────
    # 1. Extend metrics_snapshots with richer biomechanical features
    #    (all nullable so existing rows are unaffected)
    # ─────────────────────────────────────────────────────────────────────────

    # Rhythm & Pace
    op.add_column("metrics_snapshots", sa.Column("stride_length", sa.Float(), nullable=True,
                  comment="Estimated stride length (m)"))
    op.add_column("metrics_snapshots", sa.Column("step_count", sa.Integer(), nullable=True,
                  comment="Total steps detected in the session"))
    op.add_column("metrics_snapshots", sa.Column("avg_speed", sa.Float(), nullable=True,
                  comment="Average walking speed (m/s)"))

    # Joint Mechanics
    op.add_column("metrics_snapshots", sa.Column("hip_rotation_rom", sa.Float(), nullable=True,
                  comment="Hip rotation ROM (deg) from gyroscope"))
    op.add_column("metrics_snapshots", sa.Column("ankle_pushoff_proxy", sa.Float(), nullable=True,
                  comment="Ankle push-off proxy (m/s²)"))
    op.add_column("metrics_snapshots", sa.Column("vertical_oscillation", sa.Float(), nullable=True,
                  comment="Vertical oscillation peak-to-peak (m/s²)"))

    # Variability
    op.add_column("metrics_snapshots", sa.Column("stride_time_cv", sa.Float(), nullable=True,
                  comment="Stride time coefficient of variation (%)"))
    op.add_column("metrics_snapshots", sa.Column("trunk_sway_rms", sa.Float(), nullable=True,
                  comment="Trunk sway RMS lateral accel (m/s²)"))

    # Symmetry & Phases
    op.add_column("metrics_snapshots", sa.Column("stance_phase_pct", sa.Float(), nullable=True,
                  comment="Stance phase percentage (%)"))
    op.add_column("metrics_snapshots", sa.Column("double_support_pct", sa.Float(), nullable=True,
                  comment="Double-support phase percentage (%)"))

    # Anomaly detection (ML scorer output)
    op.add_column("metrics_snapshots", sa.Column("anomaly_score", sa.Float(), nullable=True,
                  comment="Autoencoder reconstruction error, normalised 0–1 (1 = very abnormal)"))
    op.add_column("metrics_snapshots", sa.Column("is_anomaly", sa.Boolean(), nullable=True,
                  comment="True when anomaly_score > 0.65"))
    op.create_index("ix_metrics_snapshots_is_anomaly", "metrics_snapshots", ["is_anomaly"])

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Create user_models table — stores per-user ML model metadata
    # ─────────────────────────────────────────────────────────────────────────
    op.create_table(
        "user_models",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("model_type", sa.String(50), nullable=False, server_default="autoencoder"),
        sa.Column(
            "trained_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("n_sessions", sa.Integer(), nullable=False),
        sa.Column("minio_path", sa.String(500), nullable=True,
                  comment="MinIO object path for autoencoder .pkl"),
        sa.Column("scaler_path", sa.String(500), nullable=True,
                  comment="MinIO object path for scaler .pkl"),
    )


def downgrade() -> None:
    # Remove user_models table (index on user_id is auto-dropped with the table)
    op.drop_table("user_models")

    # Remove extended metrics columns
    for col in [
        "is_anomaly",
        "anomaly_score",
        "double_support_pct",
        "stance_phase_pct",
        "trunk_sway_rms",
        "stride_time_cv",
        "vertical_oscillation",
        "ankle_pushoff_proxy",
        "hip_rotation_rom",
        "avg_speed",
        "step_count",
        "stride_length",
    ]:
        op.drop_column("metrics_snapshots", col)
    op.drop_index("ix_metrics_snapshots_is_anomaly", table_name="metrics_snapshots")
