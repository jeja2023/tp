"""remove sequence_number field

Revision ID: remove_sequence_number
Revises: aa7847809e16
Create Date: 2024-03-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_sequence_number'
down_revision = 'aa7847809e16'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 移除sequence_number字段
    op.drop_column('images', 'sequence_number')


def downgrade() -> None:
    # 添加sequence_number字段
    op.add_column('images', sa.Column('sequence_number', sa.Integer(), nullable=True)) 