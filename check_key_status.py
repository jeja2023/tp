#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JWT密钥状态检查工具

此脚本用于管理员检查JWT密钥的状态，包括：
- 上次轮换时间
- 下次轮换时间
- 距离下次轮换的天数
- 轮换间隔配置
- 验证密钥文件权限

使用方法：
    python check_key_status.py
"""

import os
import sys
import datetime
import logging
from backend.utils.key_manager import KeyManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("key_checker")

def check_file_permissions(filepath):
    """检查文件权限"""
    if not os.path.exists(filepath):
        return f"文件不存在: {filepath}"
    
    try:
        stats = os.stat(filepath)
        permissions = oct(stats.st_mode)[-3:]  # 获取权限的最后三位
        
        if os.name != 'nt':  # 非Windows系统
            # 检查文件是否只有所有者有读写权限
            if permissions not in ['600', '400']:
                return f"文件权限可能不安全 ({permissions}): {filepath}"
        
        return f"文件权限正常: {filepath} ({permissions})"
    except Exception as e:
        return f"检查文件权限时出错: {str(e)}"

def main():
    """主函数"""
    print("\n===== JWT 密钥状态检查 =====\n")
    
    try:
        # 初始化KeyManager
        key_manager = KeyManager()
        
        # 获取密钥信息
        key_info = key_manager.get_key_info()
        
        # 显示信息
        print(f"上次密钥轮换: {key_info['last_rotation'] or '从未'}")
        print(f"下次密钥轮换: {key_info['next_rotation'] or '未知'}")
        print(f"距离下次轮换: {key_info['days_until_rotation']} 天")
        print(f"轮换间隔设置: {key_info['rotation_interval_days']} 天")
        
        # 检查文件权限
        print("\n文件权限检查:")
        print(f"- {check_file_permissions('.env')}")
        print(f"- {check_file_permissions('last_key_rotation.txt')}")
        
        # 检查备份目录
        backup_dir = 'keybackups'
        if os.path.exists(backup_dir):
            backups = [f for f in os.listdir(backup_dir) if f.startswith('.env')]
            print(f"\n密钥备份文件数量: {len(backups)}")
            if backups:
                latest = max(backups, key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(backup_dir, latest)))
                print(f"最新备份文件: {latest} ({mtime})")
        else:
            print(f"\n备份目录不存在: {backup_dir}")
        
        print("\n===== 检查完成 =====")
        
    except Exception as e:
        logger.error(f"检查密钥状态时出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 