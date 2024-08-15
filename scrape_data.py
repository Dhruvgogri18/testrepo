import requests
import pandas as pd
from bs4 import BeautifulSoup
import psycopg2
import argparse
import mysql.connector
from mysql.connector import Error

def login_to_screener(email, password):
    session = requests.Session()
    login_url = "https://www.screener.in/login/?"
    login_page = session.get(login_url)
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
    login_payload = {
        'username': email,
        'password': password,
        'csrfmiddlewaretoken': csrf_token
    }
    headers = {
        'Referer': login_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }
    response = session.post(login_url, data=login_payload, headers=headers)
    if response.url == "https://www.screener.in/dash/":
        print("Login successful")
        return session
    else:
        print("Login failed")
        return None

def scrape_reliance_data(session):
    search_url = "https://www.screener.in/company/RELIANCE/consolidated/"
    search_response = session.get(search_url)
    if search_response.status_code == 200:
        print("Reliance data retrieved successfully")
        soup = BeautifulSoup(search_response.content, 'html.parser')
        table = soup.find('table', {'class': 'data-table responsive-text-nowrap'})
        headers = [th.text.strip() for th in table.find_all('th')]
        rows = table.find_all('tr')
        row_data = []
        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [col.text.strip() for col in cols]
            row_data.append(cols)
        df = pd.DataFrame(row_data, columns=headers)
        print(df)
        return df
    else:
        print("Failed to retrieve Reliance data")
        return None

def save_to_mysql(df, db, user, password, host, port):
    try:
        conn = mysql.connector.connect(
            database=db,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS financial_data;")
        cursor.execute("""
            CREATE TABLE financial_data (
                date_period VARCHAR(255),
                sales FLOAT,
                expenses FLOAT,
                operating_profit FLOAT,
                opm_percent FLOAT,
                other_income FLOAT,
                interest FLOAT,
                depreciation FLOAT,
                profit_before_tax FLOAT,
                tax_percent FLOAT,
                net_profit FLOAT,
                eps FLOAT
            );
        """)
        for index, row in df.iterrows():
            cursor.execute("""
                INSERT INTO financial_data (
                    date_period, sales, expenses, operating_profit, opm_percent, other_income,
                    interest, depreciation, profit_before_tax, tax_percent, net_profit, eps
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                row.get('date_period'),
                float(row.get('Sales +', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('expenses', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('operating_profit', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('OPM %', '0').replace('%', '').replace('Â', '') or 0),
                float(row.get('other_income', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('interest', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('depreciation', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('profit_before_tax', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('Tax %', '0').replace('%', '').replace('Â', '') or 0),
                float(row.get('net_profit', '0').replace(',', '').replace('Â', '') or 0),
                float(row.get('EPS in Rs', '0').replace(',', '').replace('Â', '') or 0)
            ))
        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved to MySQL")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and store Reliance data")
    parser.add_argument('--email', required=True, help='Email for Screener.in')
    parser.add_argument('--password', required=True, help='Password for Screener.in')
    parser.add_argument('--db', required=True, help='MySQL database name')
    parser.add_argument('--user', required=True, help='MySQL username')
    parser.add_argument('--pw', required=True, help='MySQL password')
    parser.add_argument('--host', required=True, help='MySQL host')
    parser.add_argument('--port', required=True, help='MySQL port')
    args = parser.parse_args()

    session = login_to_screener(args.email, args.password)
    if session:
        df = scrape_reliance_data(session)
        if df is not None:
            save_to_mysql(df, args.db, args.user, args.pw, args.host, args.port)
