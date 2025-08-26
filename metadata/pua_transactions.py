from datetime import datetime
from typing import List, Optional
from sqlalchemy.engine import Connection, Row
from sqlalchemy.sql import text


def read_bucket(conn: Connection, bucket_name: str) -> Optional[Row]:
    sql = text("""
        SELECT * FROM buckets WHERE bucket_name = :bucket_name
    """)
    return conn.execute(sql, {"bucket_name": bucket_name}).one_or_none()


def read_objects_in_bucket(conn: Connection, bucket_name: str) -> List[Row]:
    sql = text("""
        SELECT object_key, version_id FROM objects WHERE bucket_name = :bucket_name
    """)
    return conn.execute(sql, {"bucket_name": bucket_name}).fetchall()


def read_bucket_policy(conn: Connection, bucket_name: str) -> Optional[Row]:
    sql = text("""
        SELECT 1 FROM bucket_policies WHERE bucket_name = :bucket_name
    """)
    return conn.execute(sql, {"bucket_name": bucket_name}).one_or_none()


def record_object_access(
    conn: Connection,
    bucket_name: str,
    object_key: str,
    version_id: str,
    success: bool,
    accessed_at: Optional[datetime] = None
) -> None:
    sql = text("""
        INSERT INTO object_access_requests (
            bucket_name, object_key, version_id, accessed_at, success_fail
        )
        VALUES (:bucket_name, :object_key, :version_id, :accessed_at, :success)
    """)
    conn.execute(sql, {
        "bucket_name": bucket_name,
        "object_key": object_key,
        "version_id": version_id,
        "accessed_at": accessed_at or datetime.utcnow(),
        "success": success
    })
