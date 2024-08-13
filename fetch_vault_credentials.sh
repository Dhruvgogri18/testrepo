# Set Vault environment variables
export VAULT_ADDR='http://192.168.1.51:8200'
export VAULT_TOKEN='test'
# Fetch credentials from Vault
USERNAME=$(vault kv get -field=username secret/myapp)
PASSWORD=$(vault kv get -field=password secret/myapp)
# Export these variables so they can be used in Concourse tasks
export VAULT_USERNAME=$USERNAME
export VAULT_PASSWORD=$PASSWORD
# Optional: Print the fetched credentials (for debugging)
echo "Fetched Username: $VAULT_USERNAME
echo "Fetched Password: $VAULT_PASSWORD