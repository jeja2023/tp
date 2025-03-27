"""更新用户表结构

Revision ID: 002
Revises: 001
Create Date: 2024-03-25 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # 删除email列和其唯一约束
    op.drop_constraint('email', 'users', type_='unique')
    op.drop_column('users', 'email')
    
    # 添加新的列
    op.add_column('users', sa.Column('company', sa.String(length=100), nullable=False))
    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=False))
    op.add_column('users', sa.Column('is_approved', sa.Boolean(), nullable=True, default=False))
    
    # 创建phone的唯一索引
    op.create_index('ix_users_phone', 'users', ['phone'], unique=True)
    
    # 修改hashed_password列的长度
    op.alter_column('users', 'hashed_password',
        existing_type=sa.String(length=100),
        type_=sa.String(length=255),
        existing_nullable=False)

def downgrade():
    # 删除新添加的列
    op.drop_index('ix_users_phone', table_name='users')
    op.drop_column('users', 'is_approved')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'company')
    
    # 恢复email列
    op.add_column('users', sa.Column('email', sa.String(length=100), nullable=True))
    op.create_unique_constraint('email', 'users', ['email'])
    
    # 恢复hashed_password列的长度
    op.alter_column('users', 'hashed_password',
        existing_type=sa.String(length=255),
        type_=sa.String(length=100),
        existing_nullable=False) 