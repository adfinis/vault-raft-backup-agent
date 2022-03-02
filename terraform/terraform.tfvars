# Ansible Vault password file. The source can be a prompt, a file,
# or a script, depending on how you are storing your vault passwords:
# https://docs.ansible.com/ansible/latest/user_guide/vault.html
ansible_vault_id = "../ansible-vault/vault-pass"

# example: adding the vars to the role path
#ansible_variable_dir = "../ansible/roles/vault-raft-backup-agent/vars"

# example: adding the vars to a file 'main.yml' in folder '../ansible/group_vars/vault/'
#ansible_variable_dir = "../ansible/group_vars/vault/"

# example: adding the vars to a file 'vault.yml' in the folder '../ansible/group_vars/'
ansible_variable_dir = "../ansible/group_vars/"
ansible_variable_file = "vault.yml"
