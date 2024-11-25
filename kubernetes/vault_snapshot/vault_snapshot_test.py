import logging
import boto3
import pytest
import requests_mock
from moto import mock_aws
from freezegun import freeze_time
from datetime import datetime, timedelta

from vault_snapshot import VaultSnapshot

logger = logging.getLogger(__name__)

class TestVaultSnapshots:
    """
    Test Vault snapshot functionality.
    """
    
    @mock_aws
    @requests_mock.Mocker(kw="mock")
    def test_snapshot_with_token(self, **kwargs):
        """
        Test snapshot functionality with Token auth.

        https://docs.getmoto.org/en/latest/docs/getting_started.html#decorator
        """

        bucket_name = "vault-snapshots"
        region_name = "us-east-1"
        conn = boto3.resource("s3", region_name=region_name)
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=bucket_name)

        kwargs['mock'].get("http://127.0.0.1:8200/v1/auth/token/lookup-self", text="mock")
        kwargs['mock'].get("http://127.0.0.1:8200/v1/sys/storage/raft/snapshot", text="blob")
        
        vault_snapshot = VaultSnapshot(
            vault_addr="http://127.0.0.1:8200",
            vault_token="root",
            s3_access_key_id="test",
            s3_secret_access_key="test",
            s3_host=f"https://s3.{region_name}.amazonaws.com",
            s3_bucket=bucket_name
        )
        file_name = vault_snapshot.snapshot()

        s3obj = conn.Object(bucket_name, file_name).get()
        body = s3obj["Body"]

        assert body.read() == b"blob"

    @mock_aws
    @requests_mock.Mocker(kw="mock")
    def test_snapshot_with_jwt(self, **kwargs):
        """
        Test snapshot functionality with JWT auth.
        """

        kwargs['mock'].post("http://127.0.0.1:8200/v1/auth/kubernetes/login", json={
            "auth": {
              "client_token": "root"
            }
        })
        kwargs['mock'].get("http://127.0.0.1:8200/v1/sys/storage/raft/snapshot", text="blob")
        kwargs['mock'].get("http://127.0.0.1:8200/v1/auth/token/lookup-self", text="blob")

        bucket_name = "vault-snapshots"
        region_name = "us-east-1"
        conn = boto3.resource("s3", region_name=region_name)
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=bucket_name)

        vault_snapshot = VaultSnapshot(
            vault_addr="http://127.0.0.1:8200",
            vault_role="default",
            jwt_secret_path="./vault_snapshot/fixtures/jwt",
            s3_access_key_id="test",
            s3_secret_access_key="test",
            s3_host=f"https://s3.{region_name}.amazonaws.com",
            s3_bucket=bucket_name
        )
        file_name = vault_snapshot.snapshot()

        s3obj = conn.Object(bucket_name, file_name).get()
        body = s3obj["Body"]

        assert body.read() == b"blob"

    @mock_aws
    @requests_mock.Mocker(kw="mock")
    def test_snapshot_expiration(self, **kwargs):
        """
        Test snapshot expiration.
        """

        kwargs['mock'].post("http://127.0.0.1:8200/v1/auth/kubernetes/login", json={
            "auth": {
              "client_token": "root"
            }
        })
        kwargs['mock'].get("http://127.0.0.1:8200/v1/sys/storage/raft/snapshot", text="blob")
        kwargs['mock'].get("http://127.0.0.1:8200/v1/auth/token/lookup-self", text="blob")

        bucket_name = "vault-snapshots"
        region_name = "us-east-1"
        s3_host = f"https://s3.{region_name}.amazonaws.com"
        s3_access_key_id = "test"
        s3_secret_access_key = "test"

        s3_client = boto3.client(service_name="s3",
                                 endpoint_url=s3_host,
                                 aws_access_key_id=s3_access_key_id,
                                 aws_secret_access_key=s3_secret_access_key)
        conn = boto3.resource("s3", region_name=region_name)
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=bucket_name )

        vault_snapshot = VaultSnapshot(
            vault_addr="http://127.0.0.1:8200",
            vault_role="default",
            jwt_secret_path="./vault_snapshot/fixtures/jwt",
            s3_access_key_id=s3_access_key_id,
            s3_secret_access_key=s3_secret_access_key,
            s3_host=s3_host,
            s3_bucket=bucket_name,
            # delete snapshots older than 1 day
            s3_expire_days=1
        )

        # Snapshot day before yesterday
        with freeze_time(datetime.today() - timedelta(days=2.5)):
            file_name = vault_snapshot.snapshot()
            s3obj = conn.Object(bucket_name, file_name).get()
            body = s3obj["Body"]
            assert body.read() == b"blob"

        objs = s3_client.list_objects(Bucket=bucket_name)["Contents"]
        assert len(objs) == 1

        # Snapshot yesterday
        with freeze_time(datetime.today() - timedelta(days=1.5)):
            file_name = vault_snapshot.snapshot()
            s3obj = conn.Object(bucket_name, file_name).get()
            body = s3obj["Body"]
            assert body.read() == b"blob"

        objs = s3_client.list_objects(Bucket=bucket_name)["Contents"]
        assert len(objs) == 1

        # Snapshot now
        file_name = vault_snapshot.snapshot()
        s3obj = conn.Object(bucket_name, file_name).get()
        body = s3obj["Body"]
        assert body.read() == b"blob"

        objs = s3_client.list_objects(Bucket=bucket_name)["Contents"]
        assert len(objs) == 1
