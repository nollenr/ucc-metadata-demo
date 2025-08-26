CREATE TABLE buckets (
  bucket_name TEXT PRIMARY KEY,
  owner_principal TEXT NOT NULL,
  availability_zone TEXT NOT NULL,
  versioning_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  lifecycle_policy JSONB,
  audit_logging_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

