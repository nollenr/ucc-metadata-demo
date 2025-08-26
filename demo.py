#!/usr/bin/env python3
from datetime import datetime as dt
import os
import signal
import sys
from random import choice
from typing import List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine as SAEngine
from sqlalchemy.sql import text

from metadata.helpers import DemoStats, DemoTimer, run_transaction
from metadata.pua_transactions_improved import (
    read_bucket,
    read_bucket_policy,
    read_objects_in_bucket,
    record_object_access,
    # record_object_access_bulk,
    fetch_object_and_audit,
    get_node_info,
)

# ---- Tunables ---------------------------------------------------------------
STATS_INTERVAL_SECS = int(os.getenv("STATS_INTERVAL_SECS", "5"))
BULK_AUDIT_BATCH = int(os.getenv("BULK_AUDIT_BATCH", "0"))  # set >0 to demo bulk writes

# ---- Simple catalog helpers -------------------------------------------------

def get_bucket_names(conn) -> List[str]:
    rows = conn.execute(text("SELECT bucket_name FROM buckets")).fetchall()
    return [r[0] for r in rows]

def get_objects(conn) -> List[str]:
    rows = conn.execute(text("SELECT bucket_name, object_key, version_id FROM objects")).fetchall()
    return [r[0] for r in rows]

def get_bucket_policies(conn) -> List[str]:
    rows = conn.execute(text("SELECT bucket_name FROM bucket_policies")).fetchall()
    return [r[0] for r in rows]

# ---- One demo iteration -----------------------------------------------------

def demo_flow_once(db_engine: SAEngine, bucket_names: List[str], op_timer: DemoTimer, stats: DemoStats):
    # Refresh node/zone each iteration (very lightweight)
    try:
        node_id, loc = run_transaction(db_engine, lambda conn: get_node_info(conn))
        if node_id != stats.node_id or loc != stats.node_location:
            stats.update_node_info(node_id, loc)
    except Exception:
        # If we're mid-failover, this will succeed on a later iteration
        pass

    # Choose a bucket at random
    bucket_name = choice(bucket_names)

    # Read bucket metadata
    op_timer.start()
    run_transaction(db_engine, lambda conn: read_bucket(conn, bucket_name))
    stats.add_to_stats(DemoStats.OP_READ_BUCKET, op_timer.stop())

    # Read bucket policy
    op_timer.start()
    run_transaction(db_engine, lambda conn: read_bucket_policy(conn, bucket_name))
    stats.add_to_stats(DemoStats.OP_READ_BUCKET_POLICY, op_timer.stop())

    # List objects in the bucket
    op_timer.start()
    objects = run_transaction(db_engine, lambda conn: read_objects_in_bucket(conn, bucket_name))
    stats.add_to_stats(DemoStats.OP_READ_OBJECTS_IN_BUCKET, op_timer.stop())

    if not objects:
        return  # nothing to do this round

    # Choose an object version randomly
    obj_row = choice(objects)
    m = obj_row._mapping
    object_key = m["object_key"]
    version_id = m["version_id"]

    # Composite fetch + audit (records the access inside the same txn)
    op_timer.start()
    _ = run_transaction(
        db_engine,
        lambda conn: fetch_object_and_audit(conn, bucket_name, object_key, version_id)
    )
    stats.add_to_stats(DemoStats.OP_FETCH_OBJECT_AND_AUDIT, op_timer.stop())

    # # Optional: demonstrate explicit audit writes (single and bulk)
    # if BULK_AUDIT_BATCH <= 0:
    #     return

    # Single extra audit write
    op_timer.start()
    run_transaction(
        db_engine,
        lambda conn: record_object_access(conn, bucket_name, object_key, version_id, success=True)
    )
    stats.add_to_stats(DemoStats.OP_RECORD_OBJECT_ACCESS, op_timer.stop())

    # # Bulk audit writes (synthetic)
    # from datetime import datetime
    # batch = []
    # for _ in range(BULK_AUDIT_BATCH):
    #     batch.append((bucket_name, object_key, version_id, True, datetime.utcnow()))

    # op_timer.start()
    # run_transaction(
    #     db_engine,
    #     lambda conn: record_object_access_bulk(conn, batch)
    # )
    # stats.add_to_stats(DemoStats.OP_RECORD_OBJECT_ACCESS_BULK, op_timer.stop())


# ---- Main -------------------------------------------------------------------

def main():
    # Connection args (kept similar to your previous demo for drop-in ease)
    HOST        = os.getenv('DB_HOST', 'cockroachdb://root@127.0.0.1:26257/pua_demo?application_name=pua_demo')
    USER        = os.getenv('DB_USER', 'root')
    SSLCERT     = os.getenv('DB_SSLCERT', os.path.expanduser('~/.cockroach-certs/client.root.crt'))
    SSLKEY      = os.getenv('DB_SSLKEY', os.path.expanduser('~/.cockroach-certs/client.root.key'))
    SSLROOTCERT = os.getenv('DB_SSLROOTCERT', os.path.expanduser('~/.cockroach-certs/ca.crt'))
    SSLMODE     = os.getenv('DB_SSLMODE', 'require')

    args = {
        "host":        HOST,
        "port":        os.getenv('DB_PORT', '26257'),
        "user":        USER,
        "dbname":      os.getenv('DB_NAME', 'pua_demo'),
        "sslcert":     SSLCERT,
        "sslkey":      SSLKEY,
        "sslrootcert": SSLROOTCERT,
        "sslmode":     SSLMODE,
        "application_name": os.getenv('APP_NAME', 'pua_demo'),
    }
    db_engine = create_engine("cockroachdb://", connect_args=args)

    stats = DemoStats(STATS_INTERVAL_SECS, '', '')
    op_timer = DemoTimer()

    # Catalog: buckets
    bucket_names = run_transaction(db_engine, lambda conn: get_bucket_names(conn))
    print(f"{len(bucket_names)} buckets found")

    if not bucket_names:
        print("No buckets in the database. Exiting.")
        return

    # Catalog: objects
    objects = run_transaction(db_engine, lambda conn: get_objects(conn))
    print(f"{len(objects)} objects found")

    # Catalog: policies
    policies = run_transaction(db_engine, lambda conn: get_bucket_policies(conn))
    print(f"{len(policies)} policies found")

    if not bucket_names:
        print("No buckets in the database. Exiting.")
        return


    while True:
        demo_flow_once(db_engine, bucket_names, op_timer, stats)
        stats.display_if_ready()


if __name__ == '__main__':
    # Gracefully handle CTRL-C
    def sigint_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, sigint_handler)

    main()
