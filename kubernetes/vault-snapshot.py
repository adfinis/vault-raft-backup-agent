#!/usr/bin/env python

import logging
import boto3
from botocore.exceptions import ClientError
from hvac.api.auth_methods import Kubernetes
import hvac
import os
from datetime import datetime

vault_addr           = os.environ['VAULT_ADDR']
vault_token          = os.environ['VAULT_TOKEN']
s3_access_key_id     = os.environ['AWS_ACCESS_KEY_ID']
s3_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
# Example "https://my-remote-s3.com"
s3_host              = os.environ['S3_HOST']
# Example "my-bucket"
s3_bucket            = os.environ['S3_BUCKET']

# Authenticate with Kubernetes ServiceAccount if vault_token is empty
# https://hvac.readthedocs.io/en/stable/usage/auth_methods/kubernetes.html
#hvac_client = hvac.Client(url=url, verify=certificate_path)
#f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
#jwt = f.read()
####VAULT_TOKEN=$(vault write -field=token  auth/kubernetes/login role="${VAULT_ROLE}" jwt="${JWT}")
#Kubernetes(hvac_client.adapter).login(role=role, jwt=jwt)

hvac_client = hvac.Client(url=vault_addr)
hvac_client.token = vault_token

assert hvac_client.is_authenticated()

# Create snapshot. The snapshot is returned as binary data and should be
# redirected to a file:
# - https://developer.hashicorp.com/vault/api-docs/system/storage/raft
# - https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html
with hvac_client.sys.take_raft_snapshot() as resp:
    assert resp.ok

    print("Status code: %d" % resp.status_code)

    date_str = datetime.now().strftime("%F-%H%M")
    file_name = "vault_%s.snapshot" % (date_str)
    print("File name:" + file_name)

    # Upload the file
    # - https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
    # - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
    s3_client = boto3.client(service_name='s3',
                             endpoint_url=s3_host,
                             aws_access_key_id=s3_access_key_id,
                             aws_secret_access_key=s3_secret_access_key)
    try:
        response = s3_client.put_object(
            Body=resp.content,
            Bucket=s3_bucket,
            Key=file_name,
        )
        print(response)
    except ClientError as e:
        logging.error(e)

# Iterate and remove expired snapshots:
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/migrations3.html
s3 = boto3.resource(service_name='s3',
                    endpoint_url=s3_host,
                    aws_access_key_id=s3_access_key_id,
                    aws_secret_access_key=s3_secret_access_key)
bucket = s3.Bucket(s3_bucket)
for key in bucket.objects.all():
    print(key.key)
    # todo: do the S3_EXPIRE_DAYS magic
