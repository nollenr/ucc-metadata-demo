CREATE DATABASE pua_demo;

USE pua_demo;
CREATE TABLE public.buckets (
	bucket_name STRING NOT NULL,
	owner_principal STRING NOT NULL,
	availability_zone STRING NOT NULL,
	versioning_enabled BOOL NOT NULL DEFAULT false,
	lifecycle_policy JSONB NULL,
	audit_logging_enabled BOOL NOT NULL DEFAULT false,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	CONSTRAINT buckets_pkey PRIMARY KEY (bucket_name ASC)
);
