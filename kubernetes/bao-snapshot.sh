#!/usr/bin/env sh

set -e

# Set default Vault auth path if not provided
VAULT_AUTH_PATH=${VAULT_AUTH_PATH:-kubernetes}

echo "Using Vault auth path: $VAULT_AUTH_PATH"

# Authenticate with Vault
JWT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
export JWT
<<<<<<< HEAD:kubernetes/vault-snapshot.sh

echo "Using Vault auth path: $VAULT_AUTH_PATH"
VAULT_TOKEN=$(vault write -field=token "auth/$VAULT_AUTH_PATH/login" role="${VAULT_ROLE}" jwt="$JWT")
export VAULT_TOKEN
||||||| parent of 2d9c663 (feat: OpenBao raft backup agent):kubernetes/vault-snapshot.sh
VAULT_TOKEN=$(vault write -field=token  auth/kubernetes/login role="${VAULT_ROLE}" jwt="${JWT}")
export VAULT_TOKEN
=======
BAO_TOKEN=$(bao write -field=token  auth/${BAO_AUTH_PATH}/login role="${BAO_ROLE}" jwt="${JWT}")
export BAO_TOKEN
>>>>>>> 2d9c663 (feat: OpenBao raft backup agent):kubernetes/bao-snapshot.sh

<<<<<<< HEAD:kubernetes/vault-snapshot.sh
# Create snapshot
vault operator raft snapshot save /vault-snapshots/vault_"$(date +%F-%H%M)".snapshot
||||||| parent of 2d9c663 (feat: OpenBao raft backup agent):kubernetes/vault-snapshot.sh
# create snapshot
vault operator raft snapshot save /vault-snapshots/vault_"$(date +%F-%H%M)".snapshot
=======
# create snapshot
bao operator raft snapshot save /bao-snapshots/bao_"$(date +%F-%H%M)".snapshot
>>>>>>> 2d9c663 (feat: OpenBao raft backup agent):kubernetes/bao-snapshot.sh

<<<<<<< HEAD:kubernetes/vault-snapshot.sh
# Upload to S3
s3cmd put /vault-snapshots/* "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"
||||||| parent of 2d9c663 (feat: OpenBao raft backup agent):kubernetes/vault-snapshot.sh
# upload to s3
s3cmd put /vault-snapshots/* "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"
=======
# upload to s3
s3cmd put /bao-snapshots/* "${S3_URI}" --host="${S3_HOST}" --host-bucket="${S3_BUCKET}"
>>>>>>> 2d9c663 (feat: OpenBao raft backup agent):kubernetes/bao-snapshot.sh

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
