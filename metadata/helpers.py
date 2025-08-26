from datetime import datetime as dt
from statistics import mean
from time import perf_counter, sleep
from threading import RLock
import psycopg2
from sqlalchemy.engine import Engine as SAEngine
from sqlalchemy.exc import DBAPIError

class OpStats:
    def __init__(self, op_name: str) -> None:
        self.name = op_name

        # Stats as they are collected
        self.count = 0
        self.ms_sum = 0.0

        # Stats after being calculated for a reporting interval
        self.last_count = 0
        self.last_ops = 0.0
        self.last_ms_avg = 0.0

    def __str__(self):
        return (
            f"OpStats: name={self.name} count={self.count} ms_sum={self.ms_sum} "
            f"last_count={self.last_count} last_ops={self.last_ops} last_ms_avg={self.last_ms_avg}"
        )


class DemoStats:
    """Thread-safe aggregator for PUA demo operations."""

    # ---- Operation names (align with pua_transactions.py) -------------------
    OP_READ_BUCKET = "read_bucket"
    OP_READ_BUCKET_POLICY = "read_bucket_policy"
    OP_READ_OBJECTS_IN_BUCKET = "read_objects_in_bucket"
    OP_RECORD_OBJECT_ACCESS = "record_object_access"
    OP_RECORD_OBJECT_ACCESS_BULK = "record_object_access_bulk"
    OP_FETCH_OBJECT_AND_AUDIT = "fetch_object_and_audit"  # transactional composite

    def __init__(self, reporting_inteval_secs: int, node_id: int, node_location: str) -> None:
        self.node_id = node_id
        self.node_location = node_location
        self.reporting_secs = reporting_inteval_secs
        self.lock = RLock()  # Make this thread safe

        self.reporting_timer = DemoTimer()
        self.reporting_timer.start()

        self.op_names = [
            DemoStats.OP_READ_BUCKET,
            DemoStats.OP_READ_BUCKET_POLICY,
            DemoStats.OP_READ_OBJECTS_IN_BUCKET,
            DemoStats.OP_RECORD_OBJECT_ACCESS,
            DemoStats.OP_RECORD_OBJECT_ACCESS_BULK,
            DemoStats.OP_FETCH_OBJECT_AND_AUDIT,
        ]

        self.stats_objs = {op: OpStats(op) for op in self.op_names}

    def update_node_info(self, node_id: int, node_location: str) -> None:
        self.node_id = node_id
        self.node_location = node_location

    def add_to_stats(self, op_name: str, time_ms: float) -> None:
        """Record a single operation's latency in milliseconds.

        If a new op_name is seen, create an OpStats for it automatically.
        """
        with self.lock:
            stat = self.stats_objs.setdefault(op_name, OpStats(op_name))  # type: OpStats
            stat.count += 1
            stat.ms_sum += time_ms

    def calc_and_reset_stats(self) -> None:
        """Compute interval metrics and reset counters for the next window."""
        with self.lock:
            for op_name, stat in self.stats_objs.items():  # type: ignore
                if stat.count > 0:
                    stat.last_count = stat.count
                    stat.last_ops = stat.count / self.reporting_secs
                    stat.last_ms_avg = stat.ms_sum / stat.count
                else:
                    # Explicitly zero out for intervals with no activity
                    stat.last_count = 0
                    stat.last_ops = 0.0
                    stat.last_ms_avg = 0.0

                # Reset counting stats
                stat.count = 0
                stat.ms_sum = 0.0

    def display_if_ready(self) -> None:
        if self.reporting_timer.get() > self.reporting_secs * 1000:
            self.reporting_timer.start()  # Reset the stats timer
            self.calc_and_reset_stats()

            statstime = dt.now()  # time of the stats

            # Grouped summaries for the PUA demo
            metadata_reads_ms = mean([
                self.stats_objs[self.OP_READ_BUCKET].last_ms_avg,
                self.stats_objs[self.OP_READ_BUCKET_POLICY].last_ms_avg,
            ])
            object_list_ms = self.stats_objs[self.OP_READ_OBJECTS_IN_BUCKET].last_ms_avg
            audit_writes_ms = mean([
                self.stats_objs[self.OP_RECORD_OBJECT_ACCESS].last_ms_avg,
                self.stats_objs[self.OP_RECORD_OBJECT_ACCESS_BULK].last_ms_avg,
            ])
            composite_txn_ms = self.stats_objs[self.OP_FETCH_OBJECT_AND_AUDIT].last_ms_avg

            # Build rows and compute dynamic widths
            rows = [
                ("reads:", metadata_reads_ms),
                ("list in bucket:", object_list_ms),
                ("writes:", audit_writes_ms),
                ("fetch_object_and_audit:", composite_txn_ms),
            ]
            label_w = max(len(lbl) for lbl, _ in rows)  # longest label width
            num_w = 10  # width for the numeric column (e.g., "  12345.67")

            def line(lbl: str, val: float) -> None:
                print(f"  {lbl:<{label_w}}  {val:>{num_w}.2f} ms avg")

            rule_len = label_w + num_w + 8

            print(f"{statstime:%Y-%m-%d %H:%M:%S}  node: {self.node_id}")
            print(self.node_location)
            print("-" * rule_len)

            print("Lookups (buckets, bucket_policies)")
            line("reads:", metadata_reads_ms)
            print()

            print("Objects")
            line("list in bucket:", object_list_ms)
            print()

            print("Audits (object_access_requests)")
            line("writes:", audit_writes_ms)
            print()

            print("Composite")
            line("fetch_object_and_audit:", composite_txn_ms)
            print()


class DemoTimer:
    """This is NOT thread safe. Each thread should use its own instance."""

    def __init__(self) -> None:
        self.starttime: float | None = None  # Seconds

    def start(self) -> None:
        self.starttime = perf_counter()

    def stop(self) -> float:
        """Stops the timer, and returns the elapsed time in milliseconds"""
        stoptime = perf_counter()
        if self.starttime is None:
            return 0.0
        time_ms = (stoptime - self.starttime) * 1000
        return time_ms

    def get(self) -> float:
        """Does the same thing as stop, since stop doesn't actually stop the timer"""
        return self.stop()


def run_transaction(db_engine, txn_func, max_retries: int | None = 10):
    retry_count = 0
    while True:
        try:
            # No .execution_options(isolation_level="AUTOCOMMIT")
            with db_engine.connect() as conn:
                return txn_func(conn)

        except (DBAPIError, psycopg2.OperationalError) as e:
            # Pull pgcode if present (psycopg2)
            orig = getattr(e, "orig", e)
            pgcode = getattr(orig, "pgcode", None)

            # Retryable Cockroach errors
            if pgcode in ("40001", "40003"):
                if max_retries is not None and retry_count >= max_retries:
                    raise
                retry_count += 1
                print(f"Retrying {retry_count}/{max_retries} on PG error #{pgcode}")
                continue

            # Detect disconnects (dead socket / EOF / server closed conn)
            is_disconnect = getattr(e, "connection_invalidated", False)
            try:
                is_disconnect = is_disconnect or bool(getattr(e, "is_disconnect", False))
            except Exception:
                pass

            if is_disconnect or isinstance(orig, psycopg2.OperationalError):
                print(f"Disconnect detected{f' (PG {pgcode})' if pgcode else ''}; disposing pool and reconnecting…")
                try:
                    db_engine.dispose()  # drop dead connections from the pool
                except Exception:
                    pass
                retry_count = 0   # allow indefinite retry for disconnects
                sleep(1)
                continue

            # Unknown DBAPI error
            raise