import pandas as pd
import os
def read_profit_and_loss_tab(file_name):
   if file_name:
       # Read the Excel file
       try:
           # Load only the "Profit and Loss" sheet
           profit_and_loss_df = pd.read_excel(file_name, sheet_name="Profit & Loss")
           # Perform any additional processing here if needed
           print("Profit and Loss Data:")
           print(profit_and_loss_df.head())
       except Exception as e:
           print(f"Error reading Excel file or extracting Profit and Loss tab: {e}")
   else:
       print(f"File {file_name} not found")
if __name__ == '__main__':
   file_name = "Reliance Industr.xlsx"
   read_profit_and_loss_tab(download_dir, file_name)
