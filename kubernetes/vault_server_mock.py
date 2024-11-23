import subprocess

VAULT_PORT = 8200
VAULT_CONFIG = "./vault_config.hcl"
VAULT_TOKEN = "root"
VAULT_DATA_DIR = "./vault_data"

class VaultServer():
    def reset_data(self, dir: str = VAULT_DATA_DIR):
        """
        Reset Vault server mock raft data directory.
        """

        subprocess.run(f"rm -rf {dir}/*", shell=True)
        print(f"Vault data dir reset: {dir}")
        
    def run(self, port: int = VAULT_PORT, config: str = VAULT_CONFIG,
            token: str = VAULT_TOKEN):
        """
        Start the Vault server mock with data dir and config.
        """

        command = f"$(which vault) server -dev -dev-root-token-id={token} -config={config}"
        self.proc = subprocess.Popen(command, shell=True)

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
