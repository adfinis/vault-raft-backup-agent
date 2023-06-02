#!/usr/bin/env sh

# authenticate using kubernetes auth
export JWT=$(cat /var/run/secrets/kubernetes/io/serviceaccount/token)
export VAULT_TOKEN=$(vault write -field=token  auth/kubernetes/login role=$VAULT_ROLE jwt=$JWT)

# use the leader node as VAULT_ADDR
export VAULT_ADDR=$(vault status -format=yaml | egrep -o '^leader_addr.*' | awk '{print $2}')

# create snapshot

vault operator raft snapshot save /vault-snapshots/vault_$(date +%F-%H%M).snapshot

# upload to s3
s3cmd put /vault-snapshots/* $S3_URI --host=$S3_HOST --host-bucket=$S3_BUCKET
