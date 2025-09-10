# OpenBao Raft Backup Agent - Ansible Configuration

This directory contains Ansible instructions to deploy the Raft Backup Agent. The tasks of the role `bao-raft-backup-agent` are derived from the [manual configurations for Bare Metal/VMs](../docs/vm-configuration.md)).

Note that the playbook will only save the snapshot to a configured directory. If you want to automatically sync those to an S3 bucket, it will need to be configured on top.

It can be deployed directly on the OpenBao nodes or on a dedicated machine.

## Ansible Variables

All variables of the role are documented in the file [`main.yml`](./roles/bao-raft-backup-agent/defaults/main.yml).

The role `bao-raft-backup-agent` assumes that the roleid and secretid are defined. The backup agent and the backup job use these variables to authenticate against the OpenBao:

* `bao_raft_bck_role_id`: The AppRole roleid
* `bao_raft_bck_secret_id`: The AppRole secretid

Note that the **secretid is removed by default**. Set the variable `remove_secret_id_file_after_reading: no` to alter this behavior.

## Usage

### Role Usage / Playbook
An example playbook is provided in the file [`playbook.yml`](./playbook.yml)

```bash
# run the playbook with a custom inventory (not included in this repo)
$ ansible-playbook playbook.yml -i inventory
```

### Check Snapshot Job Status

```bash
$ systemctl list-timers
```

## Limitations
The Ansible role comes with the following limitations:

* Does not configure a cron job, only a systemd timer/service pair
* Does not automatically [install the OpenBao binary](https://openbao.org/docs/install/)
* Does not automatically configure sending snapshot to S3
