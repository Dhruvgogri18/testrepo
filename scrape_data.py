import requests
import pandas as pd
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import argparse
from sqlalchemy import create_engine, Integer
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

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
        table1 = soup.find('section', {'id': 'profit-loss'})
        table = table1.find('table')
        headers = [th.text.strip() or f'Column_{i}' for i, th in enumerate(table.find_all('th'))]
        rows = table.find_all('tr')
        row_data = []
        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [col.text.strip() for col in cols]
            if len(cols) == len(headers):
                row_data.append(cols)
            else:
                print(f"Row data length mismatch: {cols}")
        df = pd.DataFrame(row_data, columns=headers)
        if not df.empty:
            df.columns = ['Narration'] + df.columns[1:].tolist()
        df = pd.melt(df, id_vars=['Narration'], var_name='Year', value_name='Value')
        df = df.sort_values(by=['Narration', 'Year']).reset_index(drop=True)
        print(df.head())
        return df
    else:
        print("Failed to retrieve Reliance data")
        return None

def save_to_mysql(df, db, user, password, host, port):
    engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}")
    try:
        df.to_sql('profit_and_loss', con=engine, if_exists='replace', index=True, index_label='id', dtype={'id': Integer})
        with engine.connect() as connection:
            alter_table_sql = """
                ALTER TABLE profit_and_loss
                ADD PRIMARY KEY (id);
            """
            connection.execute(text(alter_table_sql))
        print("Data saved to MySQL")
    except SQLAlchemyError as e:
        print(f"Error: {e}")
    finally:
        engine.dispose()

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
