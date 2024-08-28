import requests
import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Integer
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
import time
import numpy as np
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
def scrape_company_data(session, company_symbol, company_id, company_name):
   urls = [
       f"https://www.screener.in/company/{company_symbol}/consolidated/",
       f"https://www.screener.in/company/{company_symbol}/"
   ]
   df, company_df, df_ttm, narration_df = None, None, None, pd.DataFrame(columns=['Narration'])
   for url in urls:
       try:
           search_response = session.get(url)
           if search_response.status_code == 200:
               print(f"Data retrieved successfully from {url}")
               soup = BeautifulSoup(search_response.content, 'html.parser')
               table1 = soup.find('section', {'id': 'profit-loss'})
               if table1:
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
                       if 'TTM' in df.columns:
                           df_ttm = df[['Narration', 'TTM']].copy()
                           df_ttm['TTM'] = df_ttm['TTM'].str.replace(',', '')
                           df_ttm['TTM'] = pd.to_numeric(df_ttm['TTM'], errors='coerce').fillna(0).astype(int)
                           df_ttm = df_ttm.assign(Company_ID=company_id)
                           df_ttm = df_ttm.reset_index(drop=True)
                           company_df = pd.DataFrame({
                               'Company_ID': [company_id],
                               'Company': [company_name]
                           })
                           company_df.reset_index(drop=True)
                           df = df.drop(columns=['TTM'])
                           df = pd.melt(df, id_vars=['Narration'], var_name='Financial_Year', value_name='Value')
                           df = df.merge(df_ttm, on='Narration', how='inner')
                           df['Value'] = df['Value'].str.replace(',', '')
                           df['Value'] = df['Value'].str.replace('%', '')
                           df['Value'] = pd.to_numeric(df['Value'], errors='coerce').fillna(0)
                           df['Company_ID'] = company_id
                           df['Percent_change'] = df.groupby('Narration')['Value'].pct_change() * 100
                           df['Percent_change'] = df['Percent_change'].replace([np.inf, -np.inf], np.nan)
                           df['Percent_change'] = df['Percent_change'].where(pd.notnull(df['Percent_change']), None)
                           df['Percent_change'] = df['Percent_change'].round(2)
                           df = df.sort_values(by=['Narration', 'Financial_Year']).reset_index(drop=True)
                           df = df.drop(columns=['TTM'], errors='ignore')
                           narration_df = pd.DataFrame({
                               'Narration': df['Narration'].unique()
                            })
                           narration_df.reset_index(drop=True)
                           return df, company_df, df_ttm, narration_df
                       else:
                           print("'TTM' column not found in DataFrame")
                           continue
               else:
                   print(f"No data found in table for {company_symbol}")
                   continue
           else:
               print(f"Failed to retrieve data from {url}. Status code: {search_response.status_code}")
               continue
       except Exception as e:
           print(f"Error: {e}")
           continue
   return df, company_df, df_ttm, narration_df

def save_to_mysql(df, company_df, df_ttm, db, user, password, host, port):
    engine = create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{db}")

    try:
        # Append new data to existing tables
        df.to_sql('f', con=engine, if_exists='replace', index=True, index_label='id', dtype={'id': Integer})
        company_df.to_sql('c', con=engine, if_exists='replace', index=True, index_label='id', dtype={'id': Integer})
        df_ttm.to_sql('t', con=engine, if_exists='replace', index=True, index_label='id', dtype={'id': Integer})
        narration_df.to_sql('n', con=engine, if_exists='replace', index=True, index_label='id', dtype={'id': Integer})
 
        with engine.connect() as connection:
            connection.execute(text("UPDATE f JOIN t ON f.Narration = t.Narration and f.Company_id = t.company_id SET f.ttm_id = t.id;"))
            connection.execute(text("UPDATE t JOIN n ON t.Narration = n.Narration SET t.n_id = n.id;"))
            connection.execute(text("UPDATE f JOIN n ON f.Narration = n.Narration SET f.n_id = n.id;"))
            connection.execute(text("ALTER TABLE f DROP COLUMN Narration;"))
            connection.execute(text("ALTER TABLE t DROP COLUMN Narration;"))

            connection.execute(text("ALTER TABLE f ADD PRIMARY KEY (id);"))
            connection.execute(text("ALTER TABLE c ADD PRIMARY KEY (id);"))
            connection.execute(text("ALTER TABLE t ADD PRIMARY KEY (id);"))
            connection.execute(text("ALTER TABLE n ADD PRIMARY KEY (id);"))
 
        print("Data saved to MySQL")
 
    except SQLAlchemyError as e:
        print(f"Error: {e}")
    finally:
       engine.dispose()

def read_company_names_from_csv(file_path):
   try:
       df = pd.read_csv(file_path)
       print("DataFrame loaded from CSV:")
       print(df.head())
       if 'Symbol' in df.columns and 'Company Name' in df.columns:
           company_symbols = df['Symbol'].unique()
           company_names = df['Company Name'].unique()
           print("\nCompany symbols extracted:")
           print(company_symbols)
           print("\nCompany names extracted:")
           print(company_names)
           return company_symbols, company_names
       else:
           print("Required columns not found in the CSV file.")
           return None, None`
   except Exception as e:
       print(f"Error reading CSV file: {e}")
       return None, None

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description="Scrape and store company data")
   parser.add_argument('--email', required=True, help='Email for Screener.in')
   parser.add_argument('--password', required=True, help='Password for Screener.in')
   parser.add_argument('--db', required=True, help='MySQL database name')
   parser.add_argument('--user', required=True, help='MySQL username')
   parser.add_argument('--pw', required=True, help='MySQL password')
   parser.add_argument('--host', required=True, help='MySQL host')
   parser.add_argument('--port', required=True, help='MySQL port')
   parser.add_argument('--csv_file', required=True, help='Path to CSV file with company data')
   args = parser.parse_args()
   company_symbols, company_names = read_company_names_from_csv(args.csv_file)
   session = login_to_screener(args.email, args.password)
   if session:
       all_company_df = pd.DataFrame(columns=['Company_ID', 'Company'])
       all_df_ttm = pd.DataFrame(columns=['n_id', 'TTM', 'Company_ID'])
       all_df = pd.DataFrame(columns=['n_id', 'Financial_Year', 'Value', 'Company_ID', 'Percent_change', 'TTM_ID'])
       all_narration_df = pd.DataFrame(columns=['Narration'])
       company_id = 1
       for symbol, name in zip(company_symbols, company_names):
           df, company_df, df_ttm, narration_df = scrape_company_data(session, symbol, company_id, name)
           if df is not None and company_df is not None and df_ttm is not None and narration_df is not None:
               all_df = pd.concat([all_df, df], ignore_index=True)
               all_company_df = pd.concat([all_company_df, company_df], ignore_index=True)
               all_df_ttm = pd.concat([all_df_ttm, df_ttm], ignore_index=True)
               all_narration_df = pd.concat([all_narration_df, narration_df], ignore_index=True)
               company_id += 1
               time.sleep(1.5)

       save_to_mysql(all_df, all_company_df, all_df_ttm, args.db, args.user, args.pw, args.host, args.port)
