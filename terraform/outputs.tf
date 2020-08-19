output "approle_role_id" {
    value = vault_approle_auth_backend_role.role.role_id
}

output "approle_secret_id" {
    value = vault_approle_auth_backend_role_secret_id.secretid
    sensitive   = true
}