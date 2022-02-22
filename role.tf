data "vault_approle_auth_backend_role_id" "role" {
  backend   = "approle"
  role_name = "vault-snap-agent"
}
