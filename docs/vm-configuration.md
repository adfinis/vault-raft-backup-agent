# Installation and configuration on bare metal server/VMs

For Bare Metal/VMs, we rely on the [AppRole authentication method](https://openbao.org/docs/auth/approle/).

Essentially, we configure an [OpenBao Agent](https://openbao.org/docs/agent-and-proxy/agent/) that provides authentication to the OpenBao server. The snapshot itself are taken at regular interval via systemd service and timer.

## Configuration of AppRole Authentication

#### OpenBao Policy

Policy for the snapshot agent:
```bash
echo '
path "sys/storage/raft/snapshot" {
   capabilities = ["read"]
}' | bao policy write snapshot -
```

#### AppRole Authentication

These manual steps for AppRole authentication are automated in the [./terraform](./terraform) code.

Enable AppRole and create the `bao-snap-agent` role:
```bash
bao auth enable approle
bao write auth/approle/role/bao-snap-agent token_ttl=2h token_policies=snapshot
bao read auth/approle/role/bao-snap-agent/role-id -format=json | jq -r .data.role_id 
bao write -f auth/approle/role/bao-snap-agent/secret-id -format=json | jq -r .data.secret_id
```

On all OpenBao servers:
```bash
echo "<role_id>" > /etc/bao.d/snap-secretid
echo "<secretd_id>" > /etc/bao.d/snap-roleid
chmod 0640 /etc/bao.d/snap-{roleid,secretid}
chown bao:bao /etc/bao.d/snap-{roleid,secretid}
```

## Deployment and Configuration

The OpenBao agent and systemd timer can also be automatically deployed using the [ansible role](/ansible)

### Manual steps

Configure the OpenBao Agent for the snapshots:
```bash
cat << EOF > /etc/bao.d/bao_snapshot_agent.hcl
# OpenBao agent configuration for Raft snapshots

vault {
  address = "https://$HOSTNAME:8200"
}

api_proxy {
  # Authenticate all requests automatically with the auto_auth token
  # https://openbao.org/docs/agent-and-proxy/agent/apiproxy/
  use_auto_auth_token = true
}

listener "unix" {
  # Expose OpenBao Agent API seperately
  # https://openbao.org/docs/agent-and-proxy/agent/caching/#configuration-listener
  address = "/etc/vault.d/agent.sock"
  tls_disable = true
}

auto_auth {
  method {
    # Authenticate with AppRole
    # https://openbao.org/docs/agent-and-proxy/autoauth/methods/approle/
    type      = "approle"

    config = {
      role_id_file_path = "/etc/bao.d/snap-roleid"
      secret_id_file_path = "/etc/bao.d/snap-secretid"
      remove_secret_id_file_after_reading = false
    }
  }
}
EOF
```

#### Vault Agent Systemd Service

Configure the systemd service for the snapshot agent:
```bash
cat << EOF > /etc/systemd/system/bao-snap-agent.service
[Unit]
Description=OpenBao Snapshot Agent
Requires=network-online.target
After=network-online.target
ConditionFileNotEmpty=/etc/bao.d/bao.hcl

[Service]
Restart=on-failure
ExecStart=/usr/local/bin/bao agent -config=/etc/bao.d/bao_snapshot_agent.hcl
ExecReload=/bin/kill -HUP $MAINPID
KillSignal=SIGINT
User=bao
Group=bao
RuntimeDirectoryMode=0750
RuntimeDirectory=bao-snap-agent

[Install]
WantedBy=multi-user.target
EOF
```

Start the agent on all OpenBao servers:
```bash
systemctl daemon-reload
systemctl enable --now bao-snap-agent
```

#### OpenBao Raft Snapshot Cronjob

Create a cronjob or an systemd service/timer unit (matter of preference).

Create a script to execute the snapshot:
```bash
cat << 'EOF' > /usr/local/bin/bao-snapshot
#!/bin/sh
#
# Take OpenBao Raft integrated storage snapshots on the leader
# See also:
#  - /etc/bao.d/bao_snapshot_agent.hcl
#  - /etc/systemd/system/bao-agent.service

BAO_ADDR="BAO_ADDR=unix:///etc/bao.d/agent.sock" \
/usr/local/bin/bao operator raft snapshot save "/opt/bao/snapshots/bao-raft_$(date +%F-%H%M).snapshot"
EOF
```

Make the script executable:
```bash
chmod +x /usr/local/bin/bao-snapshot
```

Take hourly snapshots with cron, make sure the cronjobs are evenly spaced out every hour (e.g. server1: Minute 0, server2: Minute 20, server3: Minute 40):
```bash
echo "0 * * * * root /usr/local/bin/bao-snapshot" >> /etc/crontab
```

Test the script (errors probably in `/var/spool/mail/root`):
```bash
vault-snapshot
```

## Sync with remote storage
### S3

Install s3cmd: https://github.com/s3tools/s3cmd/releases

Configure s3cmd:
```bash
s3cmd --configure
s3cmd mb s3://raft-snapshots
```

Add s3cmd sync to `bao-snapshot`:
```bash
echo "/usr/bin/s3cmd sync /opt/bao/snapshots/* s3://raft-snapshots" >> /usr/local/bin/bao-snapshot
```

## Retention

For an retention of 7 days (locally, not on the remote storage) you need to add the following to the `bao-snapshot` script:
```
find /opt/bao/snapshots/* -mtime +7 -exec rm {} \;
```

To change the retention you can change the `+7` from the mtime parameter.
