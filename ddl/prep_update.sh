export crdb_version="25.2.4"
curl https://binaries.cockroachdb.com/cockroach-v${crdb_version}.linux-arm64.tgz | tar -xz && sudo cp -i cockroach-v${crdb_version}.linux-arm64/cockroach /usr/local/bin/cockroach${crdb_version}

