# Installation and configuration on Kubernetes

On Kubernetes, the approach is to deploy a [Cronjob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) that will run a container images tailored to take snapshot of an OpenBao server at regular interval.

Currently, the container image only supports S3 as the final storage for the snapshots.

## Configure Authentication

On Kubernetes, you can choose between using [JWT Authentication](https://openbao.org/docs/auth/jwt/oidc-providers/kubernetes/) or [Kubernetes Authentication](https://openbao.org/docs/auth/kubernetes/). The instructions below provides a straighforward approach to configure both methods to use with the Kubernetes Cronjob.

### OpenBao Policy

Policy for the snapshot agent:
```bash
echo '
path "sys/storage/raft/snapshot" {
   capabilities = ["read"]
}' | bao policy write snapshot -
```

### Kubernetes authentication

This is a very straightforward example and might not work for your infrastructure. For more details, check the documentation on [openbao.org](https://openbao.org/docs/auth/kubernetes/).

1. Enable the Kubernetes authentication method:
```bash
bao auth enable kubernetes
```

2. Configure the Kubernetes authentication method:
```bash
bao write auth/kubernetes/config \
    kubernetes_host=https://192.168.99.100:<your TCP port or blank for 443>
```

3. Create a role:
```bash
bao write auth/kubernetes/role/bao-snapshot \
    bound_service_account_names=bao-snapshot \
    bound_service_account_namespaces=bao-snapshot \
    policies=snapshot \
    ttl=1h
```

### JWT Authentication

This is a very straightforward example and might not work for your infrastructure. For more details, check the documentation on [openbao.org](https://openbao.org/docs/auth/jwt/oidc-providers/kubernetes/).

1. Enable the JWT authentication method:
```bash
bao auth enable jwt
```

2. Fetch signing public keys from your Kubernetes cluster:
```bash
kubectl get --raw "$(kubectl get --raw /.well-known/openid-configuration | jq -r '.jwks_uri' | sed -r 's/.*\.[^/]+(.*)/\1/')"
```

3. Configure the authentication method:
```bash
bao write auth/jwt/config \
   jwt_validation_pubkeys="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9...
-----END PUBLIC KEY-----"
```

4. Retrive the default audience claim of the Kubernetes cluster:

```bash
kubectl create token default | cut -f2 -d. | base64 --decode
{"aud":["https://kubernetes.default.svc.cluster.local"], ...}
```

5. Create a role:
```bash
bao write auth/jwt/role/bao-snapshot \
   role_type="jwt" \
   bound_audiences="https://kubernetes.default.svc.cluster.local" \
   user_claim="sub" \
   bound_subject="system:serviceaccount:bao-snapshot:bao-snapshot" \
   policies="default" \
   ttl="1h"
```

## Configure the environement variables

In `kubernetes/cronjob.yaml`, configure the environement variables according to your setup.

* `BAO_ADDR`  - OpenBao address to access
* `BAO_ROLE` - OpenBao role to use to create the snapshot
* `BAO_AUTH_METHOD` - Path of the OpenBao authentication method to use
* `S3_URI` - S3 URI to use to upload (s3://xxx)
* `S3_BUCKET` - S3 bucket to point to
* `S3_HOST` - S3 endpoint
* `S3_EXPIRE_DAYS` - Delete files older than this threshold (expired)
* `AWS_ACCESS_KEY_ID` - Access key to use to access S3
* `AWS_SECRET_ACCESS_KEY` - Secret access key to use to access S3

## Deploy Kubernetes Cronjob

Create the destination namespace :
```bash
kubectl create ns -n bao-snapshot
```

Create the service account used for authentication:
```bash
kubectl create sa -n bao-snapshot bao-snapshot
```

Deploy the Kubernetes cronjob:
```bash
kubectl apply -n bao-snapshot -f kubernetes/cronjob.yaml
```
