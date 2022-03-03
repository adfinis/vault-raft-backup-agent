# Vault Agent for Raft Integrated Storage Backup (draft)

The problem: [Snapshot automation](https://learn.hashicorp.com/vault/operations/storage-migration-checklist#summary), "No out-of-the-box automation tool" for [Raft storage snapshots](https://www.vaultproject.io/docs/commands/operator/raft)

A suggested solution: The Vault Agent and the snapshot cronjob can be deployed on a remote backup server or on the Vault instances itself.

## Prerequisites

The automation code (Ansible playbook and Terraform) does not automatically [install the Vault binary](https://learn.hashicorp.com/tutorials/vault/getting-started-install).

## Vault Policy

Policy for the snapshot agent:
```bash
echo '
path "sys/storage/raft/snapshot" {
   capabilities = ["read"]
}' | vault policy write snapshot -
```

This policy is included in the [./terraform](./terraform) code.

## AppRole Authentication

These manual steps for AppRole authentication are automated in the [./terraform](./terraform) code.

Enable AppRole and create the `vault-snap-agent` role:
```bash
vault auth enable approle
vault write auth/approle/role/vault-snap-agent token_ttl=2h token_policies=snapshot
#vault read auth/approle/role/vault-snap-agent
vault read auth/approle/role/vault-snap-agent/role-id -format=json | jq -r .data.role_id # sudo tee vault-host:/etc/vault.d/snap-roleid
vault write -f auth/approle/role/vault-snap-agent/secret-id -format=json | jq -r .data.secret_id # sudo tee vault-host:/etc/vault.d/snap-secretid
```

On all Vault servers:
```bash
echo "7581f63b-e36b-e105-0c6d-07c534c916c4" > /etc/vault.d/snap-roleid
echo "91919667-7587-4a69-a4f9-766358b082ac" > /etc/vault.d/snap-secretid
chmod 0640 /etc/vault.d/snap-{roleid,secretid}
chown vault:vault /etc/vault.d/snap-{roleid,secretid}
```

## Vault Agent Configuration

Configure the vault agent for the snapshots:
```bash
cat << EOF > /etc/vault.d/vault_snapshot_agent.hcl
# Vault agent configuration for Raft snapshots

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
      path = "/run/vault-snap-agent/token"
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
Description=Vault Snapshot Agent
Requires=network-online.target
After=network-online.target
ConditionFileNotEmpty=/etc/vault.d/vault.hcl

[Service]
Restart=on-failure
ExecStart=/usr/local/bin/vault agent -config=/etc/vault.d/vault_snapshot_agent.hcl
ExecReload=/bin/kill -HUP $MAINPID
KillSignal=SIGINT
User=vault
Group=vault
RuntimeDirectoryMode=0750
RuntimeDirectory=vault-snap-agent

[Install]
WantedBy=multi-user.target
EOF
```

Start the agent on all Vault servers:
```bash
systemctl daemon-reload
systemctl enable --now vault-snap-agent
```

## Vault Raft Snapshot Cronjob

Create a cronjob or an systemd service/timer unit (matter of preference).

Create a script to execute the snapshot:
```bash
cat << 'EOF' > /usr/local/bin/vault-snapshot
#!/bin/sh
#
# Take Vault Raft integrated storage snapshots on the leader
# See also:
#  - /etc/vault.d/vault_snapshot_agent.hcl
#  - /etc/systemd/system/vault-agent.service

VAULT_TOKEN=$(cat /run/vault-snap-agent/token) VAULT_ADDR="https://$HOSTNAME:8200" \
/usr/local/bin/vault operator raft snapshot save "/opt/vault/snapshots/vault-raft_$(date +%F-%H%M).snapshot"
EOF
```

Make the script executable:
```bash
chmod +x /usr/local/bin/vault-snapshot
```

Take hourly snapshots with cron, make sure the cronjobs are evenly spaced out every hour (e.g. server1: Minute 0, server2: Minute 20, server3: Minute 40):
```bash
echo "0 * * * * root /usr/local/bin/vault-snapshot" >> /etc/crontab
```

Test the script (errors probably in `/var/spool/mail/root`):
```bash
vault-snapshot
```

## Verify Backup

List the backups:
```bash
[root@vault1 ~]# ls -l /opt/vault/snapshots
total 96
-rw-r--r--. 1 root  root      0 May 29 06:37 vault-raft_2020-05-29-0637.snapshot
-rw-r--r--. 1 root  root  21451 May 29 07:03 vault-raft_2020-05-29-0703.snapshot
```

## Sync with remote storage
### S3

Install s3cmd: https://github.com/s3tools/s3cmd/releases

```bash
zypper install python3
ln -s /usr/bin/python3 /usr/bin/python

wget <s3cmd-release-url>
tar xvf s3cmd-x.x.x.tar.gz
cd s3cmd-x.x.x
python setup.py install
```

Configure s3cmd:
```
s3cmd --configure
s3cmd mb s3://raft-snapshots
```

Add s3cmd sync to `vault-snapshot`:
```bash
echo "/usr/bin/s3cmd sync /opt/vault/snapshots/* s3://raft-snapshots" >> /usr/local/bin/vault-snapshot
```

## Retention

For an retention of 7 days (locally, not on the remote storage) you need to add the following to the `vault-snapshot` script:
```
find /opt/vault/snapshots/* -mtime +7 -exec rm {} \;
```

To change the retention you can change the `+7` from the mtime parameter.
