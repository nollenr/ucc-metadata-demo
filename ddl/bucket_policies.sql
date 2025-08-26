CREATE TABLE bucket_policies (
  bucket_name TEXT REFERENCES buckets(bucket_name) PRIMARY KEY,
  policy JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);