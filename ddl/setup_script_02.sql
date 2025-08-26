
IMPORT INTO pua_demo.buckets (
    bucket_name,
    owner_principal,
    availability_zone,
    versioning_enabled,
    lifecycle_policy,
    audit_logging_enabled,
    created_at
)
CSV DATA ('http://192.168.3.107:3000/buckets_1.csv',
'http://192.168.3.107:3000/buckets_2.csv',
'http://192.168.3.107:3000/buckets_3.csv',
'http://192.168.3.107:3000/buckets_4.csv',
'http://192.168.3.107:3000/buckets_5.csv',
'http://192.168.3.107:3000/buckets_6.csv',
'http://192.168.3.107:3000/buckets_7.csv',
'http://192.168.3.107:3000/buckets_8.csv',
'http://192.168.3.107:3000/buckets_9.csv',
'http://192.168.3.107:3000/buckets_10.csv',
'http://192.168.3.107:3000/buckets_11.csv',
'http://192.168.3.107:3000/buckets_12.csv',
'http://192.168.3.107:3000/buckets_13.csv',
'http://192.168.3.107:3000/buckets_14.csv',
'http://192.168.3.107:3000/buckets_15.csv',
'http://192.168.3.107:3000/buckets_16.csv',
'http://192.168.3.107:3000/buckets_17.csv',
'http://192.168.3.107:3000/buckets_18.csv',
'http://192.168.3.107:3000/buckets_19.csv',
'http://192.168.3.107:3000/buckets_20.csv')
WITH skip = '1';

IMPORT INTO pua_demo.objects (
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
  'http://192.168.3.107:3000/objects_1.csv',
  'http://192.168.3.107:3000/objects_2.csv',
  'http://192.168.3.107:3000/objects_3.csv',
  'http://192.168.3.107:3000/objects_4.csv',
  'http://192.168.3.107:3000/objects_5.csv',
  'http://192.168.3.107:3000/objects_6.csv',
  'http://192.168.3.107:3000/objects_7.csv',
  'http://192.168.3.107:3000/objects_8.csv',
  'http://192.168.3.107:3000/objects_9.csv',
  'http://192.168.3.107:3000/objects_10.csv',
  'http://192.168.3.107:3000/objects_11.csv',
  'http://192.168.3.107:3000/objects_12.csv',
  'http://192.168.3.107:3000/objects_13.csv',
  'http://192.168.3.107:3000/objects_14.csv',
  'http://192.168.3.107:3000/objects_15.csv',
  'http://192.168.3.107:3000/objects_16.csv',
  'http://192.168.3.107:3000/objects_17.csv',
  'http://192.168.3.107:3000/objects_18.csv',
  'http://192.168.3.107:3000/objects_19.csv',
  'http://192.168.3.107:3000/objects_20.csv'
)
WITH skip = '1';

IMPORT INTO pua_demo.bucket_policies (
  bucket_name,
  policy,
  updated_at
)
CSV DATA ('http://192.168.3.107:3000/bucket_policies.csv')
WITH skip = '1';

IMPORT INTO pua_demo.object_access_requests (
  bucket_name,
  object_key,
  version_id,
  accessed_at,
  success_fail
)
CSV DATA ('http://192.168.3.107:3000/object_access_requests.csv')
WITH skip = '1';
