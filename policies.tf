resource "vault_policy" "snapshot" {
  name = "snapshot"

  policy = <<EOT
path "sys/storage/raft/snapshot" {
  capabilities = ["read"]
}
EOT
}

