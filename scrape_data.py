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
        
        # Create a table with additional columns if necessary
        cursor.execute("DROP TABLE IF EXISTS profit_and_loss;")
        cursor.execute("""
            CREATE TABLE profit_and_loss (
                date_period VARCHAR(20),
                sales DECIMAL(20, 2),
                expenses DECIMAL(20, 2),
                operating_profit DECIMAL(20, 2),
                opm_percentage DECIMAL(5, 2),
                other_income DECIMAL(20, 2),
                interest DECIMAL(20, 2),
                depreciation DECIMAL(20, 2),
                profit_before_tax DECIMAL(20, 2),
                tax_percentage DECIMAL(5, 2),
                net_profit DECIMAL(20, 2),
                eps DECIMAL(20, 2)
            );
        """)
        
        for index, row in df.iterrows():
            # Convert percentage strings to decimal values
            opm_percentage = float(row['OPM %'].strip('%')) / 100 if 'OPM %' in row and row['OPM %'] != '-' else None
            tax_percentage = float(row['Tax %'].strip('%')) / 100 if 'Tax %' in row and row['Tax %'] != '-' else None

            cursor.execute("""
                INSERT INTO profit_and_loss (date_period, sales, expenses, operating_profit, opm_percentage, other_income, interest, depreciation, profit_before_tax, tax_percentage, net_profit, eps)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                index,  # or some date/period string
                row.get('SalesÂ+', 0).replace(',', '').replace('Â', ''), 
                row.get('ExpensesÂ+', 0).replace(',', '').replace('Â', ''), 
                row.get('Operating Profit', 0).replace(',', '').replace('Â', ''), 
                opm_percentage,
                row.get('Other IncomeÂ+', 0).replace(',', '').replace('Â', ''), 
                row.get('Interest', 0).replace(',', '').replace('Â', ''), 
                row.get('Depreciation', 0).replace(',', '').replace('Â', ''), 
                row.get('Profit before tax', 0).replace(',', '').replace('Â', ''), 
                tax_percentage,
                row.get('Net ProfitÂ+', 0).replace(',', '').replace('Â', ''), 
                row.get('EPS in Rs', 0).replace(',', '').replace('Â', '')
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
