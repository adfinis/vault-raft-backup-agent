import pytest
import boto3
import hvac
from moto import mock_aws
from unittest.mock import patch, create_autospec

from vault_snapshot import VaultSnapshot
from vault_server_mock import VaultServer

class TestVaultSnapshots:
    """
    Test Vault snapshot functionality.
    """

    @pytest.fixture
    def mock_vault_server(self):
        """
        Run a Vault server mock.
        """
        self.mock = VaultServer()
        self.mock.reset_data()
        # run mock
        self.mock.run()
        # return process status, 'None' means process is still running
        yield self.mock.status()
        # when tests are done, teardown the Vault server
        self.mock.stop()
    
    @mock_aws
    def test_snapshot(self, mock_vault_server):
        """
        Test snapshot functionality using boto3 and moto.

        https://docs.getmoto.org/en/latest/docs/getting_started.html#decorator
        """

        print(f"The current Vault server mock process status is: {mock_vault_server}")

        bucket_name = "vault-snapshots"
        region_name = "us-east-1"
        conn = boto3.resource("s3", region_name=region_name)
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=bucket_name)
    
        vault_snapshot = VaultSnapshot(
            vault_addr="http://127.0.0.1:8200",
            vault_token="root",
            s3_access_key_id="test",
            s3_secret_access_key="test",
            s3_host=f"https://s3.{region_name}.amazonaws.com",
            s3_bucket=bucket_name
        )
        file_name = vault_snapshot.snapshot()

        body = conn.Object(bucket_name,
                           file_name).get()#["Body"].read()#.decode("utf-8")

        #print(body)
    
        #assert body == "is awesome" 
