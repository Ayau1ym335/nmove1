"""0008_add_gait_sessions_leg_side

Align gait_sessions with ORM (leg_side for /sessions/start).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "gait_sessions",
        sa.Column("leg_side", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("gait_sessions", "leg_side")
