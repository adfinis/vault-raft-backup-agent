# Vault Raft Backup Agent - Terraform Configuration

This directory contains Terraform instructions that prepare the Vault for usage with the Raft Backup Agent. The Terraform code:
1. Adds a snapshot policy
2. Configures AppRole authentication
3. Adds the AppRole role for snapshots with the snapshot policy from (1)
4. Retrieves roleid and secretid and updates the values in Ansible vars

These steps are derived from the [description of the backup approach](../Readme.md).

## Terraform Inputs: Ansible Variables

The Terraform configuration assumes that the following Ansible var files should atomatically updated in step (4) above:

| Description | Terraform Variable forming the Ansible Path | Variable Default Value |
| --- | --- | --- |
| The path of the roleid Ansible variable | `${ansible_play_dir}/vars/${ansible_vars_file_role_id}` | `../ansible/raft-backup-roleid.yml` | 
| The path of the secretid Ansible variable |`${ansible_play_dir}/vars/${ansible_vars_file_secret_id}` | `../ansible/raft-backup-secretid.yml` |
| The location of the password file for Ansible Vault | `ansible_vault_id` | `../ansible/vault-pass` |

Notes:

* The secretid (sensitive) is encrypted with the [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html) password defined in `ansible_vault_id`.
* Any other variable in the file [`variables.tf`](./variables.tf) is used "internally", i.e., has no effect on the outputs of the module which could be processed by Ansible afterwards.

## Usage

```bash
# copy and adapt the variables
$ cp terraform.tfvars{.example,}

# configure access credentials, see also
# https://www.terraform.io/docs/providers/vault/index.html
$ export VAULT_ADDR=http://127.0.0.1:8200
$ export VAULT_TOKEN=root

# initialize and apply the Vault configuration
$ terraform init
$ terraform plan
$ terraform apply
```

## Terraform Outputs: AppRole `roleid` and `secretid`

To reveal the `roleid` and (sensitive) `secretid` of the current configuration use:
```bash
$ terraform output approle_role_id
$ terraform output approle_secret_id
```

## Import Existing AppRole Configuration

After initialization, existing AppRole configuration can be imported into the terraform state with:

```bash
# Adjust $APPROLE_PATH to match the existing Vault configuration (remote).
# Have a look at `vault auth list` to retrieve the path of an exisiting AppRole backend
APPROLE_PATH=custom_approle
terraform import vault_auth_backend.approle $APPROLE_PATH

# Verify the import
$ terraform state list
vault_auth_backend.approle

# Execute a plan to see the dif
$ terraform plan -target=vault_auth_backend.approle
  # vault_auth_backend.approle will be updated in-place
  ~ resource "vault_auth_backend" "approle" {
        accessor                  = "auth_approle_e53052a8"
        default_lease_ttl_seconds = 0
        id                        = "custom_approle"
        local                     = false
        max_lease_ttl_seconds     = 0
        path                      = "custom_approle"
      + tune                      = (known after apply)
        type                      = "approle"
    }

# Copy/paste the diff to the `terraform.tf` file,
# to replace the existing backend configuration
#
# ./terraform.tf excerpt
#
# AppRole backend
resource "vault_auth_backend" "approle" {
  local                     = false
  path                      = "custom_approle"
  tune                      = []
  type                      = "approle"
}

# Update the ./terraform.tf file until the plan on the resource
# shows that the existing config file matches the current remote state
terraform import vault_auth_backend.approle $APPROLE_PATH

# Proceed similarly with any other resources for import, e.g., the AppRole role
APPROLE_PATH=auth/approle/role/existing-snapshot-approle-role
terraform import vault_approle_auth_backend_role.example $PATH
```

See also: https://www.terraform.io/docs/providers/vault/r/approle_auth_backend_role.html#import

For importing other resources, have a look at the import instructions of the respective resources upstream:

https://www.terraform.io/docs/providers/vault