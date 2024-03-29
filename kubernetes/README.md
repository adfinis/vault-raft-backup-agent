# Cronjob for snapshotting Vault running on Kubernetes

This assumes the Kubernetes authentication backend is configured in Vault.

The script being executed in this cronjob, is authenticating with Vault using the Kubernetes authentication backend, via its serviceaccount JWT.

The role and policy being used must be created before hand and must be used by the cronjob.

After the snapshot is created in a temporary directory, `s3cmd` is used to sync it to a s3 endpoint.

## Configuration over environment variables

* `VAULT_ADDR`  - Vault address to access
* `VAULT_ROLE` - Vault role to use to create the snapshot
* `S3_URI` - S3 URI to use to upload (s3://xxx)
* `S3_BUCKET` - S3 bucket to point to
* `S3_HOST` - S3 endpoint
* `AWS_ACCESS_KEY_ID` - Access key to use to access S3
* `AWS_SECRET_ACCESS_KEY` - Secret access key to use to access S3
