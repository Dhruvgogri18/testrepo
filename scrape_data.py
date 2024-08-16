import requests
import pandas as pd
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error
import argparse

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
       # Extract headers and data
       headers = [th.text.strip() or f'Column_{i}' for i, th in enumerate(table.find_all('th'))]
       rows = table.find_all('tr')
       # Print headers for debugging
       print("Extracted Headers:", headers)
       row_data = []
       for row in rows[1:]:
           cols = row.find_all('td')
           cols = [col.text.strip() for col in cols]
           # Check if row data length matches header length
           if len(cols) == len(headers):
               row_data.append(cols)
           else:
               print(f"Row data length mismatch: {cols}")
       # Create a DataFrame with sanitized headers
       df = pd.DataFrame(row_data, columns=headers)
       # Rename the first column to 'Narration'
       if not df.empty:
           df.columns = ['Narration'] + df.columns[1:].tolist()
       # Drop the index column if it exists
       df = df.reset_index(drop=True)
       # Print the DataFrame columns and the first few rows for debugging
       print(df.head())
       return df
   else:
       print("Failed to retrieve Reliance data")
       return None

def save_to_mysql(df, db, user, password, host, port):
   # Create an SQLAlchemy engine
   engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}")
   try:
       df.to_sql('financial_data', con=engine, if_exists='replace', index=False)
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
