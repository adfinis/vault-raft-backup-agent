resource "vault_auth_backend" "approle" {
  type = "approle"
}

resource "vault_approle_auth_backend_role" "vault-snap-agent" {
  backend        = vault_auth_backend.approle.path
  role_name      = "vault-snap-agent"
  token_policies = ["snapshot"]         
  token_ttl              = "7200" # 2 hours
}

resource "vault_approle_auth_backend_role_secret_id" "id" {
  backend   = vault_auth_backend.approle.path
  role_name = vault_approle_auth_backend_role.vault-snap-agent.role_name
}

