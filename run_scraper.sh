pip install -r requirements.txt
echo "$EMAIL"
echo "$PASSWORD"
python scrape_data_50.py --email "$EMAIL" --password "$PASSWORD" --db "connect_test" --user "root" --pw "root" --host "192.168.3.19" --port "3306" --csv "ind_nifty50list.csv"
