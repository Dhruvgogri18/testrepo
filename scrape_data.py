from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.chrome.options import Options as ChromeOptions
 
 
 
options=ChromeOptions()
service =Service("C:/Users/Dhruv Gogri/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe")
 
driver = webdriver.Chrome(service=service , options=options)
try:
    driver.get("https://www.screener.in/login/")
    time.sleep(5)
    driver.fullscreen_window()
    email_input = driver.find_element(By.XPATH, '//*[@id="id_username"]')
    email_input.send_keys("dhruvgogri014@gmail.com")
    password_input = driver.find_element(By.XPATH, '//*[@id="id_password"]')
    password_input.send_keys("Dg9892211065@")
    password_input.send_keys(Keys.RETURN)
 
    time.sleep(5)
 
    driver.get("https://www.screener.in/company/RELIANCE/consolidated/")
    time.sleep(5)
    export_csv_button = driver.find_element(By.XPATH , '//*[@id="top"]/div[1]/form/button')
    export_csv_button.click()
    time.sleep(25)
 
finally:
    driver.quit()
