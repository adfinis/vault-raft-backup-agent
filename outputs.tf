output "role-id" {
  value = data.vault_approle_auth_backend_role_id.role.role_id
}


output "secret-id" {
  value     = vault_approle_auth_backend_role_secret_id.id
  sensitive = true
}

