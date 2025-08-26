#!/usr/bin/env bash

export crdb_version="25.2.4"

sudo systemctl stop securecockroachdb


# wait-until-no-cockroach.sh
set -euo pipefail

echo "Waiting for cockroach processes to exit..."
while pgrep -x cockroach >/dev/null 2>&1; do
  sleep 1
done
echo "All cockroach processes have exited."

sudo mv /usr/local/bin/cockroach /usr/local/bin/cockroach.old
sudo mv /usr/local/bin/cockroach${crdb_version} /usr/local/bin/cockroach
echo "cockroach binary replaced"
echo "starting CRDB"

sudo systemctl start securecockroachdb
echo "CRDB Started"
