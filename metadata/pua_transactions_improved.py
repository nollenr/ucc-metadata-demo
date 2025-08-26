from __future__ import annotations
from datetime import datetime
from typing import Iterable, List, Optional, Tuple
from sqlalchemy.engine import Connection, Row
from sqlalchemy.sql import text

# --- Database Connection Info-------------------------------------------------

def get_node_info(conn) -> Tuple[int, str]:
    row = conn.execute(text("""
    SELECT
        coalesce(crdb_internal.locality_value('zone'), 'unknown') AS zone,
        crdb_internal.node_id() AS node_id
    """)).one()  # raises if 0 or >1 rows

    zone   = row.zone     # or: row[0] or row._mapping["zone"]
    nodeId = row.node_id  # or: row[1] or row._mapping["node_id"]
    return (nodeId, f"locality={zone}")

# --- Simple reads ------------------------------------------------------------

def read_bucket(conn: Connection, bucket_name: str) -> Optional[Row]:
    conn.execute(text("SET TRANSACTION AS OF SYSTEM TIME follower_read_timestamp()"))
    sql = text("""
        SELECT * FROM buckets WHERE bucket_name = :bucket_name
    """)
    return conn.execute(sql, {"bucket_name": bucket_name}).one_or_none()


def read_objects_in_bucket(conn: Connection, bucket_name: str) -> List[Row]:
    conn.execute(text("SET TRANSACTION AS OF SYSTEM TIME follower_read_timestamp()"))
    sql = text("""
        SELECT * FROM objects WHERE bucket_name = :bucket_name
    """)
    return list(conn.execute(sql, {"bucket_name": bucket_name}).fetchall())


def read_bucket_policy(conn: Connection, bucket_name: str, follower_read: bool = True) -> Optional[Row]:
    """Be permissive about schema shape: pull the whole row.

    We'll infer allow/deny in _is_allowed based on whichever columns exist.
    """
    if follower_read:
        conn.execute(text("SET TRANSACTION AS OF SYSTEM TIME follower_read_timestamp()"))
    sql = text("""
        SELECT * FROM bucket_policies WHERE bucket_name = :bucket_name
    """)
    return conn.execute(sql, {"bucket_name": bucket_name}).one_or_none()


# --- Auditing ---------------------------------------------------------------

def record_object_access(
    conn: Connection,
    bucket_name: str,
    object_key: str,
    version_id: str,
    success: bool,
    accessed_at: Optional[datetime] = None,
) -> None:
    sql = text("""
        INSERT INTO object_access_requests (
            bucket_name, object_key, version_id, accessed_at, success_fail
        )
        VALUES (:bucket_name, :object_key, :version_id, :accessed_at, :success)
    """)
    conn.execute(
        sql,
        {
            "bucket_name": bucket_name,
            "object_key": object_key,
            "version_id": version_id,
            "accessed_at": accessed_at or datetime.utcnow(),
            "success": success,
        },
    )


def record_object_access_bulk(
    conn: Connection,
    rows: Iterable[Tuple[str, str, str, bool, Optional[datetime]]],
) -> None:
    sql = text("""
        INSERT INTO object_access_requests (
            bucket_name, object_key, version_id, accessed_at, success_fail
        )
        VALUES (:bucket_name, :object_key, :version_id, :accessed_at, :success)
    """)
    payload = [
        {
            "bucket_name": b,
            "object_key": k,
            "version_id": v,
            "accessed_at": ts or datetime.utcnow(),
            "success": ok,
        }
        for (b, k, v, ok, ts) in rows
    ]
    conn.execute(sql, payload)


# --- Policy evaluation (schema-flexible) ------------------------------------

def _is_allowed(policy_row: Optional[Row]) -> bool:
    """Return True if policy allows public reads.

    Supports multiple schema shapes:
      1) A boolean column like allow_public_reads / is_public / public
      2) A JSON/JSONB column like policy/config/rules with keys such as
         allow_public_reads or nested access.read.public
    Defaults to False when unknown or not present.
    """
    if policy_row is None:
        return False

    m = policy_row._mapping

    # Case 1: direct boolean-ish columns
    for key in ("allow_public_reads", "is_public", "public", "public_read", "allow_read_public"):
        if key in m and m[key] is not None:
            try:
                return bool(m[key])
            except Exception:
                pass

    # Case 2: JSON column with nested structure
    for jkey in ("policy", "config", "rules"):
        val = m.get(jkey)
        if isinstance(val, dict):
            if "allow_public_reads" in val:
                return bool(val["allow_public_reads"])

            # Try some common nested paths
            def deep_get(d, path):
                cur = d
                for p in path:
                    if isinstance(cur, dict) and p in cur:
                        cur = cur[p]
                    else:
                        return None
                return cur

            for path in (("access", "read", "public"), ("public", "read"), ("read", "public")):
                got = deep_get(val, path)
                if got is not None:
                    try:
                        return bool(got)
                    except Exception:
                        pass

    # Default deny if we can't determine
    return False


# --- Composite fetch-and-audit ----------------------------------------------

def fetch_object_and_audit(
    conn: Connection,
    bucket_name: str,
    object_key: str,
    version_id: str,
) -> Optional[Row]:
    """Read policy + object, decide allow/deny, and record audit in one txn."""
    # 1) Read policy
    policy = read_bucket_policy(conn, bucket_name, False)

    # 2) Read object
    obj = conn.execute(
        text(
            """
            SELECT * FROM objects
            WHERE bucket_name = :bucket_name
              AND object_key  = :object_key
              AND version_id  = :version_id
            LIMIT 1
            """
        ),
        {"bucket_name": bucket_name, "object_key": object_key, "version_id": version_id},
    ).one_or_none()

    allowed = _is_allowed(policy) and obj is not None

    # 3) Audit inside the same txn
    record_object_access(conn, bucket_name, object_key, version_id, success=allowed)

    # 4) Return only if allowed
    return obj if allowed else None
