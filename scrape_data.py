import requests
import pandas as pd
from bs4 import BeautifulSoup
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Reliance data")
    parser.add_argument('--email', required=True, help='Email for Screener.in')
    parser.add_argument('--password', required=True, help='Password for Screener.in')
    args = parser.parse_args()

    session = login_to_screener(args.email, args.password)
    if session:
        df = scrape_reliance_data(session)
        if df is not None:
            print(df)
            df.to_csv('reliance_profit_and_loss.csv', index=False)
