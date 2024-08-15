import requests
import pandas as pd
from bs4 import BeautifulSoup
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
        
        # Extract headers and data
        headers = [th.text.strip() for th in table.find_all('th')]
        rows = table.find_all('tr')
        row_data = []
        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [col.text.strip() for col in cols]
            row_data.append(cols)

        # Create a DataFrame and transpose it
        df = pd.DataFrame(row_data, columns=headers).transpose()
        new_header = df.iloc[0]  # first row as header
        df = df[1:]  # take the data less the header row
        df.columns = new_header  # set the header row as the df header
        
        # Reset the index to add it as the 'Date' column
        df = df.reset_index().rename(columns={'index': 'Date'})    

        
        # Print the DataFrame columns for debugging
        print("Transposed DataFrame Columns:", df.columns)
        
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
                    `Date` VARCHAR(255),
                    `Sales` VARCHAR(255),
                    `Expenses` VARCHAR(255),
                    `OperatingProfit` VARCHAR(255),
                    `OPM%` VARCHAR(255),
                    `OtherIncome` VARCHAR(255),
                    `Interest` VARCHAR(255),
                    `Depreciation` VARCHAR(255),
                    `Profitbeforetax` VARCHAR(255),
                    `Tax%` VARCHAR(255),
                    `NetProfit` VARCHAR(255),
                    `EPSinRs` VARCHAR(255)
                );
            """)

        # Strip whitespace from column names
        df.columns = df.columns.str.replace(r'[^a-zA-Z0-9]', '', regex=True)
        print(df.columns)

        df = df.drop(columns=['RawPDF'])

        for index, row in df.iterrows():
            # Debugging output
            print(f"Inserting row {index}: {row.values}")
            
            cursor.execute("""
                INSERT INTO financial_data (
                    `Date`, `Sales`, `Expenses`, `OperatingProfit`, `OPM%`, `OtherIncome`,
                    Interest, Depreciation, `Profitbeforetax`, `Tax%`, `NetProfit`, `EPSinRs`
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                row.get('Date', None),
                row.get('Sales', None),
                row.get('Expenses', None),
                row.get('OperatingProfit', None),
                row.get('OPM', None),
                row.get('OtherIncome', None),
                row.get('Interest', None),
                row.get('Depreciation', None),
                row.get('Profitbeforetax', None),
                row.get('Tax', None),
                row.get('NetProfit', None),
                row.get('EPSinRs', None)
            ))
        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved to MySQL")
    except Error as e:
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
