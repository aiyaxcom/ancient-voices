"""
时区工具函数
"""
from datetime import datetime, timezone, timedelta


# 东八区（北京时间）
CST = timezone(timedelta(hours=8))


def get_cst_now() -> datetime:
    """获取当前北京时间（CST）"""
    return datetime.now(CST)


def get_cst_now_no_tz() -> datetime:
    """获取当前北京时间（不带时区信息，用于数据库存储）"""
    return datetime.now(CST).replace(tzinfo=None)


def to_cst(dt: datetime) -> datetime:
    """将 datetime 转换为北京时间（CST）"""
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return dt.astimezone(CST)

    return dt.replace(tzinfo=timezone.utc).astimezone(CST)