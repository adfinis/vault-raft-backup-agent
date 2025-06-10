#!/usr/bin/env sh

set -e

# Set default Vault auth path if not provided
VAULT_AUTH_PATH=${VAULT_AUTH_PATH:-kubernetes}

echo "Using Vault auth path: $VAULT_AUTH_PATH"

# Authenticate with Vault
JWT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
export JWT

echo "Using Vault auth path: $VAULT_AUTH_PATH"
VAULT_TOKEN=$(vault write -field=token "auth/$VAULT_AUTH_PATH/login" role="${VAULT_ROLE}" jwt="$JWT")
export VAULT_TOKEN

# Create snapshot
vault operator raft snapshot save /vault-snapshots/vault_"$(date +%F-%H%M)".snapshot

# Upload to S3
s3cmd put /vault-snapshots/* "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"

# Remove expired snapshots
if [ "${S3_EXPIRE_DAYS}" ]; then
    s3cmd ls "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}" | while read -r line; do
        createDate=$(echo "$line" | awk '{print $1" "$2}')
        createDate=$(date -d"$createDate" +%s)
        olderThan=$(date --date @$(($(date +%s) - 86400*S3_EXPIRE_DAYS)) +%s)
        if [ "$createDate" -lt "$olderThan" ]; then
            fileName=$(echo "$line" | awk '{print $4}')
            if [ "$fileName" != "" ]; then
                s3cmd del "$fileName" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"
            fi
        fi
    done;
fi