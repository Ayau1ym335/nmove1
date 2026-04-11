"""0006_add_profiles_table

Create patient profiles table and enum types used by registration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE profile_gender AS ENUM ('male', 'female'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE profile_side AS ENUM ('left', 'right'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "age",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "gender",
            sa.Enum("male", "female", name="profile_gender", create_type=False),
            nullable=False,
        ),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("nationality", sa.String(length=100), nullable=False),
        sa.Column("have_injury", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("have_banomaly", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("banomaly", sa.String(length=255), nullable=True),
        sa.Column("shoe_size", sa.Float(), nullable=False),
        sa.Column("leg_length", sa.Float(), nullable=False),
        sa.Column(
            "dominant_leg",
            sa.Enum("left", "right", name="profile_side", create_type=False),
            nullable=False,
            server_default=sa.text("'right'"),
        ),
        sa.Column("lifestyle", sa.String(length=100), nullable=False),
        sa.Column("smoke", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("alcohol", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("age >= 1 AND age <= 120", name="ck_profiles_age_range"),
        sa.CheckConstraint("height > 80 AND height < 240", name="ck_profiles_height_range"),
        sa.CheckConstraint("weight > 20 AND weight < 300", name="ck_profiles_weight_range"),
        sa.CheckConstraint("shoe_size > 10 AND shoe_size < 60", name="ck_profiles_shoe_size_range"),
        sa.CheckConstraint("leg_length > 20 AND leg_length < 160", name="ck_profiles_leg_length_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", name="pk_profiles"),
    )


def downgrade() -> None:
    op.drop_table("profiles")
    op.execute("DROP TYPE IF EXISTS profile_side")
    op.execute("DROP TYPE IF EXISTS profile_gender")
