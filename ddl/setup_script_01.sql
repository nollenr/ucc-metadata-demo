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

CREATE TABLE bucket_policies (
  bucket_name TEXT REFERENCES buckets(bucket_name) PRIMARY KEY,
  policy JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE object_access_requests(
  bucket_name TEXT NOT NULL,
  object_key TEXT NOT NULL,
  version_id TEXT NOT NULL,
  accessed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  success_fail BOOLEAN NOT NULL,
  FOREIGN KEY (bucket_name, object_key, version_id) REFERENCES objects (bucket_name, object_key, version_id) MATCH FULL ON DELETE CASCADE ON UPDATE CASCADE
);

