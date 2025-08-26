
ALTER TABLE pua_demo.buckets SPLIT AT VALUES ('g'), ('q') WITH EXPIRATION INTERVAL '1yr';
ALTER TABLE pua_demo.buckets SCATTER;
ALTER TABLE pua_demo.objects SPLIT AT VALUES ('g'), ('q') WITH EXPIRATION INTERVAL '1yr';
ALTER TABLE pua_demo.objects SCATTER;

WITH ranked AS (
  SELECT rowid, ntile(12) OVER (ORDER BY random()) AS bucket
  FROM pua_demo.object_access_requests
)
UPDATE pua_demo.object_access_requests AS t
SET accessed_at = now() - ((13 - r.bucket) * INTERVAL '1 hour')
FROM ranked AS r
WHERE t.rowid = r.rowid;

select accessed_at, count(*) from pua_demo.object_access_requests group by
accessed_at order by 1;

ALTER TABLE pua_demo.object_access_requests
  SET (ttl_expiration_expression = $$(accessed_at + INTERVAL '12 hours')$$);

ALTER TABLE pua_demo.object_access_requests
  SET (ttl_job_cron = '@hourly');

