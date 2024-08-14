import requests
import pandas as pd
from bs4 import BeautifulSoup
import argparse
# Set up argument parser
parser = argparse.ArgumentParser(description="Login to Screener.in and download data")
parser.add_argument('--email', required=True, help="Email for Screener.in login")
parser.add_argument('--password', required=True, help="Password for Screener.in login")
parser.add_argument('--file_suffix', required=True, help="Suffix for the output file")
args = parser.parse_args()
email = args.email
password = args.password
file_suffix = args.file_suffix
# Start a session
session = requests.Session()
# Get the login page to retrieve the CSRF token
login_url = "https://www.screener.in/login/?"
login_page = session.get(login_url)
soup = BeautifulSoup(login_page.content, 'html.parser')
# Find the CSRF token in the login form (usually in a hidden input field)
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
# Prepare the login payload
login_payload = {
  'username': email,
  'password': password,
  'csrfmiddlewaretoken': csrf_token
}
# Include the Referer header as required
headers = {
  'Referer': login_url,
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}
# Send the login request
response = session.post(login_url, data=login_payload, headers=headers)
# Check if login was successful
if response.url == "https://www.screener.in/dash/":
   print("Login successful")
   # Now navigate to the Reliance company page
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
       # Save the DataFrame to a CSV file with the specified suffix
       df.to_csv(f'profit_and_loss_{file_suffix}.csv', index=False)
else:
   print("Login failed. Response URL:", response.url)
