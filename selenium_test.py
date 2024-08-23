# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# import time
# import os
 
# usernames = ["dhruvgogri014@gmail.com"]
# passwords = ["Dg9892211065@"]
 
# def login_and_download_file(url, username, password, file_suffix):

#     current_dir = os.getcwd()

#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--window-size=1920,1080")
 
#     prefs = {
#         "download.default_directory": current_dir,
#         "download.prompt_for_download": False,
#         "download.directory_upgrade": True,
#         "safebrowsing.enabled": True
#     }
#     chrome_options.add_experimental_option("prefs", prefs)
 
#     driver = webdriver.Chrome(options=chrome_options)
#     driver.implicitly_wait(10)
 
#     try:
#         driver.get(url)
#         driver.save_screenshot('before_login.png')
 
#         WebDriverWait(driver, 20).until(
#             EC.element_to_be_clickable((By.XPATH, '//*[contains(@class, "account")]'))
#         ).click()
 
#         email_input = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.ID, 'id_username'))
#         )
#         password_input = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.ID, 'id_password'))
#         )
 
#         email_input.send_keys(username)
#         password_input.send_keys(password)
#         password_input.send_keys(Keys.RETURN)
 
#         driver.save_screenshot('after_login.png')
 
#         driver.get("https://www.screener.in/company/RELIANCE/consolidated/")
 
#         download_button = WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Export to Excel"]'))
#         )
#         print("Attempting to click the download button...")
#         driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
#         driver.execute_script("arguments[0].click();", download_button)
#         print("Download button clicked.")
 
#         driver.save_screenshot('after_click.png')
 
#         download_dir = current_dir
#         file_name = "profit_and_loss.xlsx"
#         print("Files in download directory before wait:", os.listdir(download_dir))
#         if wait_for_file(download_dir, file_name):
#             print("File downloaded successfully.")
#         else:
#             print("File download failed or timeout.")
 
#     except Exception as e:
#         driver.save_screenshot('error_screenshot.png')
#         print(f"Error: {e}")
#         raise e
#     finally:
#         driver.quit()
 
# def wait_for_file(download_dir, file_name, timeout=120):
#    start_time = time.time()
#    while time.time() - start_time < timeout:
#        for file in os.listdir(download_dir):
#            if file == file_name:
#                return True
#            if file.endswith(".crdownload"):
#                time.sleep(15)  
#                return True
#        time.sleep(15) 
#    return False
 
# if __name__ == '__main__':
#     for i, (username, password) in enumerate(zip(usernames, passwords)):
#         login_and_download_file("https://www.screener.in/", username, password, i)


from sqlalchemy import create_engine, text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

# Setup Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Path to the ChromeDriver you installed
driver = webdriver.Chrome(options=chrome_options)
# URL to scrape
url = 'https://screener.in/company/RELIANCE/consolidated/'
# Open the webpage
driver.get(url)
time.sleep(5)  # Wait for the page to fully load
# Locate the profit-loss table section by ID
profit_loss_section = driver.find_element(By.ID, "profit-loss")
# Locate the table within the section
table = profit_loss_section.find_element(By.TAG_NAME, "table")
# Extract table data
table_data = []
rows = table.find_elements(By.TAG_NAME, "tr")
for row in rows:
   row_data = []
   cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
   for cell in cells:
       row_data.append(cell.text.strip())
   table_data.append(row_data)
# Convert the table data to a DataFrame
df_table = pd.DataFrame(table_data)
# Rename the first cell in the first row
df_table.iloc[0, 0] = 'Section'
# Set the first row as column names
df_table.columns = df_table.iloc[0]
# Remove the first row from DataFrame
df_table = df_table[1:]
# Transpose the DataFrame
df_table = df_table.transpose().reset_index()
df_table.columns = df_table.iloc[0]  # Set new column names
df_table = df_table[1:]  # Remove the old header row
# Reset index and add primary key
df_table.reset_index(drop=True, inplace=True)
df_table.index += 1
df_table.index.name = 'id'
df_table.reset_index(inplace=True)
# Ensure only valid numeric data is processed with eval
def safe_eval(val):
   try:
       return eval(val)
   except:
       return val
# Convert relevant columns to numeric types
for i in df_table.columns[1:]:
   df_table[i] = df_table[i].str.replace(',', '').str.replace('%', '/100').apply(safe_eval)
# MySQL database connection details
db = "connect_test"
user = "root"
pw = "root"
host = "192.168.1.51"
port = "3306"
# Create SQLAlchemy engine
engine = create_engine(f"mysql+mysqlconnector://{user}:{pw}@{host}:{port}/{db}")
# Clear table before inserting new data
# with engine.connect() as conn:
#    conn.execute(text('TRUNCATE TABLE IF EXISTS profit_loss_data1;'))
# Insert data into the MySQL table
df_table.to_sql('profit_loss_data1', engine, if_exists='append', index=False)
print("Data saved to Mysql")
# Close the browser
driver.quit()
