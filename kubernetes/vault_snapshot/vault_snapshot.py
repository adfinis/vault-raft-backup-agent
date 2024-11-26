#!/usr/bin/env python

import logging
import boto3
from botocore.exceptions import ClientError
import hvac
import os
from pathlib import Path
from datetime import UTC, datetime, timedelta

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
            self.vault_addr = kwargs["vault_addr"]
        elif "VAULT_ADDR" in os.environ:
            self.vault_addr = os.environ["VAULT_ADDR"]
        else:
            raise NameError("VAULT_ADDR undefined")

        if "vault_skip_verify" in kwargs:
            self.verify = False
        elif "VAULT_SKIP_VERIFY" in os.environ:
            self.verify = False
        else:
            self.verify = True

        if "vault_token" in kwargs:
            self.vault_token = kwargs["vault_token"]
        elif "VAULT_TOKEN" in os.environ:
            self.vault_token = os.environ["VAULT_TOKEN"]
        elif "vault_role" in kwargs:
            self.vault_role = kwargs["vault_role"]
        elif "VAULT_ROLE" in os.environ:
            self.vault_role = os.environ["VAULT_ROLE"]
        else:
            raise NameError("No VAULT_TOKEN or VAULT_ROLE")

        if "s3_access_key_id" in kwargs:
            self.s3_access_key_id = kwargs["s3_access_key_id"]
        elif "AWS_ACCESS_KEY_ID" in os.environ:
            self.s3_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        else:
            raise NameError("AWS_ACCESS_KEY_ID undefined")

        if "s3_secret_access_key" in kwargs:
            self.s3_secret_access_key = kwargs["s3_secret_access_key"]
        elif "AWS_SECRET_ACCESS_KEY" in os.environ:
            self.s3_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        else:
            raise NameError("AWS_SECRET_ACCESS_KEY undefined")

        if "s3_host" in kwargs:
            self.s3_host = kwargs["s3_host"]
        elif "S3_HOST" in os.environ:
            self.s3_host = os.environ["S3_HOST"]
        else:
            raise NameError("S3_HOST undefined")

        if "s3_bucket" in kwargs:
            self.s3_bucket = kwargs["s3_bucket"]
        elif "S3_BUCKET" in os.environ:
            self.s3_bucket = os.environ["S3_BUCKET"]
        else:
            raise NameError("S3_BUCKET undefined")

        if "s3_expire_days" in kwargs:
            self.s3_expire_days = kwargs["s3_expire_days"]
        elif "S3_EXPIRE_DAYS" in os.environ:
            self.s3_expire_days = os.environ["S3_EXPIRE_DAYS"]
        else:
            self.s3_expire_days = -1

        if "jwt_secret_path" in kwargs:
            self.jwt_secret_path = kwargs["jwt_secret_path"]
        elif "JWT_SECRET_PATH" in os.environ:
            self.s3_bucket = os.environ["JWT_SECRET_PATH"]
        else:
            # default Kubernetes serviceaccount JWT secret path
            self.jwt_secret_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"

        # Boto S3 client
        # * https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
        self.s3_client = boto3.client(service_name="s3",
                         endpoint_url=self.s3_host,
                         aws_access_key_id=self.s3_access_key_id,
                         aws_secret_access_key=self.s3_secret_access_key)

        self.logger.info(f"Connecting to Vault API {self.vault_addr}")
        self.hvac_client = hvac.Client(url=self.vault_addr,
                                       verify=self.verify)

        # try setting VAULT_TOKEN if exists
        if hasattr(self, "vault_token") and len(self.vault_token) > 0:
            self.hvac_client.token = self.vault_token
        elif Path(self.jwt_secret_path).exists():
            f = open(self.jwt_secret_path)

            # Authenticate with Kubernetes ServiceAccount if vault_token is empty
            # https://hvac.readthedocs.io/en/stable/usage/auth_methods/kubernetes.html
            login_resp = hvac.api.auth_methods.Kubernetes(self.hvac_client.adapter).login(
                    role=self.vault_role,
                    jwt=f.read()
            )
            self.hvac_client.token = login_resp["auth"]["client_token"]
        else:
            raise Exception("Unable to authenticate with VAULT_TOKEN or JWT")

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

            date_str = datetime.now(UTC).strftime("%F-%H%M")
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
        s3 = boto3.resource(service_name="s3",
                            endpoint_url=self.s3_host,
                            aws_access_key_id=self.s3_access_key_id,
                            aws_secret_access_key=self.s3_secret_access_key)
        objs = self.s3_client.list_objects(Bucket=self.s3_bucket)["Contents"]
        #self.logger.info(objs)

        for o in objs:
            self.logger.info(f"LastModified: {o['LastModified']}")
            # expire keys when older than S3_EXPIRE_DAYS
            if int(self.s3_expire_days) >= 0:
                if o["LastModified"] <= datetime.now(UTC) - timedelta(days=int(self.s3_expire_days)):
                    self.logger.info(f"Deleting expired snapshot {o['Key']}")
                    s3.Object(self.s3_bucket, o["Key"]).delete()

        return file_name

if __name__=="__main__":
    vault_snapshot = VaultSnapshot()
    vault_snapshot.snapshot()
