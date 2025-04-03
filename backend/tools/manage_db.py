import os
import sys
from pathlib import Path
import argparse
from alembic import command
from alembic.config import Config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.db.database import engine
from backend.models.models import Base
from backend.db.initialize_db import initialize_base_data

def get_alembic_config():
    """获取 Alembic 配置"""
    alembic_cfg = Config(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini"))
    return alembic_cfg

def init_alembic():
    """初始化 Alembic"""
    alembic_cfg = get_alembic_config()
    command.init(alembic_cfg, "migrations")

def create_migration(message):
    """创建新的迁移"""
    alembic_cfg = get_alembic_config()
    command.revision(alembic_cfg, autogenerate=True, message=message)

def upgrade_database():
    """升级数据库到最新版本"""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")

def downgrade_database(revision):
    """降级数据库到指定版本"""
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, revision)

def init_database():
    """初始化数据库"""
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    
    # 创建所有表
    upgrade_database()
    
    # 初始化基础数据
    initialize_base_data()

def main():
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument('action', choices=['init', 'migrate', 'upgrade', 'downgrade', 'init-alembic'],
                      help='要执行的操作: init=初始化数据库, migrate=创建迁移, upgrade=升级数据库, downgrade=降级数据库, init-alembic=初始化Alembic')
    parser.add_argument('--message', '-m', help='迁移说明信息')
    parser.add_argument('--revision', '-r', help='降级到指定版本')
    
    args = parser.parse_args()
    
    if args.action == 'init-alembic':
        print('初始化 Alembic...')
        init_alembic()
        print('Alembic 初始化完成！')
    
    elif args.action == 'init':
        print('初始化数据库...')
        init_database()
        print('数据库初始化完成！')
    
    elif args.action == 'migrate':
        if not args.message:
            print('错误：创建迁移时必须提供说明信息')
            sys.exit(1)
        print(f'创建迁移：{args.message}')
        create_migration(args.message)
        print('迁移创建完成！')
    
    elif args.action == 'upgrade':
        print('升级数据库...')
        upgrade_database()
        print('数据库升级完成！')
    
    elif args.action == 'downgrade':
        if not args.revision:
            print('错误：降级数据库时必须指定目标版本')
            sys.exit(1)
        print(f'降级数据库到版本：{args.revision}')
        downgrade_database(args.revision)
        print('数据库降级完成！')

if __name__ == '__main__':
    main() 