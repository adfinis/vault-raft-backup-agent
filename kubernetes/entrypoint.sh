#!/usr/bin/env sh

# authenticate using kubernetes auth
JWT=$(cat /var/run/secrets/kubernetes/io/serviceaccount/token)
export JWT
VAULT_TOKEN=$(vault write -field=token  auth/kubernetes/login role="${VAULT_ROLE}" jwt="${JWT}")
export VAULT_TOKEN

# use the leader node as VAULT_ADDR
VAULT_ADDR=$(vault status -format=yaml | grep -Eo '^leader_addr.*' | awk '{print $2}')
export VAULT_ADDR

# create snapshot

vault operator raft snapshot save /vault-snapshots/vault_"$(date +%F-%H%M)".snapshot

# upload to s3
s3cmd put /vault-snapshots/* "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"
