import os
import logging
import sys
from backend.config import settings

def setup_logger(name, level=None, enable_file_logging=None):
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别，如果未指定则根据环境自动设置
        enable_file_logging: 是否启用文件日志记录，如果未指定则使用全局设置
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 设置默认值
    if level is None:
        level = settings.LOG_LEVEL
    if enable_file_logging is None:
        enable_file_logging = settings.ENABLE_FILE_LOGGING

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除现有的处理器
    logger.handlers.clear()

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 如果启用了文件日志
    if enable_file_logging:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(settings.LOG_FILE)
            os.makedirs(log_dir, exist_ok=True)

            # 创建文件处理器
            file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
            file_handler.setLevel(level)
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # 记录日志目录创建信息
            logger.debug(f"日志目录已创建/确认: {log_dir}")
        except Exception as e:
            # 如果创建文件处理器失败，记录错误但继续使用控制台处理器
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.error(f"无法创建日志文件处理器: {str(e)}")

    return logger 