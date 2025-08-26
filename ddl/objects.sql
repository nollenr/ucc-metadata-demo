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
