"""0003_session_status — Add status, doctor_id, and metadata to gait_sessions.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create Enum Type
    session_status = postgresql.ENUM('ingested', 'processing', 'done', 'error', name='session_status')
    session_status.create(op.get_bind())

    # 2. Add columns with Enum
    op.add_column('gait_sessions',
        sa.Column('status', session_status, server_default='ingested', nullable=False)
    )

    op.add_column('gait_sessions', sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('gait_sessions', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('gait_sessions', sa.Column('task_id', sa.String(length=255), nullable=True))
    
    op.add_column('gait_sessions', sa.Column('doctor_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_gait_sessions_doctor_id_users',
        'gait_sessions', 'users',
        ['doctor_id'], ['id'],
        ondelete='SET NULL'
    )
    
    op.add_column('gait_sessions', sa.Column('reading_count', sa.Integer(), nullable=True))

    # 3. Add Indexes
    op.create_index('ix_gait_sessions_status', 'gait_sessions', ['status'], unique=False)
    op.create_index('ix_gait_sessions_doctor_id_status', 'gait_sessions', ['doctor_id', 'status'], unique=False)
    op.create_index('ix_gait_sessions_user_id_status', 'gait_sessions', ['user_id', 'status'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_gait_sessions_user_id_status', table_name='gait_sessions')
    op.drop_index('ix_gait_sessions_doctor_id_status', table_name='gait_sessions')
    op.drop_index('ix_gait_sessions_status', table_name='gait_sessions')
    
    op.drop_column('gait_sessions', 'reading_count')
    
    op.drop_constraint('fk_gait_sessions_doctor_id_users', 'gait_sessions', type_='foreignkey')
    op.drop_column('gait_sessions', 'doctor_id')
    
    op.drop_column('gait_sessions', 'task_id')
    op.drop_column('gait_sessions', 'error_message')
    op.drop_column('gait_sessions', 'status_updated_at')
    
    op.drop_column('gait_sessions', 'status')
    
    session_status = postgresql.ENUM('ingested', 'processing', 'done', 'error', name='session_status')
    session_status.drop(op.get_bind())
