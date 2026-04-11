"""0007_add_profile_baseline_snapshot

Add baseline snapshot link on profiles.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("baseline_snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_profiles_baseline_snapshot_id_metrics_snapshots",
        "profiles",
        "metrics_snapshots",
        ["baseline_snapshot_id"],
        ["id"],
        ondelete="SET NULL",
    )

def downgrade() -> None:
    op.drop_constraint("fk_profiles_baseline_snapshot_id_metrics_snapshots", "profiles", type_="foreignkey")
    op.drop_column("profiles", "baseline_snapshot_id")
