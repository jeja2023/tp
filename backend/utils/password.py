from passlib.context import CryptContext
import logging

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别

# 使用固定的配置创建CryptContext
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__ident="2b"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    try:
        # 确保输入是字符串类型
        plain_password = str(plain_password).strip()
        hashed_password = str(hashed_password).strip()
        
        # 记录密码验证过程
        logger.debug(f"验证密码: 明文={plain_password}, 明文长度={len(plain_password)}")
        logger.debug(f"验证密码: 哈希={hashed_password}, 哈希长度={len(hashed_password)}")
        
        # 验证密码
        result = pwd_context.verify(plain_password, hashed_password)
        logger.debug(f"密码验证结果: {result}")
        
        # 如果验证失败，生成一个新的哈希值进行比较
        if not result:
            new_hash = pwd_context.hash(plain_password)
            logger.debug(f"生成新哈希: {new_hash}")
            logger.debug(f"新旧哈希比较: 新={new_hash}, 旧={hashed_password}")
        
        return result
    except Exception as e:
        # 记录错误并返回False
        logger.error(f"密码验证失败: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """获取密码的哈希值"""
    try:
        # 确保输入是字符串类型
        password = str(password).strip()
        
        # 记录密码哈希过程
        logger.debug(f"生成密码哈希: 明文={password}, 明文长度={len(password)}")
        
        # 生成哈希
        hashed = pwd_context.hash(password)
        logger.debug(f"生成的哈希: {hashed}, 长度={len(hashed)}")
        return hashed
    except Exception as e:
        # 记录错误并重新抛出
        logger.error(f"生成密码哈希失败: {str(e)}")
        raise e 