terraform a 24.3 database

WHY IS THE NODE MAP NOT INSTALLED?!?!?!

Install License Keys
SETCRDBVARS

show cluster setting cluster.auto_upgrade.enabled;
SET CLUSTER SETTING cluster.auto_upgrade.enabled=false;



After the update script is complete, the following will be executed in the database
```
SHOW CLUSTER SETTING version;
SET CLUSTER SETTING version='25.2';
```

# Setup
## Database
Copy the folder demo_data the app server

On the app server, from the directory containing the files, run the following
python3 -m http.server --bind 192.168.7.107 3000

In the database
```
create database pua_demo;
use pua_demo ;
CREATE TABLE buckets (
  bucket_name TEXT PRIMARY KEY,
  owner_principal TEXT NOT NULL,
  availability_zone TEXT NOT NULL,
  versioning_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  lifecycle_policy JSONB,
  audit_logging_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

IMPORT INTO buckets (
    bucket_name,
    owner_principal,
    availability_zone,
    versioning_enabled,
    lifecycle_policy,
    audit_logging_enabled,
    created_at
)
CSV DATA ('http://192.168.7.107:3000/buckets_1.csv',
'http://192.168.7.107:3000/buckets_2.csv',
'http://192.168.7.107:3000/buckets_3.csv',
'http://192.168.7.107:3000/buckets_4.csv',
'http://192.168.7.107:3000/buckets_5.csv',
'http://192.168.7.107:3000/buckets_6.csv',
'http://192.168.7.107:3000/buckets_7.csv',
'http://192.168.7.107:3000/buckets_8.csv',
'http://192.168.7.107:3000/buckets_9.csv',
'http://192.168.7.107:3000/buckets_10.csv',
'http://192.168.7.107:3000/buckets_11.csv',
'http://192.168.7.107:3000/buckets_12.csv',
'http://192.168.7.107:3000/buckets_13.csv',
'http://192.168.7.107:3000/buckets_14.csv',
'http://192.168.7.107:3000/buckets_15.csv',
'http://192.168.7.107:3000/buckets_16.csv',
'http://192.168.7.107:3000/buckets_17.csv',
'http://192.168.7.107:3000/buckets_18.csv',
'http://192.168.7.107:3000/buckets_19.csv',
'http://192.168.7.107:3000/buckets_20.csv')
WITH skip = '1';

CREATE TABLE objects (
  bucket_name TEXT REFERENCES buckets(bucket_name),
  object_key TEXT NOT NULL,
  version_id TEXT NOT NULL,
  size BIGINT NOT NULL,
  etag TEXT NOT NULL,
  last_modified TIMESTAMPTZ NOT NULL DEFAULT now(),
  storage_class TEXT,
  metadata JSONB,
  is_latest BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (bucket_name, object_key, version_id)
);


IMPORT INTO objects (
  bucket_name,
  object_key,
  version_id,
  size,
  etag,
  last_modified,
  storage_class,
  metadata,
  is_latest
)
CSV DATA (
  'http://192.168.7.107:3000/objects_1.csv',
  'http://192.168.7.107:3000/objects_2.csv',
  'http://192.168.7.107:3000/objects_3.csv',
  'http://192.168.7.107:3000/objects_4.csv',
  'http://192.168.7.107:3000/objects_5.csv',
  'http://192.168.7.107:3000/objects_6.csv',
  'http://192.168.7.107:3000/objects_7.csv',
  'http://192.168.7.107:3000/objects_8.csv',
  'http://192.168.7.107:3000/objects_9.csv',
  'http://192.168.7.107:3000/objects_10.csv',
  'http://192.168.7.107:3000/objects_11.csv',
  'http://192.168.7.107:3000/objects_12.csv',
  'http://192.168.7.107:3000/objects_13.csv',
  'http://192.168.7.107:3000/objects_14.csv',
  'http://192.168.7.107:3000/objects_15.csv',
  'http://192.168.7.107:3000/objects_16.csv',
  'http://192.168.7.107:3000/objects_17.csv',
  'http://192.168.7.107:3000/objects_18.csv',
  'http://192.168.7.107:3000/objects_19.csv',
  'http://192.168.7.107:3000/objects_20.csv'
)
WITH skip = '1';

CREATE TABLE bucket_policies (
  bucket_name TEXT REFERENCES buckets(bucket_name) PRIMARY KEY,
  policy JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

IMPORT INTO bucket_policies (
  bucket_name,
  policy,
  updated_at
)
CSV DATA ('http://192.168.7.107:3000/bucket_policies.csv')
WITH skip = '1';

CREATE TABLE object_access_requests(
  bucket_name TEXT NOT NULL,
  object_key TEXT NOT NULL,
  version_id TEXT NOT NULL,
  accessed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  success_fail BOOLEAN NOT NULL,
  FOREIGN KEY (bucket_name, object_key, version_id) REFERENCES objects (bucket_name, object_key, version_id) MATCH FULL ON DELETE CASCADE ON UPDATE CASCADE
);

IMPORT INTO object_access_requests (
  bucket_name,
  object_key,
  version_id,
  accessed_at,
  success_fail
)
CSV DATA ('http://192.168.7.107:3000/object_access_requests.csv')
WITH skip = '1';

ALTER TABLE buckets SPLIT AT VALUES ('g'), ('q') WITH EXPIRATION INTERVAL '1yr';
ALTER TABLE buckets SCATTER;
ALTER TABLE objects SPLIT AT VALUES ('g'), ('q') WITH EXPIRATION INTERVAL '1yr';
ALTER TABLE objects SCATTER;

WITH ranked AS (
  SELECT rowid, ntile(12) OVER (ORDER BY random()) AS bucket
  FROM object_access_requests
)
UPDATE object_access_requests AS t
SET accessed_at = now() - ((13 - r.bucket) * INTERVAL '1 hour')
FROM ranked AS r
WHERE t.rowid = r.rowid;

select accessed_at, count(*) from object_access_requests group by
accessed_at order by 1;

ALTER TABLE object_access_requests
  SET (ttl_expiration_expression = $$(accessed_at + INTERVAL '12 hours')$$);

ALTER TABLE object_access_requests
  SET (ttl_job_cron = '@hourly');

```

## CRDB Instances
- run `SETCRDBVARS`

- Stage the update
  - copy prep_update.sh to 1st instance
    - figure out which node you're on (`echo CRDBNODE1`, etc until you find the matching IP)
    - `scp prep_update.sh $CRDBNODE1:.` to all other nodes
  - run prep_update.sh on all nodes
    - Run on all nodes `ssh $CRDBNODE1 'bash -lc "~/prep_update.sh"'`


- Execute the Update on all nodes except the "last" node
  - copy apply_update.sh to 1st instance
    - figure out which node you're on (`echo CRDBNODE1`, etc until you find the matching IP)
    - `scp apply_update.sh $CRDBNODE1:.` to all other nodes
  - run apply_update.sh on all nodes **EXCEPT THE LAST ONE**!!
    - DO NOT RUN THIS ON THE LAST NODE! `ssh -t "$CRDBNODE1" 'bash -lic "source ~/.bashrc; source $HOME/apply_update.sh"'`