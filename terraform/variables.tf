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

variable "ansible_vault_id" {
    type = string
    description = "Location of the ansible-vault password file relative to this folder"
    default = "../ansible/vault-pass"
}

variable "ansible_play_dir" {
    type = string
    description = "The relative path to the Ansible playbook directory"
    default = "../ansible"
}

variable "ansible_vars_file_secret_id" {
    type = string
    description = "The name of the Ansible vars file that holds the secret id"
    default = "raft-backup-secretid.yml"
}

variable "ansible_vars_file_role_id" {
    type = string
    description = "The name of the Ansible vars file that holds the role id"
    default = "raft-backup-roleid.yml"
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