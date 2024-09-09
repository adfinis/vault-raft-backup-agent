#!/usr/bin/env sh

# authenticate using kubernetes auth
JWT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
export JWT
VAULT_TOKEN=$(vault write -field=token  auth/kubernetes/login role="${VAULT_ROLE}" jwt="${JWT}")
export VAULT_TOKEN

# create snapshot
vault operator raft snapshot save /vault-snapshots/vault_"$(date +%F-%H%M)".snapshot

# upload to s3
s3cmd put /vault-snapshots/* "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"

# remove expired snapshots
if [ "${S3_EXPIRE_DAYS}" ]; then
    s3cmd ls "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}" | while read -r line; do
        createDate=$(echo "$line" | awk '{print $1" "$2}')
        createDate=$(date -d"$createDate" +%s)
        olderThan=$(date --date "${S3_EXPIRE_DAYS} days ago" +%s)
        if [ $createDate -lt $olderThan ]; then
            fileName=$(echo "$line" | awk '{print $4}')
            if [ $fileName != "" ]; then
                s3cmd del "${S3_URI}/$fileName" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"
            fi
        fi
    done;
fi
