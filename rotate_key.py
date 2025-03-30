#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JWT密钥手动轮换工具

此脚本用于管理员手动轮换JWT密钥，无需等待自动轮换周期。
轮换会自动备份当前.env文件，并生成新的密钥。

使用方法：
    python rotate_key.py [--force]

参数：
    --force: 强制轮换密钥，即使当前密钥未过期
"""

import os
import sys
import logging
import argparse
from backend.utils.key_manager import KeyManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("key_rotator")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='JWT密钥手动轮换工具')
    parser.add_argument('--force', action='store_true', help='强制轮换密钥，即使当前密钥未过期')
    args = parser.parse_args()
    
    print("\n===== JWT 密钥手动轮换 =====\n")
    
    try:
        # 初始化KeyManager
        key_manager = KeyManager()
        
        # 获取当前密钥信息
        key_info = key_manager.get_key_info()
        print(f"当前密钥状态:")
        print(f"- 上次轮换: {key_info['last_rotation'] or '从未'}")
        print(f"- 下次轮换: {key_info['next_rotation'] or '未知'}")
        print(f"- 距离下次轮换: {key_info['days_until_rotation']} 天")
        
        if not args.force and not key_manager.should_rotate_key():
            print("\n当前密钥未过期，不需要轮换。")
            print("如果您确实需要立即轮换密钥，请使用 --force 参数。")
            return 0
        
        # 备份环境文件
        backup_result = key_manager.backup_env_file()
        if backup_result:
            print("\n已成功备份当前环境文件。")
        else:
            print("\n警告: 备份环境文件失败，但将继续轮换密钥。")
        
        # 轮换密钥
        print("\n正在轮换密钥...")
        new_key = key_manager.generate_secret_key()
        
        # 读取当前.env文件内容
        try:
            if os.path.exists(key_manager.key_file):
                with open(key_manager.key_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                print(f"警告: 找不到环境文件，将创建新文件。")
                lines = []
        except Exception as e:
            logger.error(f"读取环境文件失败: {str(e)}")
            print(f"错误: 无法读取环境文件: {str(e)}")
            return 1
        
        # 更新或添加SECRET_KEY
        key_updated = False
        for i, line in enumerate(lines):
            if line.startswith('SECRET_KEY='):
                old_key = line.strip().split('=')[1]
                lines[i] = f'SECRET_KEY={new_key}\n'
                key_updated = True
                break
        
        if not key_updated:
            lines.append(f'\nSECRET_KEY={new_key}\n')
        
        # 写入更新后的内容
        try:
            with open(key_manager.key_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 设置文件权限（仅适用于Unix/Linux系统）
            if os.name != 'nt':  # 非Windows系统
                try:
                    os.chmod(key_manager.key_file, 0o600)  # 仅所有者可读写
                except Exception as e:
                    print(f"警告: 设置环境文件权限失败: {str(e)}")
        except Exception as e:
            logger.error(f"写入环境文件失败: {str(e)}")
            print(f"错误: 无法更新环境文件: {str(e)}")
            return 1
        
        # 更新最后更换时间
        key_manager.update_last_rotation_time()
        
        print("\n密钥已成功轮换！")
        print("新密钥将在应用下次启动时生效。")
        print("建议立即重启应用以应用新密钥。")
        
        print("\n===== 操作完成 =====")
        
    except Exception as e:
        logger.error(f"轮换密钥时出错: {str(e)}")
        print(f"错误: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 