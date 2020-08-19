provider "vault" {}

# Data source to retrieve AppRole role id
data "vault_approle_auth_backend_role_id" "role" {
  backend   = vault_auth_backend.approle.path
  role_name = var.approle_role_id
}

# Policy for creating Raft snapshots
data "vault_policy_document" "raft" {
  rule {
    path         = "sys/storage/raft/snapshot"
    capabilities = ["read"]
    description  = "create raft storage snapshots"
  }
}
resource "vault_policy" "raft" {
  name   = var.snapshot_role_policy_name
  policy = data.vault_policy_document.raft.hcl
}

# AppRole backend
resource "vault_auth_backend" "approle" {
  type = "approle"
}

# AppRole backend role
resource "vault_approle_auth_backend_role" "role" {
  backend   = vault_auth_backend.approle.path
  role_name = var.approle_role_id
  token_policies  = ["${var.snapshot_role_policy_name}"]
  token_ttl = var.approle_role_token_ttl
}

# AppRole secretid
resource "vault_approle_auth_backend_role_secret_id" "secretid" {
  backend   = vault_auth_backend.approle.path
  role_name = vault_approle_auth_backend_role.role.role_name
}

# Update the AppRole roleid in the Ansible vars
resource "null_resource" "update_appid" {
  triggers = {
      # when the AppRole role changes
      key_id   = vault_approle_auth_backend_role.role.id
  }
  provisioner "local-exec" {
      # Prepare directory for Ansible play variables
      # Play vars can be overridden with group or host vars, see also:
      # https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable
      command = "mkdir -p '${var.ansible_variable_dir}'"
  }
  provisioner "local-exec" {
      # Write the new roleid to the Ansible vars file
      command = "echo -n \"${var.ansible_roleid_variable_name}: '${data.vault_approle_auth_backend_role_id.role.role_id}'\" >> \"${var.ansible_variable_dir}/${var.ansible_variable_file}\""
  }
}

# Update the AppRole secretid in the Ansible vars
resource "null_resource" "update_secretid" {
  triggers = {
      # when the secretid changes
      key_id   = vault_approle_auth_backend_role_secret_id.secretid.id
  }
  provisioner "local-exec" {
      command = "mkdir -p '${var.ansible_variable_dir}'"
  }
  provisioner "local-exec" {
      # Encrypt the secretid and write to the Ansible vars file
      command = <<EOT
  echo -n "${vault_approle_auth_backend_role_secret_id.secretid.secret_id}" \
    | ansible-vault encrypt_string --vault-id "${var.ansible_vault_id}" --stdin-name "${var.ansible_secretid_variable_name}" \
    >> "${var.ansible_variable_dir}/${var.ansible_variable_file}"
  EOT
  }
}