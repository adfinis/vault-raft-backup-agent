import subprocess
import hvac
import requests

VAULT_PORT = 8200
VAULT_ADDR = f"http://127.0.0.1:{VAULT_PORT}"
VAULT_CONFIG = "./vault_config.hcl"
VAULT_TOKEN = "root"
VAULT_DATA_DIR = "./vault_data"

class VaultServer():
    """
    Vault server mock.

    Runs on http://127.0.0.1:8200 and can be initialized with Vault token as
    first argument.
    """

    def __init__(self, *args):
        self.token = VAULT_TOKEN
        if len(args) >= 1:
            self.token = args[0]
        else:
            self.token = VAULT_TOKEN

        self.headers = {"X-Vault-Token": self.token}

    def reset_data(self, dir: str = VAULT_DATA_DIR):
        """
        Reset Vault server mock raft data directory.
        """

        subprocess.run(f"rm -rf {dir}/*", shell=True)
        print(f"Vault data dir reset: {dir}")
        
    def run(self, port: int = VAULT_PORT, config: str = VAULT_CONFIG):
        """
        Start the Vault server mock with data dir and config.
        """

        command = f"$(which vault) server -dev -dev-root-token-id={self.token} -config={config}"
        self.proc = subprocess.Popen(command, shell=True)

    def init_hvac_client(self):
        """
        Initialize hvac client as root on the mock server
        """

        self.hvac_client = hvac.Client(url=VAULT_ADDR)
        self.hvac_client.token = self.token

        assert self.hvac_client.is_authenticated()

    def setup_kubernetes_auth(self):
        """"
        Configure a Kubernetes auth backend for testing purposes.
        """

        self.hvac_client.sys.enable_auth_method(
                method_type="kubernetes",
                path="kubernetes",
        )

        #data = {
        #  "kubernetes_host": "127.0.0.1",
        #}
        # configure Kubernetes auth backend

        data = {
          "bound_service_account_names": "default",
          "bound_service_account_namespaces": "*",
          "policies": ["root"],
        }

        # add login role
        # https://developer.hashicorp.com/vault/api-docs/auth/kubernetes#create-update-role
        ret = requests.post(f"{VAULT_ADDR}/v1/auth/kubernetes/role/default",
                            json=data,
                            headers=self.headers)

    def status(self):
        """
        Return Vault server mock status.

        A None value indicates that the process hadn’t yet terminated at the
        time of the last method call:
        * https://docs.python.org/3/library/subprocess.html#subprocess.Popen.returncode
        """
        return self.proc.returncode

    def stop(self):
        """
        Kill Vault server mock process.
        """

        self.proc.kill()
        self.proc.wait()
        print(f"Process returned with return code: {self.proc.returncode}")
