"""连接 MySQL，并统一管理提交、回滚和关闭连接。"""

from collections.abc import Iterator
from contextlib import contextmanager

import pymysql
from pymysql.constants import CLIENT
from pymysql.cursors import DictCursor

from config import load_settings


@contextmanager
def get_connection() -> Iterator[pymysql.Connection]:
    settings = load_settings()
    connection = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=5,
        # UPDATE 即使写入相同值，也按匹配行数返回，能正确判断商品是否存在。
        client_flag=CLIENT.FOUND_ROWS,
    )
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
