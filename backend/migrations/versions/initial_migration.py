"""初始数据库迁移

Revision ID: 001
Revises: 
Create Date: 2023-03-22 12:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建用户表
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # 创建任务表
    op.create_table('tasks',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建图片表
    op.create_table('images',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('time', sa.DateTime(), nullable=True),
        sa.Column('transportation', sa.String(length=50), nullable=True),
        sa.Column('task_id', sa.String(length=36), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建涉事人员表
    op.create_table('persons_involved',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('id_number', sa.String(length=18), nullable=True),
        sa.Column('household_registration', sa.String(length=255), nullable=True),
        sa.Column('image_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['image_id'], ['images.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建权限表
    op.create_table('task_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # 删除表（按照依赖关系的反向顺序）
    op.drop_table('task_permissions')
    op.drop_table('persons_involved')
    op.drop_table('images')
    op.drop_table('tasks')
    op.drop_table('users') 