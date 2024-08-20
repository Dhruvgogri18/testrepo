from selenium import webdriver
from selenium.webdriver.chrome.options import Options
def login_and_download_file(url, username, password, file_suffix):
   chrome_options = Options()
   chrome_options.add_argument("--headless")
   chrome_options.add_argument("--no-sandbox")
   chrome_options.add_argument("--disable-dev-shm-usage")
   chrome_options.add_argument("--disable-gpu")
   chrome_options.add_argument("--window-size=1920x1080")  # optional, but can help in headless mode
   driver = webdriver.Chrome(options=chrome_options)
   driver.get(url)
   # Your remaining code to log in and download
