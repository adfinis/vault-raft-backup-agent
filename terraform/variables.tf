variable "snapshot_role_policy_name" {
    type = string
    description = "Name of the policy for the snapshot role"
    default = "snapshot"
}

variable "approle_role_id" {
    type = string
    description = "Name of the role for AppRole"
    default = "vault-snap-agent"
}

variable "approle_role_token_ttl" {
    type = string
    description = "TTL in seconds for snapshot role tokens"
    default = 7200
}

variable "ansible_vault_id" {
    type = string
    description = "Location of the ansible-vault password file relative to this folder"
    default = "../ansible/vault-pass"
}

variable "ansible_variable_dir" {
    type = string
    description = "The relative path to the Ansible variable directory"
    default = "../ansible/roles/vault-raft-backup-agent/vars"
}

variable "ansible_variable_file" {
    type = string
    description = "The name of the Ansible vars file"
    default = "main.yml"
}

variable "ansible_roleid_variable_name" {
    type = string
    description = "The variable name for the roleid"
    default = "vault_raft_bck_role_id"
}

variable "ansible_secretid_variable_name" {
    type = string
    description = "The variable name for the secretid encrypted with ansible-vault"
    default = "vault_raft_bck_secret_id"
}