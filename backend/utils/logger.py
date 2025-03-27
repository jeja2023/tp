import logging
import sys
from config import settings

def setup_logger(name, level=logging.INFO):
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别，默认为INFO
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 如果是生产环境，将日志写入文件
    if settings.IS_PRODUCTION:
        # 文件处理器
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    else:
        # 开发环境下，使用简化的控制台输出格式
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter('%(message)s')  # 简化的格式
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger 