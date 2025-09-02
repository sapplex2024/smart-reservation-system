import logging
import sys
from typing import Optional

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 创建全局logger实例
logger = logging.getLogger('smart-reservation-system')

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取指定名称的logger实例"""
    if name:
        return logging.getLogger(f'smart-reservation-system.{name}')
    return logger