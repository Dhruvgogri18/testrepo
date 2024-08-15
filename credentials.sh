export VAULT_ADDR='http://192.168.0.108:8200'
export VAULT_TOKEN='root'
vault kv get -field=login_email secret/data/screener > credentials/email.txt
vault kv get -field=login_password secret/data/screener > credentials/password.txt
