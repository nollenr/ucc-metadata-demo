-- Version: CockroachDB CCL v25.2.4 (aarch64-unknown-linux-gnu, built 2025/07/31 21:22:08, go1.23.7 X:nocoverageredesign)

-- User: ron

SET application_name = 'pua_demo';  -- default value: 
-- read-only authentication_method = cert-password
SET database = 'pua_demo';  -- default value: 
SET direct_columnar_scans_enabled = off;  -- default value: off
-- read-only is_superuser = on
-- read-only locality = region=us-east-2,zone=us-east-2b
-- read-only node_id = 3
-- read-only results_buffer_size = 524288
-- read-only session_id = 185bfa1b8f84008d0000000000000003
-- read-only ssl = on
-- read-only transaction_priority = normal
SET transaction_read_only = on;  -- default value: off
-- read-only transaction_status = Open

SET CLUSTER SETTING cluster.auto_upgrade.enabled = 'false';  -- default value: true
SET CLUSTER SETTING cluster.organization = 'CockroachLabs';  -- default value: 
SET CLUSTER SETTING kv.snapshot_rebalance.max_rate = '3.7 GiB';  -- default value: 32 MiB
SET CLUSTER SETTING server.time_until_store_dead = '1m15s';  -- default value: 5m0s
