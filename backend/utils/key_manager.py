import os
import time
import secrets
import logging
import shutil
from datetime import datetime, timedelta
from typing import Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

class KeyManager:
    def __init__(self, key_file: str = ".env", rotation_interval_days: int = 30, backup_dir: str = "keybackups"):
        self.key_file = key_file
        self.rotation_interval_days = rotation_interval_days
        self.last_rotation_file = "last_key_rotation.txt"
        self.backup_dir = backup_dir
        
        # 确保备份目录存在
        if not os.path.exists(self.backup_dir):
            try:
                os.makedirs(self.backup_dir, exist_ok=True)
                logger.info(f"创建密钥备份目录: {self.backup_dir}")
            except Exception as e:
                logger.warning(f"无法创建密钥备份目录: {e}")
        
    def generate_secret_key(self) -> str:
        """生成新的安全密钥"""
        try:
            key = secrets.token_urlsafe(32)
            logger.info("已生成新的密钥")
            return key
        except Exception as e:
            logger.error(f"生成密钥时出错: {e}")
            # 返回一个备用随机密钥，但记录错误
            return secrets.token_hex(32)
    
    def get_last_rotation_time(self) -> Optional[datetime]:
        """获取上次密钥更换时间"""
        try:
            if not os.path.exists(self.last_rotation_file):
                logger.warning(f"密钥轮换记录文件不存在: {self.last_rotation_file}")
                return None
                
            with open(self.last_rotation_file, 'r', encoding='utf-8') as f:
                timestamp = float(f.read().strip())
                return datetime.fromtimestamp(timestamp)
        except (FileNotFoundError, ValueError, PermissionError) as e:
            logger.error(f"读取密钥轮换记录失败: {e}")
            return None
    
    def update_last_rotation_time(self):
        """更新最后更换时间"""
        try:
            with open(self.last_rotation_file, 'w', encoding='utf-8') as f:
                f.write(str(time.time()))
            
            # 设置文件权限（仅适用于Unix/Linux系统）
            try:
                if os.name != 'nt':  # 非Windows系统
                    os.chmod(self.last_rotation_file, 0o600)  # 仅所有者可读写
            except Exception as e:
                logger.warning(f"设置密钥轮换记录文件权限失败: {e}")
                
            logger.info("已更新密钥轮换时间记录")
        except Exception as e:
            logger.error(f"更新密钥轮换时间失败: {e}")
    
    def should_rotate_key(self) -> bool:
        """检查是否需要更换密钥"""
        last_rotation = self.get_last_rotation_time()
        if not last_rotation:
            logger.info("首次运行或找不到轮换记录，将生成新密钥")
            return True
        
        next_rotation = last_rotation + timedelta(days=self.rotation_interval_days)
        is_rotation_needed = datetime.now() >= next_rotation
        
        if is_rotation_needed:
            logger.info("密钥已过期，将进行轮换")
        
        return is_rotation_needed
    
    def backup_env_file(self) -> bool:
        """备份.env文件"""
        if not os.path.exists(self.key_file):
            logger.warning(f"找不到要备份的文件: {self.key_file}")
            return False
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"{os.path.basename(self.key_file)}.{timestamp}")
            shutil.copy2(self.key_file, backup_file)
            
            # 设置备份文件权限
            if os.name != 'nt':  # 非Windows系统
                try:
                    os.chmod(backup_file, 0o600)  # 仅所有者可读写
                except Exception as e:
                    logger.warning(f"设置备份文件权限失败: {e}")
            
            logger.info(f"已创建环境文件备份: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"备份环境文件失败: {e}")
            return False
    
    def rotate_key(self) -> Optional[str]:
        """更换密钥"""
        if not self.should_rotate_key():
            return None
        
        # 备份当前环境文件
        self.backup_env_file()
        
        new_key = self.generate_secret_key()
        
        # 读取当前.env文件内容
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                logger.warning(f"环境文件不存在，将创建新文件: {self.key_file}")
                lines = []
        except Exception as e:
            logger.error(f"读取环境文件失败: {e}")
            lines = []
        
        # 更新或添加SECRET_KEY
        key_updated = False
        for i, line in enumerate(lines):
            if line.startswith('SECRET_KEY='):
                lines[i] = f'SECRET_KEY={new_key}\n'
                key_updated = True
                break
        
        if not key_updated:
            lines.append(f'\nSECRET_KEY={new_key}\n')
        
        # 写入更新后的内容
        try:
            with open(self.key_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # 设置文件权限（仅适用于Unix/Linux系统）
            if os.name != 'nt':  # 非Windows系统
                try:
                    os.chmod(self.key_file, 0o600)  # 仅所有者可读写
                except Exception as e:
                    logger.warning(f"设置环境文件权限失败: {e}")
            
            logger.info("已更新密钥到环境文件")
        except Exception as e:
            logger.error(f"写入环境文件失败: {e}")
            return None
        
        # 更新最后更换时间
        self.update_last_rotation_time()
        
        logger.info("密钥轮换完成")
        return new_key
    
    def get_current_key(self) -> str:
        """获取当前密钥"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('SECRET_KEY='):
                            key = line.strip().split('=')[1]
                            logger.info("已从环境文件获取密钥")
                            return key
            else:
                logger.warning(f"环境文件不存在: {self.key_file}")
        except Exception as e:
            logger.error(f"读取密钥失败: {e}")
        
        # 如果找不到密钥，生成一个新的
        logger.warning("未找到现有密钥，将生成新密钥")
        new_key = self.generate_secret_key()
        self.rotate_key()  # 确保写入到文件
        return new_key
    
    def get_key_info(self) -> dict:
        """获取密钥信息（不包含密钥本身）"""
        last_rotation = self.get_last_rotation_time()
        if last_rotation:
            next_rotation = last_rotation + timedelta(days=self.rotation_interval_days)
            days_until_rotation = (next_rotation - datetime.now()).days
        else:
            next_rotation = None
            days_until_rotation = 0
            
        return {
            "last_rotation": last_rotation.isoformat() if last_rotation else None,
            "next_rotation": next_rotation.isoformat() if next_rotation else None,
            "days_until_rotation": days_until_rotation,
            "rotation_interval_days": self.rotation_interval_days
        } 