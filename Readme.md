# Vault Agent for Raft Integrated Storage Backup (draft)

The problem: [Snapshot automation](https://learn.hashicorp.com/vault/operations/storage-migration-checklist#summary), "No out-of-the-box automation tool" for [Raft storage snapshots](https://www.vaultproject.io/docs/commands/operator/raft)

A suggested solution: The Vault Agent and the snapshot cronjob can be deployed on a remote backup server or on the Vault instances itself.

## Vault Policy

Policy for the snapshot agent (todo TF config):
```bash
echo '
path "sys/storage/raft/snapshot" {
   capabilities = ["read"]
}' | vault policy write snapshot -
```
## AppRole Authentication

Enable AppRole and create the `vault-snap-agent` role (todo TF config):
```bash
vault auth enable approle
vault write auth/approle/role/vault-snap-agent token_ttl=2h token_policies=snapshot
#vault read auth/approle/role/vault-snap-agent
vault read auth/approle/role/vault-snap-agent/role-id -format=json | jq -r .data.role_id # sudo tee vault-host:/etc/vault.d/snap-roleid
vault write -f auth/approle/role/vault-snap-agent/secret-id -format=json | jq -r .data.secret_id # sudo tee vault-host:/etc/vault.d/snap-secretid
```

On all Vault servers (todo automate, this is still manual as of today):
```bash
echo "7581f63b-e36b-e105-0c6d-07c534c916c4" > /etc/vault.d/snap-roleid
echo "91919667-7587-4a69-a4f9-766358b082ac" > /etc/vault.d/snap-secretid
```

## Vault Agent Configuration

Configure the vault agent for the snapshots:
```bash
cat << EOF > /etc/vault.d/vault_snapshot_agent.hcl 
# Vault agent configuration for Raft snapshots

pid_file = "/etc/vault.d/vault-snap-agent.pid"

vault {
  address = "https://$HOSTNAME:8200"
}

auto_auth {
  method {
    # Authenticate with AppRole
    # https://www.vaultproject.io/docs/agent/autoauth/methods/approle
    type      = "approle"

    config = {
      role_id_file_path = "/etc/vault.d/snap-roleid"
      secret_id_file_path = "/etc/vault.d/snap-secretid"
      remove_secret_id_file_after_reading = false
    }
  }

  sink {
    # write Vault token to file
    # https://www.vaultproject.io/docs/agent/autoauth/sinks/file
    type = "file"

    config = {
      # best practice to write the file to a ramdisk (0640)
      # have a look at wrapped token for advanced configuration
      path = "/tmp/vault-snap-agent-token"
    }
  }
}
EOF
```

## Vault Agent Systemd Service

Configure the systemd service for the snapshot agent:
```bash
cat << EOF > /etc/systemd/system/vault-snap-agent.service
[Unit]
Description=Vault Agent
Requires=network-online.target
After=network-online.target

[Service]
Restart=on-failure
ExecStart=/usr/local/bin/vault agent -config /etc/vault.d/vault_snapshot_agent.hcl
ExecReload=/bin/kill -HUP $MAINPID
KillSignal=SIGTERM
User=vault
Group=vault

[Install]
WantedBy=multi-user.target
EOF
```

Start the agent on all Vault servers:
```bash
systemctl daemon-reload
systemctl start vault-snap-agent
```

## Vault Raft Snapshot Cronjob

Create a cronjob or an systemd service/timer unit (matter of preference).

Take hourly snapshots with cron:
```bash
cat << 'EOF' > /etc/cron.hourly/vault
#!/bin/sh
#
# Take Vault Raft integrated storage snapshots on the leader
# See also:
#  - /etc/vault.d/vault_snapshot_agent.hcl
#  - /etc/systemd/system/vault-agent.service

VAULT_TOKEN=$(cat /tmp/vault-snap-agent-token) \
/usr/local/bin/vault operator raft snapshot save "/var/vault/vault-raft_$(date +%F-%H%M).snapshot"
EOF
```

Make the cron script executable:
```bash
chmod +x /etc/cron.hourly/vault
```

Test the script (errors probably in `/var/spool/mail/root`):
```bash
run-parts /etc/cron.hourly/ -v
```

## Verify Backup

List the backups:
```bash
[root@vault1 ~]# ls -l /var/vault/
total 96
drwxr-xr-x. 3 vault bin      38 May 28 12:08 raft
-rw-r--r--. 1 vault bin  131072 May 29 07:03 vault.db
-rw-r--r--. 1 root  root      0 May 29 06:37 vault-raft_2020-05-29-0637.snapshot
-rw-r--r--. 1 root  root  21451 May 29 07:03 vault-raft_2020-05-29-0703.snapshot
```

Todo: `snapshot inspect`?

## Retention
Todo: retention
