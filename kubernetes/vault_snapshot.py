#!/usr/bin/env python

import logging
import boto3
from botocore.exceptions import ClientError
from hvac.api.auth_methods import Kubernetes
import hvac
import os
import datetime

class VaultSnapshot:
    """
    Create Vault snapshots on S3.
    """

    def __init__(self, **kwargs):
        """
        Init S3 and hvac clients
        """

        # setup logger
        self.logger = logging.getLogger(__name__)

        # read input keyword arguments
        if "vault_addr" in kwargs:
            self.vault_addr = kwargs['vault_addr']
        elif "VAULT_ADDR" in os.environ:
            self.vault_addr = os.environ['VAULT_ADDR']
        else:
            raise NameError("VAULT_ADDR undefined")

        if "vault_token" in kwargs:
            self.vault_token = kwargs['vault_token']
        elif "VAULT_TOKEN" in os.environ:
            self.vault_token = os.environ['VAULT_TOKEN']
        else:
            raise NameError("VAULT_TOKEN undefined")

        if "s3_access_key_id" in kwargs:
            self.s3_access_key_id = kwargs['s3_access_key_id']
        elif "AWS_ACCESS_KEY_ID" in os.environ:
            self.s3_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
        else:
            raise NameError("AWS_ACCESS_KEY_ID undefined")

        if "s3_secret_access_key" in kwargs:
            self.s3_secret_access_key = kwargs['s3_secret_access_key']
        elif "AWS_SECRET_ACCESS_KEY" in os.environ:
            self.s3_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
        else:
            raise NameError("AWS_SECRET_ACCESS_KEY undefined")

        if "s3_host" in kwargs:
            self.s3_host = kwargs['s3_host']
        elif "S3_HOST" in os.environ:
            self.s3_host = os.environ['S3_HOST']
        else:
            raise NameError("S3_HOST undefined")

        if "s3_bucket" in kwargs:
            self.s3_bucket = kwargs['s3_bucket']
        elif "S3_BUCKET" in os.environ:
            self.s3_bucket = os.environ['S3_BUCKET']
        else:
            raise NameError("S3_BUCKET undefined")

        # Boto S3 client
        # * https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
        self.s3_client = boto3.client(service_name='s3',
                         endpoint_url=self.s3_host,
                         aws_access_key_id=self.s3_access_key_id,
                         aws_secret_access_key=self.s3_secret_access_key)

        # Authenticate with Kubernetes ServiceAccount if vault_token is empty
        # https://hvac.readthedocs.io/en/stable/usage/auth_methods/kubernetes.html
        #hvac_client = hvac.Client(url=url, verify=certificate_path)
        #f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
        #jwt = f.read()
        ####VAULT_TOKEN=$(vault write -field=token  auth/kubernetes/login role="${VAULT_ROLE}" jwt="${JWT}")
        #Kubernetes(hvac_client.adapter).login(role=role, jwt=jwt)

        self.logger.info(f"Connecting to Vault API {self.vault_addr}")
        self.hvac_client = hvac.Client(url=self.vault_addr)
        self.hvac_client.token = self.vault_token

        assert self.hvac_client.is_authenticated()

    def snapshot(self):
        """Create Vault integrated storage (Raft) snapshot.

        The snapshot is returned as binary data and should be redirected to
        a file:
        * https://developer.hashicorp.com/vault/api-docs/system/storage/raft
        * https://hvac.readthedocs.io/en/stable/source/hvac_api_system_backend.html
        """

        with self.hvac_client.sys.take_raft_snapshot() as resp:
            assert resp.ok

            self.logger.info("Raft snapshot status code: %d" % resp.status_code)

            date_str = datetime.datetime.now(datetime.UTC).strftime("%F-%H%M")
            file_name = "vault_%s.snapshot" % (date_str)
            self.logger.info(f"File name: {file_name}")

            # Upload the file
            # * https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html
            try:
                response = self.s3_client.put_object(
                    Body=resp.content,
                    Bucket=self.s3_bucket,
                    Key=file_name,
                )
                self.logger.info("s3 put_object response: %s", response)
            except ClientError as e:
                logging.error(e)

        # Iterate and remove expired snapshots:
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/migrations3.html
        s3 = boto3.resource(service_name='s3',
                            endpoint_url=self.s3_host,
                            aws_access_key_id=self.s3_access_key_id,
                            aws_secret_access_key=self.s3_secret_access_key)
        bucket = s3.Bucket(self.s3_bucket)
        for key in bucket.objects.all():
            self.logger.info(key.key)
            # todo: do the S3_EXPIRE_DAYS magic

        return file_name

if __name__=="__main__":
    VaultSnapshot.snapshot()
