from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
 
usernames = ["dhruvgogri014@gmail.com"]
passwords = ["Dg9892211065@"]
 
def login_and_download_file(url, username, password, file_suffix):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
 
    prefs = {
        "download.default_directory": r"C:\Users\Dhruv Gogri\Desktop",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    service = Service('/usr/local/bin/chromedriver-linux64/chromedriver')
 
 
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
 
    try:
        driver.get(url)
        driver.save_screenshot('before_login.png')
 
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(@class, "account")]'))
        ).click()
 
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'id_username'))
        )
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'id_password'))
        )
 
        email_input.send_keys(username)
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)
 
        driver.save_screenshot('after_login.png')
 
        driver.get("https://www.screener.in/company/RELIANCE/consolidated/")
 
        download_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//button[@aria-label="Export to Excel"]'))
        )
        print("Attempting to click the download button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
        driver.execute_script("arguments[0].click();", download_button)
        print("Download button clicked.")
 
        driver.save_screenshot('after_click.png')
 
        download_dir = r"C:\Users\Dhruv Gogri\Desktop"
        file_name = "profit_and_loss.xlsx"
        print("Files in download directory before wait:", os.listdir(download_dir))
        if wait_for_file(download_dir, file_name):
            print("File downloaded successfully.")
        else:
            print("File download failed or timeout.")
 
    except Exception as e:
        driver.save_screenshot('error_screenshot.png')
        print(f"Error: {e}")
        raise e
    finally:
        driver.quit()
 
def wait_for_file(download_dir, file_name, timeout=120):
   start_time = time.time()
   while time.time() - start_time < timeout:
       for file in os.listdir(download_dir):
           if file == file_name:
               return True
           if file.endswith(".crdownload"):
               time.sleep(30)  
       time.sleep(30) 
   return False
 
if __name__ == '__main__':
    for i, (username, password) in enumerate(zip(usernames, passwords)):
        login_and_download_file("https://www.screener.in/", username, password, i)
